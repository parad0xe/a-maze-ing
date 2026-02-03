import logging
import logging.config
import os
import sys
from dataclasses import dataclass
from typing import Iterator

from colors import Palette
from engine import (
    EngineConfig,
    EngineContext,
    GraphicalEngine,
    KeyCode,
)
from errors import ExitCode
from loader import load
from pydantic import ValidationError

from mazegen import CellState, Maze

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
    This context stores the current generator and solver iterators.

    Attributes:
        generator: Iterator used to animate maze generation.
        solver: Iterator used to animate maze solving.
    """

    generator: Iterator[int] | None = None
    solver: Iterator[int] | None = None
    idle_index: int = 0
    idle_previous_cell: tuple[int, int] | None = None
    idle_cell: tuple[int, int] = (0, 0)


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
            args.idle_index = 0
            controls.reinitialize()
            args.generator = maze.iter_generate()
        case KeyCode.C:
            args.idle_index = 0
            controls.clear()
            args.solver = maze.iter_solve()
        case KeyCode.Q:
            controls.stop()
        case KeyCode.R:
            palette.randomize()
        case KeyCode.N:
            args.idle_index = 0
            controls.clear()
            maze.random_entry_exit()
            controls.render()
        case KeyCode.S:
            controls.toggle_path()

    return 0


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
        args.idle_previous_cell = None

    if maze.shortest_path:
        len_shortest_path: int = len(maze.shortest_path)
        char: str = maze.shortest_path[args.idle_index % len_shortest_path]
        if args.idle_previous_cell:
            if args.idle_previous_cell == maze.entry:
                maze.set_state(*args.idle_previous_cell, CellState.ENTRY)
            elif args.idle_previous_cell == maze.exit:
                maze.set_state(*args.idle_previous_cell, CellState.EXIT)
            else:
                maze.set_state(*args.idle_previous_cell, CellState.PATH)

        if args.idle_cell == maze.exit:
            args.idle_cell = maze.entry
        args.idle_previous_cell = args.idle_cell
        if char == "W":
            args.idle_cell = (args.idle_cell[0] - 1, args.idle_cell[1])
        elif char == "E":
            args.idle_cell = (args.idle_cell[0] + 1, args.idle_cell[1])
        elif char == "S":
            args.idle_cell = (args.idle_cell[0], args.idle_cell[1] + 1)
        elif char == "N":
            args.idle_cell = (args.idle_cell[0], args.idle_cell[1] - 1)

        if args.idle_cell != maze.exit:
            maze.set_state(*args.idle_cell, CellState.IDLE_PATH)

        args.idle_index += 1
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
        config=EngineConfig(wall_size=2, cell_size=50),
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
