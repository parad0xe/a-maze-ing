import logging
import os
import random
import sys

from pydantic import ValidationError

from maze import Maze
from maze.engine import (
    EngineConfig,
    GraphicalEngine,
    Palette,
    UpdateCallback,
    UpdateCallbackParams,
)
from maze.generator import generate
from maze.loader import ParseError, load
from maze.solving import solve

logger: logging.Logger = logging.getLogger(__name__)


def random_color() -> int:
    color = 0
    color |= random.randint(0x22, 0xDD) << 24
    color |= random.randint(0x22, 0xDD) << 16
    color |= random.randint(0x22, 0xDD) << 8
    color |= 0xFF
    return color


def menu(maze: Maze) -> tuple[UpdateCallback, dict]:

    def update(params: UpdateCallbackParams) -> None:
        (context, maze, palette, switch, exit, reset, clear) = params
        print("menu")

        command = (
            input(
                """
                === A-Maze-Ing ===
                [g] Re-generate a new maze
                [c] Compute path from entry to exit
                [s] Show/Hide path from entry to exit
                [r] Rotate maze colors
                [n] New random entry and exit points
                [q] Quit
                Choice ? [g/c/s/r/n/q]: 
                """
            ).strip().lower()
        )
        match command:
            case "g":
                reset()
                switch("generator")
            case "c":
                switch("solver")
            case "s":
                maze.hide_path = not maze.hide_path
            case "r":
                for key in vars(palette):
                    setattr(palette, key, random_color())
            case "n":
                maze.entry = (
                    random.randint(0, maze.width - 1),
                    random.randint(0, maze.height - 1),
                )
                maze.exit = (
                    random.randint(0, maze.width - 1),
                    random.randint(0, maze.height - 1),
                )
                clear()
            case "q":
                exit()
                return

    return (update, {})


def generator(maze: Maze) -> tuple[UpdateCallback, dict]:

    def update(params: UpdateCallbackParams) -> None:
        (context, maze, palette, switch, exit, reset, clear) = params

        try:
            (x, y, flag) = next(context["iter"])
            maze.set(x, y, flag)
        except StopIteration:
            switch("menu")

    return (update, {"iter": generate(maze)})


def solver(maze: Maze) -> tuple[UpdateCallback, dict]:

    def update(params: UpdateCallbackParams) -> None:
        (context, maze, palette, switch, exit, reset, clear) = params
        try:
            next(context["iter"])
        except StopIteration:
            switch("menu")

    return (update, {"iter": solve(maze)})


def main(argc: int, argv: list[str]) -> None:
    if argc < 2:
        logger.error(
            f"Usage: python3 {os.path.basename(__file__)} <config_file>"
        )

    try:
        maze: Maze = load(argv[1])
    except ValidationError as e:
        for error in e.errors():
            field = " -> ".join(str(item) for item in error["loc"])
            message = error["msg"]
            logger.error(f"{type(e).__name__}: {message} {field}) ")
        sys.exit(1)
    except (OSError, ParseError, FileNotFoundError) as e:
        logger.error(f"{type(e).__name__}: {e}")
        sys.exit(1)

    engine = GraphicalEngine(
        maze=maze,
        config=EngineConfig(border_size=2, cell_size=50),
        palette=Palette(
            border=0x0000AAFF,
            unreachable=0xAAAAAAFF,
            cursor=0x00FF00FF,
            path=0xFF0000AA,
            seek=0x00FF0033,
            seek_premium=0xFF00FFAA,
            default=0x000000FF,
            entry=0xFFFFFFFF,
            exit=0xFFFFFFFF,
        ),
        loops={
            "menu": menu,
            "generator": generator,
            "solver": solver,
        },
    )
    engine.loop("menu")


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
