from typing import Any, Callable, TypeAlias

from mlx import Mlx
from pydantic import BaseModel, Field, PrivateAttr

from .maze import CellFlag, Maze


class Palette(BaseModel):
    cursor: int
    path: int
    seek: int
    seek_premium: int
    border: int
    unreachable: int
    default: int
    entry: int
    exit: int

    _is_dirty = PrivateAttr(default=True)

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

        if not name.startswith("_"):
            self._is_dirty = True

    def flush(self) -> bool:
        is_dirty: bool = self._is_dirty
        self._is_dirty = False
        return is_dirty


class EngineConfig(BaseModel):
    cell_size: int = Field(frozen=True)
    border_size: int = Field(frozen=True)


class Rgba(BaseModel):
    r: int
    g: int
    b: int
    a: int

    def to_bytes(self) -> bytes:
        return bytes([self.b, self.g, self.r, self.a])

    @staticmethod
    def from_int(color: int) -> "Rgba":
        rgba = Rgba(
            a=color & 0xFF,
            r=(color >> 24) & 0xFF,
            g=(color >> 16) & 0xFF,
            b=(color >> 8) & 0xFF,
        )
        return rgba

    @staticmethod
    def bytes_from_int(color: int) -> bytes:
        rgba = Rgba.from_int(color)
        return rgba.to_bytes()


SwitcherCallback: TypeAlias = Callable[[str], None]
ExitCallback: TypeAlias = Callable[[], None]
ResetCallback: TypeAlias = Callable[[], None]
ClearCallback: TypeAlias = Callable[[], None]

UpdateCallbackParams: TypeAlias = tuple[
    dict[str, Any],
    Maze,
    Palette,
    SwitcherCallback,
    ExitCallback,
    ResetCallback,
    ClearCallback,
]
UpdateCallback: TypeAlias = Callable[[UpdateCallbackParams], None]

LoopConfig: TypeAlias = tuple[UpdateCallback, dict[str, Any]]
LoopConfigCallback: TypeAlias = Callable[[Maze], LoopConfig]


class GraphicalEngine:

    def __init__(
        self,
        maze: Maze,
        config: EngineConfig,
        palette: Palette,
        loops: dict[str, LoopConfigCallback],
    ) -> None:
        self._maze: Maze = maze
        self._width: int = maze.width * config.cell_size
        self._height: int = maze.height * config.cell_size
        self._config: EngineConfig = config
        self._palette: Palette = palette
        self._mlx: Mlx = Mlx()
        self._mlx_ptr: Any = self._mlx.mlx_init()
        self._window = self._mlx.mlx_new_window(
            self._mlx_ptr, self._width, self._height, "A-Maze-ing"
        )
        self._image = self._mlx.mlx_new_image(
            self._mlx_ptr, self._width, self._height
        )

        data: tuple[Any, ...] = self._mlx.mlx_get_data_addr(self._image)
        self._image_bytes: Any = data[0]
        self._bpp: int = data[1] // 8
        self._ppr: int = data[2]
        self._loop_registry: dict[str, LoopConfigCallback] = loops
        self._lines: dict[str, dict[tuple[int, int], bytes]] = {}
        self._precompute_lines()

    def _precompute_lines(self) -> None:
        border_size: int = self._config.border_size
        cell_size: int = self._config.cell_size

        border_px: bytes = Rgba.bytes_from_int(self._palette.border)

        for key in vars(self._palette):
            pixel: bytes = Rgba.bytes_from_int(getattr(self._palette, key))

            self._lines[key] = {
                (0, 0):
                    pixel * cell_size,
                (CellFlag.WEST, 0): (border_px * border_size) + pixel *
                                    (cell_size - border_size),
                (0, CellFlag.EAST):
                    pixel * (cell_size - border_size) +
                    (border_px * border_size),
                (CellFlag.WEST, CellFlag.EAST):
                    (border_px * border_size) + pixel *
                    (cell_size - border_size * 2) + (border_px * border_size),
            }

    @staticmethod
    def _update(args: tuple["GraphicalEngine", LoopConfig]) -> None:
        self, (callback, context) = args
        callback((
            context,
            self._maze,
            self._palette,
            self._get_switcher(),
            self._exit,
            self._reset,
            self._clear,
        ))

        if self._palette.flush():
            self._precompute_lines()
            self._render()
        elif self._maze.flush():
            self._render()

    def loop(self, loop_key: str) -> None:
        if loop_key not in self._loop_registry:
            raise KeyError(f"loop {loop_key} does not exists")

        self._mlx.mlx_loop_hook(
            self._mlx_ptr,
            self._update,
            (self, self._loop_registry[loop_key](self._maze)),
        )
        self._mlx.mlx_loop(self._mlx_ptr)

    def _get_switcher(self) -> SwitcherCallback:

        def switcher(loop_key: str) -> None:
            if loop_key not in self._loop_registry:
                raise KeyError(f"loop {loop_key} does not exists")
            self._mlx.mlx_loop_hook(
                self._mlx_ptr,
                self._update,
                (self, self._loop_registry[loop_key](self._maze)),
            )

        return switcher

    def _exit(self) -> None:
        self._mlx.mlx_loop_exit(self._mlx_ptr)

    def _reset(self) -> None:
        self._maze.clear()
        self._render()

    def _clear(self) -> None:
        for cy in range(self._maze.height):
            for cx in range(self._maze.width):
                self._maze.unset(cx, cy, ~0x7F)

    def _render(self) -> None:
        self._mlx.mlx_clear_window(self._mlx_ptr, self._window)

        border_size: int = self._config.border_size
        cell_size: int = self._config.cell_size

        for cy in range(self._maze.height):
            for cx in range(self._maze.width):
                flags: int = self._maze.get_cell(cx, cy)

                n_border: int = border_size if flags & CellFlag.NORTH else 0
                s_border: int = border_size if flags & CellFlag.SOUTH else 0

                x0 = cx * cell_size
                y0 = cy * cell_size
                e: int = flags & CellFlag.EAST
                w: int = flags & CellFlag.WEST
                for dy in range(cell_size):
                    offset = (y0 + dy) * self._ppr + (x0 * self._bpp)
                    if dy < n_border or dy >= cell_size - s_border:
                        self._image_bytes[offset:offset + self._bpp *
                                          cell_size] = self._lines["border"][
                                              (w, e)]
                    elif flags & CellFlag.UNREACHABLE:
                        self._image_bytes[offset:offset + self._bpp * cell_size
                                         ] = self._lines["unreachable"][(w, e)]
                    elif flags & CellFlag.ENTRY:
                        self._image_bytes[offset:offset + self._bpp *
                                          cell_size] = self._lines["entry"][
                                              (w, e)]
                    elif flags & CellFlag.EXIT:
                        self._image_bytes[offset:offset + self._bpp *
                                          cell_size] = self._lines["exit"][
                                              (w, e)]
                    elif (dy >= n_border and dy < cell_size - s_border and
                          flags & CellFlag.CURSOR):
                        self._image_bytes[offset:offset + self._bpp *
                                          cell_size] = self._lines["cursor"][
                                              (w, e)]
                    elif flags & CellFlag.PATH and not self._maze.hide_path:
                        self._image_bytes[offset:offset + self._bpp *
                                          cell_size] = self._lines["path"][
                                              (w, e)]
                    elif flags & CellFlag.SEEK and not self._maze.hide_path:
                        self._image_bytes[offset:offset + self._bpp *
                                          cell_size] = self._lines["seek"][
                                              (w, e)]
                    elif (flags & CellFlag.SEEK_PREMIUM and
                          not self._maze.hide_path):
                        self._image_bytes[offset:offset +
                                          self._bpp * cell_size] = self._lines[
                                              "seek_premium"][(w, e)]
                    else:
                        self._image_bytes[offset:offset + self._bpp *
                                          cell_size] = self._lines["default"][
                                              (w, e)]

        self._mlx.mlx_put_image_to_window(
            self._mlx_ptr, self._window, self._image, 0, 0
        )
