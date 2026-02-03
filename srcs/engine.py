import logging
from enum import IntEnum
from typing import Any, Callable, TypeAlias

import numpy as np
import numpy.typing as npt
from mlx import Mlx
from pydantic import BaseModel, Field

from colors import Palette, Rgba
from mazegen import Cell, CellState, CellWall, Maze

logger: logging.Logger = logging.getLogger(__name__)

KeypressCallback: TypeAlias = Callable[
    [int, Maze, "GraphicalEngine.Controls", "EngineContext"],
    int,
]
UpdateCallback: TypeAlias = Callable[
    [Maze, "GraphicalEngine.Controls", "EngineContext"],
    None,
]

PIXEL_DT = np.dtype("u1, u1, u1, u1")

# typing helpers
TileKey: TypeAlias = tuple[int, int]
Pixel: TypeAlias = np.void
Tile: TypeAlias = npt.NDArray[Pixel]
Tiles: TypeAlias = dict[TileKey, Tile]


class KeyCode(IntEnum):
    """
    This enum stores ASCII key codes used by the engine.

    Attributes:
        C (int): Key code for solve action.
        G (int): Key code for generate action.
        N (int): Key code for random entry and exit.
        Q (int): Key code for quit.
        R (int): Key code for randomize palette.
        S (int): Key code for toggle path display.
    """
    C = 99
    G = 103
    N = 110
    Q = 113
    R = 114
    S = 115


class EngineConfig(BaseModel):
    """
    This model stores graphical sizes used to render the maze.

    Attributes:
        cell_size: Pixel size of one cell square.
        wall_size: Pixel thickness of walls inside a cell.
    """
    cell_size: int = Field(frozen=True)
    wall_size: int = Field(frozen=True)


class EngineContext(BaseModel):
    """
    This model stores user arguments and the active palette for callbacks.

    Attributes:
        args: User provided loop context.
        palette: Palette used to draw tiles.
    """
    args: Any
    palette: Palette


class GraphicalEngine:
    """
    This class renders a Maze with MiniLibX and runs a key and update loop.
    """

    def __init__(
        self,
        maze: Maze,
        config: EngineConfig,
        palette: Palette,
    ) -> None:
        """
        This initializes MLX resources, precomputes tiles, and renders once.

        Args:
            maze: Maze instance to display.
            config: Rendering configuration for cell and wall sizes.
            palette: Colors used to draw maze states and walls.
        """
        self._maze: Maze = maze
        self._width: int = maze.width * config.cell_size
        self._height: int = maze.height * config.cell_size
        self._config: EngineConfig = config
        self._palette: Palette = palette
        self._mlx: Mlx = Mlx()
        self._mlx_ptr: Any = self._mlx.mlx_init()
        self._window: Any = self._mlx.mlx_new_window(
            self._mlx_ptr, self._width, self._height, "A-Maze-ing"
        )
        self._image: Any = self._mlx.mlx_new_image(
            self._mlx_ptr, self._width, self._height
        )
        data: tuple[Any, ...] = self._mlx.mlx_get_data_addr(self._image)
        self._image_bytes: Any = data[0]
        self._bpp: int = data[1] // 8
        self._ppr: int = data[2]
        self._tiles: Tiles = {}
        self._show_path: bool = True

        self._compute_tiles()
        self.controls = GraphicalEngine.Controls(self)
        self.controls.render()

        logger.debug("Graphical engine initialized")

    def _compute_tiles(self) -> None:
        """
        This rebuilds cached tiles for all wall and state combinations.
        """
        wall_size: int = self._config.wall_size
        cell_size: int = self._config.cell_size

        wall_bytes: bytes = Rgba.bytes_from_int(self._palette.wall)
        wall_pixel: Pixel = np.frombuffer(wall_bytes, dtype=PIXEL_DT)[0]

        dump: dict[str, Any] = self._palette.model_dump()
        pixels: dict[int, Pixel] = {}

        for state in CellState:
            value = dump.get(state.name.lower(), None)
            if value is None:
                logger.warning(
                    f"color {state.name.lower()} not defined in the palette"
                )
                continue
            pixel_bytes: bytes = Rgba.bytes_from_int(value)
            pixels[state.value] = np.frombuffer(pixel_bytes, dtype=PIXEL_DT)[0]

        tiles: Tiles = {}
        for state_value, pixel in pixels.items():
            for walls in range(16):
                tile: Tile = np.full((
                    cell_size, cell_size), pixel, dtype=PIXEL_DT
                )

                if walls & CellWall.NORTH:
                    tile[:wall_size, :] = wall_pixel
                if walls & CellWall.SOUTH:
                    tile[-wall_size:, :] = wall_pixel
                if walls & CellWall.EAST:
                    tile[:, -wall_size:] = wall_pixel
                if walls & CellWall.WEST:
                    tile[:, :wall_size] = wall_pixel

                tiles[(walls, state_value)] = tile

        self._tiles = tiles

    @staticmethod
    def _update(
        args: tuple["GraphicalEngine", tuple[UpdateCallback, EngineContext]],
    ) -> None:
        """
        This wraps the callback and refreshes tiles if the palette changed.

        Args:
            args: Engine instance plus (update_callback, engine_context).
        """
        self, (callback, context) = args
        callback(self._maze, self.controls, context)

        if self._palette.flush():
            self._compute_tiles()
            self.controls.render()

    @staticmethod
    def _keypress(
        keycode: int,
        args: tuple["GraphicalEngine", tuple[KeypressCallback, EngineContext]],
    ) -> int:
        """
        This wraps the keypress callback with the engine and context.

        Args:
            keycode: Pressed key code from MLX.
            args: Engine instance plus (keypress_callback, engine_context).

        Returns:
            The callback return code.
        """
        self, (callback, context) = args
        return callback(keycode, self._maze, self.controls, context)

    def loop(
        self,
        callback: UpdateCallback,
        keypress: KeypressCallback | None = None,
        args: Any = None,
    ) -> int:
        """
        This runs the MLX loop with update and optional keypress hooks.

        Args:
            callback: Per frame update callback.
            keypress: Optional keypress callback.
            args: User object stored in EngineContext.args.

        Returns:
            The exit code stored in controls.
        """
        context: EngineContext = EngineContext(
            args=args,
            palette=self._palette,
        )
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
        return self.controls.exit_code

    class Controls:
        """
        This helper exposes safe actions to control the engine loop and view.

        Attributes:
            exit_code: Process exit code set when stopping the loop.
        """
        exit_code: int = 0

        def __init__(self, engine: "GraphicalEngine") -> None:
            """
            This stores a reference to the owning engine.

            Args:
                engine: GraphicalEngine instance to control.
            """
            self._engine: "GraphicalEngine" = engine

        def stop(self, code: int = 0) -> None:
            """
            This stops the MLX loop and stores an exit code.

            Args:
                code: Exit code to return from GraphicalEngine.loop().
            """
            self.exit_code = code
            self._engine._mlx.mlx_loop_exit(self._engine._mlx_ptr)

        def reinitialize(self) -> None:
            """
            This resets the maze and redraws with the path display enabled.
            """
            self._engine._show_path = True
            self._engine._maze.initialize()
            self.render()

        def clear(self) -> None:
            """
            This clears states while keeping unreachable, entry and exit.
            """
            self._engine._show_path = True
            self._engine._maze.mask(
                state=(
                    CellState.UNREACHABLE | CellState.ENTRY | CellState.EXIT
                )
            )
            self.render()

        def toggle_path(self) -> None:
            """
            This toggles path and search overlays visibility then redraws.
            """
            self._engine._show_path = not self._engine._show_path
            self.render()

        def render(self) -> None:
            """
            This draws the maze grid into the image buffer and displays it.
            """
            self._engine._mlx.mlx_clear_window(
                self._engine._mlx_ptr, self._engine._window
            )

            cell_size: int = self._engine._config.cell_size

            view_2d: npt.NDArray[Pixel] = np.frombuffer(
                self._engine._image_bytes, dtype=PIXEL_DT
            ).reshape((self._engine._height, self._engine._width))

            for cy in range(self._engine._maze.height):
                y0 = cy * cell_size

                for cx in range(self._engine._maze.width):
                    x0 = cx * cell_size
                    cell: Cell = self._engine._maze.get_cell(cx, cy)

                    walls: int = cell["walls"].item()
                    state: int = cell["state"].item()

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
