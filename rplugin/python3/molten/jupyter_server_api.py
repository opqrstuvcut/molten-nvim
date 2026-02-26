import json
import struct
import time
import uuid
from datetime import datetime, timezone
from queue import Empty as EmptyQueueException
from queue import Queue
from threading import Thread
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from molten.runtime_state import RuntimeState


class JupyterAPIClient:
    _V1_WS_PROTOCOL = "v1.kernel.websocket.jupyter.org"

    def __init__(self,
                 url: str,
                 kernel_info: Dict[str, Any],
                 headers: Dict[str, str]):
        self._base_url = url
        self._kernel_info = kernel_info
        self._headers = headers

        self._recv_queue: Queue[Dict[str, Any]] = Queue()
        self._stdin_recv_queue: Queue[Dict[str, Any]] = Queue()
        self._kernel_api_base = f"{self._base_url}/api/kernels/{self._kernel_info['id']}"
        self._ws_protocol = ""
        self._session_id = uuid.uuid4().hex

        import requests
        self.requests = requests

    def get_stdin_msg(self, **kwargs):
        if self._stdin_recv_queue.empty():
            raise EmptyQueueException
        return self._stdin_recv_queue.get()

    def wait_for_ready(self, timeout: float = 0.):
        start = time.time()
        while True:
            response = self.requests.get(self._kernel_api_base,
                                    headers=self._headers)
            response = json.loads(response.text)

            if response["execution_state"] != "idle" and time.time() - start > timeout:
                raise RuntimeError

            # Discard unnecessary messages.
            while True:
                try:
                    response = self.get_iopub_msg()
                except EmptyQueueException:
                    return


    def start_channels(self) -> None:
        import websocket

        parsed_url = urlparse(self._base_url)
        base_path = parsed_url.path.rstrip("/")
        ws_scheme = "wss" if parsed_url.scheme == "https" else "ws"
        ws_api_path = f"{base_path}/api/kernels/{self._kernel_info['id']}/channels"
        ws_url = (
            f"{ws_scheme}://{parsed_url.netloc}"
            f"{ws_api_path}"
        )
        ws_headers = [f"{key}: {value}" for key, value in self._headers.items()]

        self._socket = websocket.create_connection(
            ws_url,
            header=ws_headers,
            subprotocols=[self._V1_WS_PROTOCOL],
        )
        self._ws_protocol = self._socket.getsubprotocol() or ""

        self._iopub_recv_thread = Thread(target=self._recv_message)
        self._iopub_recv_thread.daemon = True
        self._iopub_recv_thread.start()

    def _recv_message(self) -> None:
        while True:
            response = _deserialize_message(self._socket.recv())
            if response is None:
                continue

            msg = _to_runtime_message(response)
            if msg is None:
                continue

            channel = response.get("channel", "")
            if channel == "stdin":
                self._stdin_recv_queue.put(msg)
            else:
                self._recv_queue.put(msg)

    def get_iopub_msg(self, **kwargs):
        if self._recv_queue.empty():
            raise EmptyQueueException

        response = self._recv_queue.get()

        return response

    def execute(self, code: str):
        header = self._build_header("execute_request")

        message = {
            'channel': 'shell',
            'header': header,
            'parent_header': {},
            'metadata': {},
            'content': {
                'code': code,
                'silent': False,
                'store_history': True,
                'user_expressions': {},
                'allow_stdin': True,
                'stop_on_error': True,
            },
            'buffers': [],
        }

        if self._ws_protocol == self._V1_WS_PROTOCOL:
            self._socket.send_binary(_serialize_v1_message(message))
            return

        self._socket.send(json.dumps(message))

    def _build_header(self, msg_type: str) -> Dict[str, str]:
        return {
            "msg_id": uuid.uuid4().hex,
            "session": self._session_id,
            "username": "molten",
            "date": datetime.now(timezone.utc).isoformat(),
            "msg_type": msg_type,
            "version": "5.3",
        }

    def shutdown(self):
        self.requests.delete(self._kernel_api_base,
                        headers=self._headers)

    def cleanup_connection_file(self):
        pass

class JupyterAPIManager:
    def __init__(self,
                 url: str,
                 ):
        parsed_url = urlparse(url)
        self._base_url = self._normalize_base_url(parsed_url)

        token = parse_qs(parsed_url.query).get("token")
        if token:
            self._headers = {'Authorization': f'token {token[0]}'}
        else:
            # Run notebook with --NotebookApp.disable_check_xsrf="True".
            self._headers = {}

        import requests
        self.requests = requests

    def start_kernel(self) -> None:
        url = f"{self._base_url}/api/kernels"
        response = self.requests.post(url,
                                 headers=self._headers)
        self._kernel_info = json.loads(response.text)
        assert "id" in self._kernel_info, "Could not connect to Jupyter Server API. The URL specified may be incorrect."
        self._kernel_api_base = f"{url}/{self._kernel_info['id']}"

    def client(self) -> JupyterAPIClient:
        return JupyterAPIClient(url=self._base_url,
                                kernel_info=self._kernel_info,
                                headers=self._headers)

    def interrupt_kernel(self) -> None:
        self.requests.post(f"{self._kernel_api_base}/interrupt",
                      headers=self._headers)

    def restart_kernel(self) -> None:
        self.state = RuntimeState.STARTING
        self.requests.post(f"{self._kernel_api_base}/restart",
                      headers=self._headers)

    @staticmethod
    def _normalize_base_url(parsed_url) -> str:
        path_segments = [segment for segment in parsed_url.path.split("/") if segment]
        for idx, segment in enumerate(path_segments):
            if segment in {"lab", "tree", "notebooks"}:
                path_segments = path_segments[:idx]
                break
        path = f"/{'/'.join(path_segments)}" if path_segments else ""
        return f"{parsed_url.scheme}://{parsed_url.netloc}{path}"


def _decode_utf8_json(raw: bytes) -> Any:
    return json.loads(raw.decode("utf-8"))


def _deserialize_v1_message(raw: bytes) -> Dict[str, Any]:
    (offset_count,) = struct.unpack_from("<Q", raw, 0)
    offsets = struct.unpack_from(f"<{offset_count}Q", raw, 8)

    parts = []
    for idx in range(offset_count - 1):
        parts.append(raw[offsets[idx]:offsets[idx + 1]])

    if len(parts) < 5:
        raise ValueError("Invalid v1 websocket message")

    message: Dict[str, Any] = {
        "channel": parts[0].decode("utf-8"),
        "header": _decode_utf8_json(parts[1]),
        "parent_header": _decode_utf8_json(parts[2]),
        "metadata": _decode_utf8_json(parts[3]),
        "content": _decode_utf8_json(parts[4]),
    }
    if len(parts) > 5:
        message["buffers"] = parts[5:]
    return message


def _serialize_v1_message(message: Dict[str, Any]) -> bytes:
    parts = [
        message.get("channel", "shell").encode("utf-8"),
        json.dumps(message.get("header", {})).encode("utf-8"),
        json.dumps(message.get("parent_header", {})).encode("utf-8"),
        json.dumps(message.get("metadata", {})).encode("utf-8"),
        json.dumps(message.get("content", {})).encode("utf-8"),
    ]
    for buffer in message.get("buffers", []):
        parts.append(buffer if isinstance(buffer, (bytes, bytearray)) else bytes(buffer))

    offsets = []
    offset = 8 * (len(parts) + 2)
    for part in parts:
        offsets.append(offset)
        offset += len(part)
    offsets.append(offset)

    header = struct.pack("<Q", len(offsets)) + struct.pack(f"<{len(offsets)}Q", *offsets)
    return header + b"".join(parts)


def _to_runtime_message(message: Dict[str, Any]) -> Dict[str, Any] | None:
    if "msg_type" in message and "content" in message:
        return {"msg_type": message["msg_type"], "content": message["content"]}
    header = message.get("header")
    content = message.get("content")
    if isinstance(header, dict) and isinstance(content, dict):
        msg_type = header.get("msg_type")
        if isinstance(msg_type, str):
            return {"msg_type": msg_type, "content": content}
    return None


def _deserialize_message(raw: Any) -> Dict[str, Any] | None:
    if isinstance(raw, str):
        return json.loads(raw)
    if isinstance(raw, (bytes, bytearray)):
        try:
            return _deserialize_v1_message(raw)
        except Exception:
            return None
    return None
