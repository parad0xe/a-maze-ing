import logging
from enum import IntEnum
from typing import Any, Callable, TypeAlias

import numpy as np
from mlx import Mlx
from pydantic import BaseModel, Field

from maze.colors import Palette, Rgba
from maze.maze import Cell, CellState, CellWall, Maze

logger: logging.Logger = logging.getLogger(__name__)

KeypressCallback: TypeAlias = Callable[
    [
        int,
        Maze,
        Palette,
        Any,
        "GraphicalEngine.Controls",
    ],
    int,
]
UpdateCallback: TypeAlias = Callable[
    [
        Maze,
        Palette,
        Any,
        "GraphicalEngine.Controls",
    ],
    None,
]

PIXEL_DT = np.dtype("u1, u1, u1, u1")


class KeyCode(IntEnum):
    C = 99
    G = 103
    N = 110
    Q = 113
    R = 114
    S = 115


class EngineConfig(BaseModel):
    cell_size: int = Field(frozen=True)
    wall_size: int = Field(frozen=True)


class GraphicalEngine:

    def __init__(
        self,
        maze: Maze,
        config: EngineConfig,
        palette: Palette,
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
        self._tiles: dict = {}
        self._show_path: bool = True

        self._compute_tiles()
        self.controls = GraphicalEngine.Controls(self)
        self.controls.render()

        logger.debug("Graphical engine initialized")

    def _compute_tiles(self) -> None:
        wall_size: int = self._config.wall_size
        cell_size: int = self._config.cell_size

        wall_bytes: bytes = Rgba.bytes_from_int(self._palette.wall)
        wall_pixel = np.frombuffer(wall_bytes, dtype=PIXEL_DT)[0]

        dump: dict[str, Any] = self._palette.model_dump()
        pixels: dict = {}
        for state in CellState:
            value = dump.get(state.name.lower(), None)
            if value is None:
                logger.warning(
                    f"color {state.name.lower()} not defined in the palette"
                )
                continue
            pixel_bytes = Rgba.bytes_from_int(value)
            pixels[state.value] = np.frombuffer(pixel_bytes, dtype=PIXEL_DT)[0]

        tiles: dict = {}
        for state, pixel in pixels.items():
            for walls in range(16):
                tile = np.full((cell_size, cell_size), pixel, dtype=PIXEL_DT)

                if walls & CellWall.NORTH:
                    tile[:wall_size, :] = wall_pixel
                if walls & CellWall.SOUTH:
                    tile[-wall_size:, :] = wall_pixel
                if walls & CellWall.EAST:
                    tile[:, -wall_size:] = wall_pixel
                if walls & CellWall.WEST:
                    tile[:, :wall_size] = wall_pixel

                tiles[(walls, state)] = tile

        self._tiles = tiles

    @staticmethod
    def _update(
        args: tuple["GraphicalEngine", tuple[UpdateCallback, Any]],
    ) -> None:
        self, (callback, context) = args
        callback(self._maze, self._palette, context, self.controls)

        if self._palette.flush():
            self._compute_tiles()

    @staticmethod
    def _keypress(keycode: int, args: tuple["GraphicalEngine", Any]) -> int:
        self, (callback, context) = args
        return callback(
            keycode, self._maze, self._palette, context, self.controls
        )

    def loop(
        self,
        callback: UpdateCallback,
        keypress: KeypressCallback | None = None,
        context: Any = None,
    ) -> None:
        if keypress is not None:
            self._mlx.mlx_key_hook(
                self._window,
                self._keypress,
                (self, (keypress, context)),
            )
        self._mlx.mlx_loop_hook(
            self._mlx_ptr,
            self._update,
            (self, (callback, context)),
        )
        self._mlx.mlx_loop(self._mlx_ptr)

    class Controls:

        def __init__(self, engine: "GraphicalEngine") -> None:
            self._engine: "GraphicalEngine" = engine

        def stop(self) -> None:
            self._engine._mlx.mlx_loop_exit(self._engine._mlx_ptr)

        def reinitialize(self) -> None:
            self._engine._show_path = True
            self._engine._maze.initialize()
            self.render()

        def clear(self) -> None:
            self._engine._show_path = True
            self._engine._maze.mask(
                state=(
                    CellState.UNREACHABLE | CellState.ENTRY | CellState.EXIT
                )
            )
            self.render()

        def toggle_path(self) -> None:
            self._engine._show_path = not self._engine._show_path
            self.render()

        def render(self) -> None:
            self._engine._mlx.mlx_clear_window(
                self._engine._mlx_ptr, self._engine._window
            )

            cell_size = self._engine._config.cell_size

            view_2d = np.frombuffer(
                self._engine._image_bytes, dtype=PIXEL_DT
            ).reshape((self._engine._height, self._engine._width))

            for cy in range(self._engine._maze.height):
                y0 = cy * cell_size

                for cx in range(self._engine._maze.width):
                    x0 = cx * cell_size
                    cell: Cell = self._engine._maze.get_cell(cx, cy)

                    walls = cell["walls"].item()
                    state = cell["state"].item()

                    if not self._engine._show_path and state & (
                            CellState.PATH | CellState.SEEK |
                            CellState.SEEK_PREMIUM):
                        state = CellState.EMPTY
                    view_2d[y0:y0 + cell_size, x0:x0 + cell_size] = (
                        self._engine._tiles[(walls, state)]
                    )

            self._engine._mlx.mlx_put_image_to_window(
                self._engine._mlx_ptr,
                self._engine._window,
                self._engine._image,
                0,
                0,
            )
