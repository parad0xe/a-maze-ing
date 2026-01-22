from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Protocol, TypeAlias

from mlx import Mlx

from .maze import Maze


class CellFlag(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    CURSOR = 4
    SEEK = 5
    PATH = 6
    UNREACHABLE = 7


@dataclass()
class Palette:
    cursor: int
    border: int
    unreachable: int
    default: int


@dataclass()
class RendererConfig:
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
        return bytes([self.a, self.r, self.g, self.b])

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


RendererCallbackParams: TypeAlias = tuple[Maze, RendererConfig]
RendererCallback: TypeAlias = Callable[[RendererCallbackParams], None]


class Renderer(Protocol):

    def loop(self, callback: RendererCallback) -> None:
        ...


class GraphicalRenderer:

    def __init__(self, maze: Maze, config: RendererConfig) -> None:
        self._maze: Maze = maze
        self._width: int = maze.width * config.cell_size
        self._height: int = maze.height * config.cell_size
        self._config: RendererConfig = config
        self._mlx: Mlx = Mlx()
        self._mlx_ptr: Any = self._mlx.mlx_init()
        self._window = self._mlx.mlx_new_window(
            self._mlx_ptr, self._width, self._height, "A-Maze-ing"
        )
        self._image = self._mlx.mlx_new_image(
            self._mlx_ptr, self._width, self._height
        )

        data: tuple[Any, ...] = self._mlx.mlx_get_data_addr(self._image)
        self._img: Any = data[0]
        self._bpp: int = data[1] // 8
        self._ppr: int = data[2]

    def loop(self, callback: RendererCallback) -> None:
        self._mlx.mlx_loop_hook(self._mlx_ptr, self._update, (self, callback))
        self._mlx.mlx_loop(self._mlx_ptr)

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

        w_border: int = border_size if flags & (1 << CellFlag.WEST) else 0
        e_border: int = border_size if flags & (1 << CellFlag.EAST) else 0
        n_border: int = border_size if flags & (1 << CellFlag.NORTH) else 0
        s_border: int = border_size if flags & (1 << CellFlag.SOUTH) else 0

        inner_width: int = cell_size - w_border - e_border
        inner_width_space: int = inner_width - space_size * 2

        space: bytes = default_px * space_size
        default_line: bytes = ((border_px * w_border) + space +
                               (default_px * inner_width_space) + space +
                               (border_px * e_border))
        cursor_line: bytes = ((border_px * w_border) + space +
                              (cursor_px * inner_width_space) + space +
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
                self._img[offset:offset + self._bpp * cell_size] = (
                    border_line
                )
            elif flags & (1 << CellFlag.UNREACHABLE):
                self._img[offset:offset + self._bpp * cell_size] = (
                    unreachable_line
                )
            elif (dy >= n_border + space_size and
                  dy < cell_size - s_border - space_size and
                  flags & (1 << CellFlag.CURSOR)):
                self._img[offset:offset + self._bpp * cell_size] = (
                    cursor_line
                )
            else:
                self._img[offset:offset + self._bpp * cell_size] = (
                    default_line
                )

    def _render(self) -> None:
        maze_map: list[list[int]] | None = self._maze.map

        if maze_map is None:
            raise ValueError("invalid maze map")

        for cy in range(self._maze.height):
            for cx in range(self._maze.width):
                self._draw(cx, cy, maze_map[cy][cx])

        self._mlx.mlx_put_image_to_window(
            self._mlx_ptr, self._window, self._image, 0, 0
        )

    @staticmethod
    def _update(args: tuple["GraphicalRenderer", RendererCallback]) -> None:
        self, callback = args
        callback((self._maze, self._config))

        if self._maze.is_dirty:
            self._render()
            self._maze.is_dirty = False
