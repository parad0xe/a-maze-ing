from typing import Protocol

from .maze import Maze
from enum import IntEnum
from typing import Any
from mlx import Mlx

"""
examples:

render(TerminalRenderer, maze)
render(GraphicalRenderer, maze)
"""


class Cell(IntEnum):
    NORTH = (1 << 0)
    EAST = (1 << 1)
    SOUTH = (1 << 2)
    WEST = (1 << 3)
    CURSOR = (1 << 4)
    SEEK = (1 << 5)
    PATH = (1 << 6)


class Renderer(Protocol):

    def render(self) -> None:
        ...


class TerminalRenderer:

    def render(self) -> None:
        raise NotImplementedError("terminal render method not implemented")


class GraphicalRenderer:

    def __init__(self, maze: Maze, scale: int) -> None:
        self._maze = maze
        self._mlx: Mlx = Mlx()
        self._mlx_ptr: Any = self._mlx.mlx_init()
        self._scale = scale
        self._image = self._mlx.mlx_new_image(
            self._mlx_ptr,
            maze.width * self._scale,
            maze.height * self._scale,
        )
        self._image_data: tuple[Any, ...] = self._mlx.mlx_get_data_addr(
            self._image
        )
        self._window = self._mlx.mlx_new_window(
            self._mlx_ptr,
            maze.width * self._scale,
            maze.height * self._scale,
            "A-Maze-ing"
        )

    def put_pixel_img(self, x: int, y: int, color: int) -> None:
        idx = (y * self._image_data[2] + x * (self._image_data[1] // 8))
        image = self._image_data[0]
        image[idx + 0] = color & 0xFF
        image[idx + 1] = (color >> 8) & 0xFF
        image[idx + 2] = (color >> 16) & 0xFF
        image[idx + 3] = (color >> 24) & 0xFF

    def fill_cell(self, cx: int, cy: int, color: int, cell: int) -> None:
        bpp = self._image_data[1] // 8
        line = self._image_data[2]
        img = self._image_data[0]

        x0 = cx * self._scale
        y0 = cy * self._scale

        b0 = color & 0xFF
        b1 = (color >> 8) & 0xFF
        b2 = (color >> 16) & 0xFF
        b3 = (color >> 24) & 0xFF

        x_start: int = 0
        x_end: int = self._scale
        y_start: int = 0
        y_end: int = self._scale
        if cell & 0x1:
            y_start = int(self._scale * 0.2)
        if cell & 0x2:
            x_end = int(self._scale * 0.8)
        if cell & 0x4:
            y_end = int(self._scale * 0.8)
        if cell & 0x8:
            x_start = int(self._scale * 0.2)

        for dy in range(self._scale):
            y = y0 + dy
            row = y * line + x0 * bpp
            for x in range(self._scale):
                if x_start < x < x_end and y_start < dy < y_end:
                    img[row + 0] = 255
                    img[row + 1] = 0
                    img[row + 2] = 0
                    img[row + 3] = 140
                    row += bpp
                else:
                    img[row + 0] = b0
                    img[row + 1] = b1
                    img[row + 2] = b2
                    img[row + 3] = b3
                    row += bpp


    def update(self) -> None:
        m = self._maze.map
        h = self._maze.height
        w = self._maze.width

        for cy in range(h):
            for cx in range(w):
                color = 0xFF000077
                self.fill_cell(cx, cy, color, m[cy][cx])

    def render(self) -> None:
        def tick(_): # main thread
            self.update()
            self._mlx.mlx_put_image_to_window(
                self._mlx_ptr,
                self._window,
                self._image,
                0,
                0
            )
            input("t")

        self._mlx.mlx_loop_hook(
            self._mlx_ptr, tick, None
        )
        self._mlx.mlx_loop(self._mlx_ptr)


def render(maze: Maze, renderer: Renderer) -> None:
    renderer.render()
    #raise NotImplementedError("render method not implemented")
