import logging
import logging.config
import os
import sys
from dataclasses import dataclass
from typing import Iterator

from pydantic import ValidationError

from mazegen import CellState, Maze, WallDescriptor
from src.colors import Palette
from src.engine import (
    EngineConfig,
    EngineContext,
    GraphicalEngine,
    KeyCode,
)
from src.errors import ExitCode
from src.loader import load

logger: logging.Logger = logging.getLogger(__name__)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": (
                "%(asctime)s [%(levelname)s] %(name)s "
                "(%(filename)s:%(lineno)d): %(message)s"
            ),
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}


@dataclass
class LoopContext:
    """
    This stores iterators and state for the loop and idle path animation.

    Attributes:
        generator: Iterator used to animate maze generation.
        solver: Iterator used to animate maze solving.
        idle_index: Current index in the idle animation path.
        prev_idle_cell: Previous animated cell to restore after moving.
        idle_cell: Current animated cell position.
    """

    generator: Iterator[int] | None = None
    solver: Iterator[int] | None = None
    idle_index: int = 0
    prev_idle_cell: tuple[int, int] | None = None
    idle_cell: tuple[int, int] = (0, 0)

    def reset_idle(self) -> None:
        """
        This resets the idle animation to its initial state.
        """
        self.idle_index = 0
        self.prev_idle_cell = None


def keypress(
    keycode: int,
    maze: Maze,
    controls: GraphicalEngine.Controls,
    context: EngineContext,
) -> int:
    """
    This handles input and triggers generation, solving, or UI actions.

    Args:
        keycode: Pressed key code from the engine.
        maze: Maze instance being displayed and modified.
        controls: Engine controls used to render and stop the loop.
        context: Engine context holding palette and loop arguments.

    Returns:
        Always returns 0 to keep the engine running.
    """
    args: LoopContext = context.args
    palette = context.palette

    match keycode:
        case KeyCode.G:
            args.reset_idle()
            controls.reinitialize()
            args.generator = maze.iter_generate()
        case KeyCode.C:
            args.reset_idle()
            controls.clear()
            args.solver = maze.iter_solve()
        case KeyCode.Q:
            controls.stop()
        case KeyCode.R:
            palette.randomize()
        case KeyCode.N:
            args.reset_idle()
            controls.clear()
            maze.random_entry_exit()
            controls.render()
        case KeyCode.S:
            controls.toggle_path()

    return 0


def idle_animation_tick(maze: Maze, args: LoopContext) -> None:
    """
    This advance the maze path animation by one step and update cell states.

    Args:
        maze: Maze instance providing the path and state modification methods.
        args: Context object holding the animation state and current position.
    """
    len_shortest_path: int = len(maze.shortest_path)
    char: str = maze.shortest_path[args.idle_index % len_shortest_path]
    if args.prev_idle_cell:
        if args.prev_idle_cell == maze.entry:
            maze.set_state(*args.prev_idle_cell, CellState.ENTRY)
        elif args.prev_idle_cell == maze.exit:
            maze.set_state(*args.prev_idle_cell, CellState.EXIT)
        else:
            maze.set_state(*args.prev_idle_cell, CellState.PATH)

    if args.idle_cell == maze.exit:
        args.idle_cell = maze.entry
    args.prev_idle_cell = args.idle_cell

    dx, dy = WallDescriptor.cardinals.get(char, (0, 0))
    args.idle_cell = (args.idle_cell[0] + dx, args.idle_cell[1] + dy)

    if args.idle_cell != maze.exit:
        maze.set_state(*args.idle_cell, CellState.IDLE_PATH)

    args.idle_index += 1


def update(
    maze: Maze,
    controls: GraphicalEngine.Controls,
    context: EngineContext,
) -> None:
    """
    This advances iterators and renders frames, then exports after solving.

    Args:
        maze: Maze instance being generated or solved.
        controls: Engine controls used to render and stop the loop.
        context: Engine context holding loop arguments.
    """
    args: LoopContext = context.args

    if args.generator is not None:
        for _ in args.generator:
            controls.render()
        args.generator = None

    if args.solver is not None:
        for _ in args.solver:
            controls.render()
        args.solver = None
        try:
            maze.export()
        except (OSError, UnicodeEncodeError) as e:
            logger.error(f"export failed: {type(e).__name__}: {e}")
            controls.stop(ExitCode.FILE_ERROR)
        args.idle_cell = maze.entry
        args.prev_idle_cell = None

    if maze.shortest_path:
        idle_animation_tick(maze, args)
        controls.render()


def main() -> None:
    """
    This loads a config, creates the engine, and starts the interactive loop.
    """
    logging.config.dictConfig(LOGGING_CONFIG)

    if len(sys.argv) < 2:
        logger.error(
            f"Usage: python3 {os.path.basename(__file__)} <config_file>"
        )
        sys.exit(ExitCode.ARGUMENTS_ERROR)

    maze: Maze = load(sys.argv[1])

    if maze.width > 50 or maze.height > 50:
        logger.error("maze width or height cannot be greater than 50")
        sys.exit(ExitCode.VALUE_ERROR)

    engine = GraphicalEngine(
        maze=maze,
        config=EngineConfig(wall_size=2, cell_size=42),
        palette=Palette(
            empty=0x000000FF,
            wall=0x0000AAFF,
            unreachable=0xAAAAAAFF,
            cursor=0x00FF00FF,
            path=0xFF000055,
            idle_path=0xFF000066,
            seek=0x00FF0033,
            seek_premium=0xFF00FFAA,
            entry=0xFFFFFFFF,
            exit=0xFFFFFFFF,
        ),
    )

    print(
        "=== A-Maze-Ing ===",
        "[g] Re-generate a new maze",
        "[c] Compute path from entry to exit",
        "[s] Show/Hide path from entry to exit",
        "[r] Rotate maze colors",
        "[n] New random entry and exit points",
        "[q] Quit",
        sep="\n",
        flush=True,
    )

    exit_code: int = engine.loop(
        update,
        keypress=keypress,
        args=LoopContext(
            generator=maze.iter_generate(),
            solver=maze.iter_solve(),
        ),
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except ValidationError as e:
        for error in e.errors():
            field = " -> ".join(str(item) for item in error["loc"])
            message = error["msg"]
            logger.error(f"{type(e).__name__}: {message} ({field}) ")
        sys.exit(ExitCode.VALIDATION_ERROR)
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")
        sys.exit(ExitCode.UNEXPECTED_ERROR)
