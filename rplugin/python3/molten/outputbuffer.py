from datetime import datetime
from typing import Any, List, Optional, Tuple, Union, Callable

from pynvim import Nvim
from pynvim.api import Buffer, Window

from molten.code_cell import CodeCell
from molten.images import Canvas
from molten.outputchunks import ImageOutputChunk, Output, OutputStatus
from molten.options import MoltenOptions
from molten.position import DynamicPosition, Position
from molten.utils import notify_error


def truncate_bottom(lines: list[str], text_max_lines: int) -> list[str]:
    truncated_lines = lines[: text_max_lines - 1]
    truncated_lines.append(f"󰁅 {len(lines) - text_max_lines + 1} More lines ")
    return truncated_lines


def truncate_top(lines: list[str], text_max_lines: int):
    truncated_lines = [lines[0]]
    truncated_lines.append(f"↑ {len(lines) - text_max_lines} More lines")
    truncated_lines.extend(lines[-text_max_lines + 2 :])
    return truncated_lines


class OutputBuffer:
    nvim: Nvim
    canvas: Canvas

    output: Output

    display_buf: Buffer
    display_win: Optional[Window]
    display_virt_lines: Optional[DynamicPosition]
    extmark_namespace: int
    virt_text_id: Optional[int]
    displayed_status: OutputStatus

    options: MoltenOptions
    lua: Any

    def __init__(self, nvim: Nvim, canvas: Canvas, extmark_namespace: int, options: MoltenOptions):
        self.nvim = nvim
        self.canvas = canvas

        self.output = Output(None)

        self.display_buf = self.nvim.buffers[self.nvim.funcs.nvim_create_buf(False, True)]
        self.display_win: Window | None = None
        self.display_virt_lines = None
        self.virt_hidden: bool = False
        self.extmark_namespace = extmark_namespace
        self.virt_text_id = None
        self.displayed_status = OutputStatus.HOLD

        self.options = options
        self.nvim.exec_lua("_ow = require('output_window')")
        self.lua = self.nvim.lua._ow

        self.truncate_lines: Callable[[list[str], int], list[str]]
        if self.options.virt_text_truncate == "bottom":
            self.truncate_lines = truncate_bottom
        elif self.options.virt_text_truncate == "top":
            self.truncate_lines = truncate_top
        else:
            raise ValueError("Wrong virtual text truncate option")

    def _buffer_to_window_lineno(self, lineno: int) -> int:
        return self.lua.calculate_window_position(lineno)

    def _get_header_text(self, output: Output) -> str:
        if output.execution_count is None:
            execution_count = "..."
        else:
            execution_count = str(output.execution_count)

        match output.status:
            case OutputStatus.HOLD:
                status = "* On Hold"
            case OutputStatus.DONE:
                if output.success:
                    status = "✓ Done"
                else:
                    status = "✗ Failed"
            case OutputStatus.RUNNING:
                status = "... Running"
            case OutputStatus.NEW:
                status = ""
            case _:
                raise ValueError("bad output.status: %s" % output.status)

        if output.old:
            old = "[OLD] "
        else:
            old = ""

        if not output.old and self.options.output_show_exec_time and output.start_time:
            start = output.start_time
            end = output.end_time if output.end_time is not None else datetime.now()
            diff = end - start

            days = diff.days
            hours = diff.seconds // 3600
            minutes = diff.seconds // 60
            seconds = diff.seconds - hours * 3600 - minutes * 60
            microseconds = diff.microseconds

            time = ""

            # Days
            if days:
                time += f"{days}d "
            if hours:
                time += f"{hours}hr "
            if minutes:
                time += f"{minutes}m "

            # Microseconds is an int, roundabout way to round to 2 digits
            time += f"{seconds}.{int(round(microseconds, -4) / 10000)}s"
        else:
            time = ""

        if output.status == OutputStatus.NEW:
            return f"Out[_]: Never Run"
        else:
            return f"{old}Out[{execution_count}]: {status} {time}".rstrip()

    def enter(self, anchor: Position, span: CodeCell | None = None) -> bool:
        entered = False
        if self.display_win is None:
            if self.options.enter_output_behavior == "open_then_enter":
                self.show_floating_win(anchor, span)
            elif self.options.enter_output_behavior == "open_and_enter":
                self.show_floating_win(anchor, span)
                entered = True
                self.nvim.funcs.nvim_set_current_win(self.display_win)
        elif self.options.enter_output_behavior != "no_open":
            entered = True
            self.nvim.funcs.nvim_set_current_win(self.display_win)
        if entered:
            if self.options.output_show_more:
                self.remove_window_footer()
            if self.options.output_win_hide_on_leave:
                return False
        return True

    def clear_float_win(self) -> None:
        if self.display_win is not None:
            if self.display_win.valid:
                self.nvim.funcs.nvim_win_close(self.display_win, True)
            self.display_win = None
        self.clear_images()
        if self.display_virt_lines is not None:
            del self.display_virt_lines
            self.display_virt_lines = None

    def clear_images(self) -> None:
        redraw = False
        for chunk in self.output.chunks:
            if isinstance(chunk, ImageOutputChunk) and chunk.img_identifier is not None:
                self.canvas.remove_image(chunk.img_identifier)
                chunk.img_identifier = None
                redraw = True
        if redraw:
            self.canvas.present()

    def clear_virt_output(self, bufnr: int) -> None:
        if self.virt_text_id is not None:
            # remove the extmark…
            self.nvim.funcs.nvim_buf_del_extmark(bufnr, self.extmark_namespace, self.virt_text_id)
            # …and clear our flag so show_virtual_output can re-add it
            self.virt_text_id = None
            # (optional) reset displayed_status so your guard won’t block:
            # self.displayed_status = OutputStatus.NEW
            self.virt_hidden = True

        # clear any inline images, etc.
        self.clear_images()

    def toggle_virtual_output(self, anchor: Position) -> None:
        if self.virt_hidden:
            # currently suppressed ⇒ un‐suppress and show
            self.virt_hidden = False
            self.show_virtual_output(anchor)
        else:
            # currently visible (or default) ⇒ hide and suppress
            self.clear_virt_output(anchor.bufno)
            # clear_virtual_output already set virt_hidden=True

    def set_win_option(self, option: str, value) -> None:
        if self.display_win:
            self.nvim.api.set_option_value(
                option,
                value,
                {"scope": "local", "win": self.display_win.handle},
            )

    def build_output_text(
        self,
        shape,
        buf: int,
        virtual: bool,
        render_images: bool = True,
    ) -> Tuple[List[str], int]:
        lineno = 1  # we add a status line at the top in the end
        lines_str = ""
        # images are rendered with virtual lines by image.nvim
        virtual_lines = 0
        if len(self.output.chunks) > 0:
            x = 0
            for chunk in self.output.chunks:
                if isinstance(chunk, ImageOutputChunk) and not render_images:
                    continue
                y = lineno
                if virtual:
                    y = shape[1]
                chunktext, virt_lines = chunk.place(
                    buf,
                    self.options,
                    x,
                    y,
                    shape,
                    self.canvas,
                    virtual,
                    winnr=self.nvim.current.window.handle if virtual else None,
                )
                lines_str += chunktext
                lineno += chunktext.count("\n")
                virtual_lines += virt_lines
                x = len(lines_str) - lines_str.rfind("\n")

            limit = self.options.limit_output_chars
            if limit and len(lines_str) > limit:
                lines_str = lines_str[:limit]
                lines_str += f"\n...truncated to {limit} chars\n"

            lines = lines_str.split("\n")
            lineno = len(lines) + virtual_lines
        else:
            lines = []

        # Remove trailing empty lines
        while len(lines) > 0 and lines[-1] == "":
            lines.pop()

        lines.insert(0, self._get_header_text(self.output))
        return lines, len(lines) - 1 + virtual_lines

    def _cell_bottom_border(self, span: CodeCell | None) -> str | None:
        if span is None:
            return None

        win_width = self.nvim.current.window.width
        standard_frame_width = max(40, min(int(win_width * 0.8), 120))
        lines = self.nvim.funcs.nvim_buf_get_lines(
            span.bufno,
            span.begin.lineno,
            span.end.lineno + 1,
            False,
        )
        max_line_width = max((self.nvim.funcs.strdisplaywidth(line) for line in lines), default=0)
        frame_width = max(standard_frame_width, max_line_width + 3)
        return "╰" + ("─" * (frame_width - 2)) + "╯"

    def show_virtual_output(
        self,
        anchor: Position,
        span: CodeCell | None = None,
        render_images: bool = True,
    ) -> None:
        if self.virt_hidden:
            return
        if (
            self.displayed_status == OutputStatus.DONE
            and self.virt_text_id is not None
            and not render_images
        ):
            return
        offset = self.calculate_offset(anchor) if self.options.cover_empty_lines else 0
        self.displayed_status = self.output.status

        buf = self.nvim.buffers[anchor.bufno]

        # clear the existing virtual text
        if self.virt_text_id is not None:
            self.nvim.funcs.nvim_buf_del_extmark(
                anchor.bufno, self.extmark_namespace, self.virt_text_id
            )
            self.virt_text_id = None

        win = self.nvim.current.window
        win_info = self.nvim.funcs.getwininfo(win.handle)[0]
        win_col = win_info["wincol"]
        win_row = anchor.lineno + offset
        win_width = win_info["width"] - win_info["textoff"]
        win_height = win_info["height"]
        last = self.nvim.funcs.line("$")

        if self.options.virt_lines_off_by_1 and win_row < last - 1:
            win_row += 1

        if win_row > last:
            win_row = last

        shape = (
            win_col,
            win_row,
            win_width,
            win_height,
        )
        if render_images and self.options.image_provider == "snacks-gallery.nvim":
            gallery_anchor_col = self._gallery_anchor_col(span, win)
            if gallery_anchor_col is not None:
                buf.vars["molten_gallery_anchor_col"] = gallery_anchor_col
            gallery_anchor_row = self._gallery_anchor_row(span, win)
            if gallery_anchor_row is not None:
                buf.vars["molten_gallery_anchor_row"] = gallery_anchor_row

        lines, _ = self.build_output_text(shape, anchor.bufno, True, render_images=render_images)

        if len(lines) > self.options.virt_text_max_lines:
            lines = self.truncate_lines(lines, self.options.virt_text_max_lines)

        virt_lines = [[(line, self.options.hl.virtual_text)] for line in lines]
        bottom_border = self._cell_bottom_border(span)
        if bottom_border is not None:
            virt_lines = [[(bottom_border, "MoltenCellBorder")]] + virt_lines

        self.virt_text_id = buf.api.set_extmark(
            self.extmark_namespace,
            win_row,
            0,
            {
                "virt_lines": virt_lines,
            },
        )
        self.canvas.present()

    def calculate_offset(self, anchor: Position) -> int:
        offset = 0
        lineno = anchor.lineno
        while lineno > 0:
            current_line = self.nvim.funcs.nvim_buf_get_lines(
                anchor.bufno,
                lineno,
                lineno + 1,
                False,
            )[0]
            is_comment = False
            for x in self.options.cover_lines_starting_with:
                if current_line.startswith(x):
                    is_comment = True
                    break
            if current_line != "" and not is_comment:
                return offset
            else:
                lineno -= 1
                offset -= 1
        # Only get here if current_pos.lineno == 0
        return 0

    def _cell_right_screen_col(self, span: CodeCell, win: Window) -> int:
        win_info = self.nvim.funcs.getwininfo(win.handle)[0]
        text_left = win_info["wincol"] - 1 + win_info["textoff"]

        lines = self.nvim.funcs.nvim_buf_get_lines(
            span.bufno, span.begin.lineno, span.end.lineno + 1, False
        )
        if len(lines) == 0:
            return text_left

        display_lines: list[str] = []
        if len(lines) == 1:
            display_lines.append(lines[0][span.begin.colno : span.end.colno])
        else:
            display_lines.append(lines[0][span.begin.colno :])
            display_lines.extend(lines[1:-1])
            display_lines.append(lines[-1][: span.end.colno])

        max_width = max((self.nvim.funcs.strdisplaywidth(line) for line in display_lines), default=0)
        return text_left + max_width

    def _gallery_anchor_col(self, span: CodeCell | None, win: Window) -> int | None:
        current_buf = self.nvim.current.buffer
        try:
            anchor_col = current_buf.vars.get("molten_snacks_gallery_right_anchor_col")
            if isinstance(anchor_col, int):
                return anchor_col
        except Exception:
            pass

        anchor_col = self.nvim.vars.get("molten_snacks_gallery_right_anchor_col")
        if isinstance(anchor_col, int):
            return anchor_col

        if span is None:
            return None
        return self._cell_right_screen_col(span, win)

    def _gallery_anchor_row(self, span: CodeCell | None, win: Window) -> int | None:
        if span is None:
            return None

        cell_top_win_row = self._buffer_to_window_lineno(span.begin.lineno + 1)
        win_info = self.nvim.funcs.getwininfo(win.handle)[0]
        return max(win_info["winrow"] + cell_top_win_row - 2, 0)

    def show_floating_win(self, anchor: Position, span: CodeCell | None = None) -> None:
        win = self.nvim.current.window
        win_col = 0
        offset = 0
        if self.options.cover_empty_lines:
            offset = self.calculate_offset(anchor)
            win_row = self._buffer_to_window_lineno(anchor.lineno + offset) + 1
        else:
            win_row = self._buffer_to_window_lineno(anchor.lineno + 1)

        if win_row <= 0:  # anchor position is off screen
            return
        win_width = win.width
        win_height = win.height

        border_w, border_h = border_size(self.options.output_win_border)

        win_height -= border_h
        win_width -= border_w

        # Clear buffer:
        self.display_buf.api.set_lines(0, -1, False, [])

        sign_col_width = 0
        text_off = self.nvim.funcs.getwininfo(win.handle)[0]["textoff"]
        if not self.options.output_win_cover_gutter:
            sign_col_width = text_off

        shape = (
            win_col + sign_col_width,
            win_row,
            win_width - sign_col_width,
            win_height,
        )
        gallery_anchor_col = self._gallery_anchor_col(span, win)
        if gallery_anchor_col is not None:
            self.display_buf.vars["molten_gallery_anchor_col"] = gallery_anchor_col
        gallery_anchor_row = self._gallery_anchor_row(span, win)
        if gallery_anchor_row is not None:
            self.display_buf.vars["molten_gallery_anchor_row"] = gallery_anchor_row

        lines, real_height = self.build_output_text(shape, self.display_buf.number, False)

        # You can't append lines normally, there will be a blank line at the top
        self.display_buf[0] = lines[0]
        self.display_buf.append(lines[1:])
        self.nvim.api.set_option_value(
            "filetype", "molten_output", {"buf": self.display_buf.handle}
        )

        # Open output window
        # assert self.display_window is None
        if not win_row < win_height:
            return

        border = self.options.output_win_border
        zindex = self.options.output_win_zindex
        max_height = min(real_height + 1, self.options.output_win_max_height)
        height = min(win_height - win_row, max_height)

        cropped = False
        if height == win_height - win_row and max_height > height:  # It didn't fit on the screen
            if self.options.output_crop_border and type(border) is list:
                cropped = True
                # Expand the border, so top and bottom can change independently
                border = [border[i % len(border)] for i in range(8)]
                border[5 % len(border)] = ""
                height += 1

        if self.options.use_border_highlights:
            border = self.set_border_highlight(border)

        win_opts = {
            "relative": "win",
            "row": shape[1],
            "col": shape[0],
            "width": min(shape[2], self.options.output_win_max_width),
            "height": height,
            "border": border,
            "focusable": True,
            "zindex": zindex,
        }
        if self.options.output_win_style:
            win_opts["style"] = self.options.output_win_style
        if (
            self.options.output_show_more
            and not cropped
            and height == self.options.output_win_max_height
        ):
            # the entire window size is shown, but the buffer still has more lines to render
            hidden_lines = len(self.display_buf) - height
            if self.options.output_win_cover_gutter and type(border) == list:
                border_pad = border[5 % len(border)][0] * text_off
                win_opts["footer"] = [
                    (border_pad, border[5 % len(border)][1]),
                    (f" 󰁅 {hidden_lines} More Lines ", self.options.hl.foot),
                ]
            else:
                win_opts["footer"] = [(f" 󰁅 {hidden_lines} More Lines ", self.options.hl.foot)]
            win_opts["footer_pos"] = "left"

        if self.display_win is None or not self.display_win.valid:  # open a new window
            window: Window = self.nvim.api.open_win(
                self.display_buf.number,
                False,
                win_opts,
            )
            self.display_win = window

            hl = self.options.hl
            self.set_win_option("winhighlight", f"Normal:{hl.win},NormalNC:{hl.win_nc}")
            # TODO: Refactor once MoltenOutputWindowOpen autocommand is a thing.
            # note, the above setting will probably stay there, just so users can set highlights
            # with their other highlights
            self.set_win_option("wrap", self.options.wrap_output)
            self.set_win_option("cursorline", False)
            self.canvas.present()
        else:  # move the current window
            self.display_win.api.set_config(win_opts)

        if self.display_virt_lines is not None:
            del self.display_virt_lines
            self.display_virt_lines = None

        if self.options.output_virt_lines or self.options.cover_empty_lines:
            virt_lines_y = anchor.lineno
            if self.options.cover_empty_lines:
                virt_lines_y += offset
            virt_lines_height = max_height + border_h
            if self.options.virt_lines_off_by_1:
                virt_lines_y += 1
                virt_lines_height -= 1
            self.display_virt_lines = DynamicPosition(
                self.nvim, self.extmark_namespace, anchor.bufno, virt_lines_y, 0
            )
            self.display_virt_lines.set_height(virt_lines_height)

        if self.options.floating_window_focus == "top":
            self.display_win.api.set_cursor((1, 0))

        elif self.options.floating_window_focus == "bottom":
            self.display_win.api.set_cursor((len(self.display_buf), 0))

    def set_border_highlight(self, border):
        hl = self.options.hl.border_norm
        if not self.output.success:
            hl = self.options.hl.border_fail
        elif self.output.status == OutputStatus.DONE:
            hl = self.options.hl.border_succ

        if type(border) == str:
            notify_error(
                self.nvim,
                "`use_border_highlights` only works when `output_win_border` is specified as a table",
            )
            return border

        for i in range(len(border)):
            match border[i]:
                case [str(_), *_]:
                    border[i][1] = hl
                case str(_):
                    border[i] = [border[i], hl]

        return border

    def remove_window_footer(self) -> None:
        if self.display_win is not None:
            self.display_win.api.set_config({"footer": ""})


def border_size(border: Union[str, List[str], List[List[str]]]):
    width, height = 0, 0
    match border:
        case list(b):
            height += border_char_size(1, b)
            height += border_char_size(5, b)
            width += border_char_size(7, b)
            width += border_char_size(3, b)
        case "rounded" | "single" | "double" | "solid":
            height += 2
            width += 2
        case "shadow":
            height += 1
            width += 1
    return width, height


def border_char_size(index: int, border: Union[List[str], List[List[str]]]):
    match border[index % len(border)]:
        case str(ch) | [str(ch), _]:
            return len(ch)
        case _:
            return 0
