import logging
import logging.config
import os
import random
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
from loader import load
from pydantic import ValidationError

from mazegen import Maze

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
    generator: Iterator[int] | None = None
    solver: Iterator[int] | None = None


def keypress(
    keycode: int,
    maze: Maze,
    controls: GraphicalEngine.Controls,
    context: EngineContext,
) -> int:
    args: LoopContext = context.args
    palette = context.palette

    match keycode:
        case KeyCode.G:
            controls.reinitialize()
            args.generator = maze.iter_generate()
        case KeyCode.C:
            controls.clear()
            args.solver = maze.iter_solve()
        case KeyCode.Q:
            controls.stop()
        case KeyCode.R:
            palette.randomize()
        case KeyCode.N:
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
            controls.stop(4)


def main() -> None:
    logging.config.dictConfig(LOGGING_CONFIG)

    if len(sys.argv) < 2:
        logger.error(
            f"Usage: python3 {os.path.basename(__file__)} <config_file>"
        )
        sys.exit(1)

    maze: Maze = load(sys.argv[1])

    random.seed(maze.seed)
    engine = GraphicalEngine(
        maze=maze,
        config=EngineConfig(wall_size=2, cell_size=40),
        palette=Palette(
            empty=0x000000FF,
            wall=0x0000AAFF,
            unreachable=0xAAAAAAFF,
            cursor=0x00FF00FF,
            path=0xFF000055,
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
        sys.exit(2)
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")
        sys.exit(3)
