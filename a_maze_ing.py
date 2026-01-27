import logging
import logging.config
import os
import random
import sys
from dataclasses import dataclass
from typing import Iterator

from pydantic import ValidationError

from maze import Maze
from maze.engine import (
    EngineConfig,
    GraphicalEngine,
    Palette,
)
from maze.generator import generate
from maze.loader import load
from maze.solving import solve

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
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}


def random_color() -> int:
    color = 0
    color |= random.randint(0x55, 0xFF) << 24
    color |= random.randint(0x55, 0xFF) << 16
    color |= random.randint(0x55, 0xFF) << 8
    color |= 0xFF
    return color


@dataclass
class Context:
    frame: int = 0
    generator: Iterator[int] | None = None
    solver: Iterator[int] | None = None


def keypress(
    keycode: int,
    maze: Maze,
    palette: Palette,
    context: Context,
    controls: GraphicalEngine.Controls,
) -> int:
    match keycode:
        case 103:  # g
            controls.reinitialize()
            context.generator = generate(maze)
        case 99:  # c
            controls.clear()
            context.solver = solve(maze)
        case 113:  # q
            controls.stop()
        case 114:  # r
            for key in vars(palette):
                if key != "empty":
                    setattr(palette, key, random_color())
        case 110:  # n
            controls.clear()
            maze.random_entry_exit()
        case 115:  # s
            controls.toggle_path()

    return 0


def update(
    maze: Maze,
    palette: Palette,
    context: Context,
    controls: GraphicalEngine.Controls,
) -> None:
    logger.debug(f"update {context.frame}")
    context.frame += 1

    if context.generator is not None:
        try:
            next(context.generator)
        except StopIteration:
            context.generator = None
            pass
    if context.solver is not None:
        try:
            next(context.solver)
        except StopIteration:
            context.solver = None
            pass

    controls.render()


def main(argc: int, argv: list[str]) -> None:
    logging.config.dictConfig(LOGGING_CONFIG)

    if argc < 2:
        logger.error(
            f"Usage: python3 {os.path.basename(__file__)} <config_file>"
        )
        sys.exit(1)

    try:
        maze: Maze = load(argv[1])
    except ValidationError as e:
        for error in e.errors():
            field = " -> ".join(str(item) for item in error["loc"])
            message = error["msg"]
            logger.error(f"{type(e).__name__}: {message} ({field}) ")
        sys.exit(1)
    except Exception as e:
        logger.error(f"{type(e).__name__}: {e}")
        sys.exit(1)

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
        """
            === A-Maze-Ing ===
            [g] Re-generate a new maze
            [c] Compute path from entry to exit
            [s] Show/Hide path from entry to exit
            [r] Rotate maze colors
            [n] New random entry and exit points
            [q] Quit
            Choice ? [g/c/s/r/n/q]:
            """,
        flush=True,
    )

    engine.loop(
        update,
        keypress=keypress,
        context=Context(),
    )


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
