from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Protocol, TypeAlias, TypedDict

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


class Palette(TypedDict):
    cursor: int
    border: int
    default: int


@dataclass()
class RendererConfig:
    border_size: int
    cell_size: int
    palette: Palette


@dataclass
class Rgba:
    r: int
    g: int
    b: int
    a: int

    @staticmethod
    def from_int(color: int) -> "Rgba":
        rgba = Rgba(
            a=color & 0xFF,
            r=(color >> 24) & 0xFF,
            g=(color >> 16) & 0xFF,
            b=(color >> 8) & 0xFF,
        )
        return rgba


RendererCallbackParams: TypeAlias = tuple[Maze, RendererConfig]
RendererCallback: TypeAlias = Callable[[RendererCallbackParams], None]


class Renderer(Protocol):

    def loop(self, callback: RendererCallback) -> None:
        ...


class TerminalRenderer:

    def render(self) -> None:
        raise NotImplementedError("terminal render method not implemented")


class GraphicalRenderer:

    def __init__(self, maze: Maze, config: RendererConfig) -> None:
        self._maze: Maze = maze
        self._width: int = maze.width * config.cell_size
        self._height: int = maze.height * config.cell_size
        self._config: RendererConfig = config
        self._mlx: Mlx = Mlx()
        self._mlx_ptr: Any = self._mlx.mlx_init()
        self._image = self._mlx.mlx_new_image(
            self._mlx_ptr, self._width, self._height
        )
        self._image_data: tuple[
            Any, ...] = self._mlx.mlx_get_data_addr(self._image)
        self._window = self._mlx.mlx_new_window(
            self._mlx_ptr, self._width, self._height, "A-Maze-ing"
        )

    def loop(self, callback: RendererCallback) -> None:
        self._mlx.mlx_loop_hook(self._mlx_ptr, self._update, (self, callback))
        self._mlx.mlx_loop(self._mlx_ptr)

    def _fill(self, cx: int, cy: int, flags: int) -> None:
        bpp = self._image_data[1] // 8
        line = self._image_data[2]
        img = self._image_data[0]

        border_color: Rgba = Rgba.from_int(self._config.palette.get("border"))
        cell_color: Rgba = Rgba.from_int(self._config.palette.get("default"))

        border_size: int = self._config.border_size
        cell_size: int = self._config.cell_size

        x0 = cx * cell_size
        y0 = cy * cell_size

        x_start: int = x0 - 1
        x_end: int = x0 + cell_size
        y_start: int = y0 - 1
        y_end: int = y0 + cell_size

        if flags & (1 << CellFlag.NORTH):
            y_start += border_size
        if flags & (1 << CellFlag.SOUTH):
            y_end -= border_size
        if flags & (1 << CellFlag.WEST):
            x_start += border_size
        if flags & (1 << CellFlag.EAST):
            x_end -= border_size

        for dy in range(cell_size):
            y = y0 + dy
            offset = y * line + x0 * bpp
            for dx in range(cell_size):
                x = x0 + dx
                if x_start < x < x_end and y_start < y < y_end:
                    self._put_pixel(img, offset, cell_color)
                else:
                    self._put_pixel(img, offset, border_color)
                offset += bpp

    def _put_pixel(self, img: Any, offset: int, rgba: Rgba) -> None:
        img[offset + 0] = rgba.a
        img[offset + 1] = rgba.r
        img[offset + 2] = rgba.g
        img[offset + 3] = rgba.b

    def _render(self) -> None:
        maze_map: list[list[int]] | None = self._maze.map

        if maze_map is None:
            raise ValueError("invalid maze map")

        for cy in range(self._maze.height):
            for cx in range(self._maze.width):
                self._fill(cx, cy, maze_map[cy][cx])

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
