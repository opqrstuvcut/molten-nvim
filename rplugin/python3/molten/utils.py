import time
import traceback
from functools import wraps

from pynvim import Nvim


class MoltenException(Exception):
    pass


_LAST_ERROR: tuple[str, float] | None = None


def nvimui(func):  # type: ignore
    @wraps(func)
    def inner(self, *args, **kwargs):  # type: ignore
        try:
            func(self, *args, **kwargs)
        except MoltenException as err:
            notify_error(self.nvim, str(err))
        except Exception as err:
            global _LAST_ERROR
            message = f"{func.__name__}: {err}"
            now = time.monotonic()
            if _LAST_ERROR is None or _LAST_ERROR[0] != message or now - _LAST_ERROR[1] > 1.5:
                _LAST_ERROR = (message, now)
                notify_error(
                    self.nvim,
                    message + ". Check `:messages` for the Python traceback.",
                )
                self.nvim.err_write(
                    "[Molten] Unhandled exception in "
                    + func.__name__
                    + "\n"
                    + "".join(traceback.format_exc())
                    + "\n"
                )

    return inner


def _notify(nvim: Nvim, msg: str, log_level: str) -> None:
    lua = f"""
        vim.schedule_wrap(function()
            vim.notify([[[Molten] {msg}]], vim.log.levels.{log_level}, {{}})
        end)()
    """
    nvim.exec_lua(lua)


def notify_info(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display an info message."""
    _notify(nvim, msg, "INFO")


def notify_warn(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display a warning message."""
    _notify(nvim, msg, "WARN")


def notify_error(nvim: Nvim, msg: str) -> None:
    """Use the vim.notify API to display an error message."""
    _notify(nvim, msg, "ERROR")
