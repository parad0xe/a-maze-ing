from dataclasses import dataclass
from typing import Any, Callable, Protocol, TypeAlias

from mlx import Mlx

from .maze import CellFlag, Maze


@dataclass
class Palette:
    cursor: int
    path: int
    border: int
    unreachable: int
    default: int


@dataclass
class EngineConfig:
    border_size: int
    cell_size: int
    space_size: int
    palette: Palette


@dataclass
class Rgba:
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

CallbackParams: TypeAlias = tuple[dict[str, Any],
                                  Maze,
                                  EngineConfig,
                                  SwitcherCallback]
Callback: TypeAlias = Callable[[CallbackParams], None]

LoopConfig: TypeAlias = tuple[Callback, dict[str, Any]]
LoopConfigCallback: TypeAlias = Callable[[], LoopConfig]


class Engine(Protocol):

    def loop(self, loop_key: str) -> None:
        ...


class GraphicalEngine:

    def __init__(
        self,
        maze: Maze,
        config: EngineConfig,
        loops: dict[str, LoopConfigCallback],
    ) -> None:
        self._maze: Maze = maze
        self._width: int = maze.width * config.cell_size
        self._height: int = maze.height * config.cell_size
        self._config: EngineConfig = config
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

    @staticmethod
    def _update(args: tuple["GraphicalEngine", LoopConfig]) -> None:
        self, (callback, context) = args

        callback((context, self._maze, self._config, self._get_switcher()))

        if self._maze.flush():
            self._render()

    def _get_switcher(self) -> SwitcherCallback:

        def switcher(loop_key: str) -> None:
            if loop_key not in self._loop_registry:
                raise KeyError(f"loop {loop_key} does not exists")
            self._mlx.mlx_loop_hook(
                self._mlx_ptr,
                self._update,
                (self, self._loop_registry[loop_key]()),
            )

        return switcher

    def loop(self, loop_key: str) -> None:
        if loop_key not in self._loop_registry:
            raise KeyError(f"loop {loop_key} does not exists")
        self._mlx.mlx_loop_hook(
            self._mlx_ptr,
            self._update,
            (self, self._loop_registry[loop_key]()),
        )
        self._mlx.mlx_loop(self._mlx_ptr)

    def _render(self) -> None:
        self._mlx.mlx_clear_window(self._mlx_ptr, self._window)

        for cy in range(self._maze.height):
            for cx in range(self._maze.width):
                self._draw(cx, cy, self._maze.map_data[cy][cx])

        self._mlx.mlx_put_image_to_window(
            self._mlx_ptr, self._window, self._image, 0, 0
        )

    def _draw(self, cx: int, cy: int, flags: int) -> None:
        border_size: int = self._config.border_size
        cell_size: int = self._config.cell_size
        space_size: int = self._config.space_size

        border_px: bytes = Rgba.bytes_from_int(self._config.palette.border)
        default_px: bytes = Rgba.bytes_from_int(self._config.palette.default)
        unreachable_px: bytes = Rgba.bytes_from_int(
            self._config.palette.unreachable
        )
        cursor_px: bytes = Rgba.bytes_from_int(self._config.palette.cursor)
        path_px: bytes = Rgba.bytes_from_int(self._config.palette.path)

        w_border: int = border_size if flags & CellFlag.WEST else 0
        e_border: int = border_size if flags & CellFlag.EAST else 0
        n_border: int = border_size if flags & CellFlag.NORTH else 0
        s_border: int = border_size if flags & CellFlag.SOUTH else 0

        inner_width: int = cell_size - w_border - e_border
        inner_width_space: int = inner_width - space_size * 2

        space: bytes = default_px * space_size
        default_line: bytes = ((border_px * w_border) + space +
                               (default_px * inner_width_space) + space +
                               (border_px * e_border))
        cursor_line: bytes = ((border_px * w_border) + space +
                              (cursor_px * inner_width_space) + space +
                              (border_px * e_border))
        path_line: bytes = ((border_px * w_border) + (path_px * inner_width) +
                            (border_px * e_border))
        unreachable_line: bytes = ((border_px * w_border) +
                                   (unreachable_px * inner_width) +
                                   (border_px * e_border))
        border_line: bytes = border_px * cell_size

        x0 = cx * cell_size
        y0 = cy * cell_size
        for dy in range(cell_size):
            offset = (y0 + dy) * self._ppr + (x0 * self._bpp)
            if dy < n_border or dy >= cell_size - s_border:
                self._image_bytes[offset:offset + self._bpp * cell_size] = (
                    border_line
                )
            elif flags & CellFlag.UNREACHABLE:
                self._image_bytes[offset:offset + self._bpp * cell_size] = (
                    unreachable_line
                )
            elif (dy >= n_border + space_size and
                  dy < cell_size - s_border - space_size and
                  flags & CellFlag.CURSOR):
                self._image_bytes[offset:offset + self._bpp * cell_size] = (
                    cursor_line
                )
            elif flags & CellFlag.PATH:
                self._image_bytes[offset:offset + self._bpp * cell_size] = (
                    path_line
                )
            else:
                self._image_bytes[offset:offset + self._bpp * cell_size] = (
                    default_line
                )
