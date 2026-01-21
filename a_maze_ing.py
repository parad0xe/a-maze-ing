import logging
import os
import sys

from maze import Maze, generate, load, render, solve
from maze.error import ErrCode, ParseError
from maze.renderer import GraphicalRenderer

logger = logging.getLogger(__name__)


def main(argc: int, argv: list[str]) -> int:
    if argc < 2:
        logger.error(
            f"Usage: python3 {os.path.basename(__file__)} <config_file>"
        )
        return ErrCode.INPUT_ERROR

    try:
        maze: Maze = load(argv[1])
    except ParseError as e:
        logger.error(f"parse error: {e}")
        return ErrCode.PARSE_ERROR

    generate(maze)
    solve(maze)
    render(maze, GraphicalRenderer)

    #  print function
    while True:
        command = (
            input(
                """=== A-Maze-Ing ===
            [r] Re-generate a new maze
            [s] Show/Hide path from entry to exit
            [c] Rotate maze colors
            [q] Quit
            Choice ? [r/s/c/q]: """
            ).strip().lower()
        )
        match command:
            case "r":
                pass
            case "s":
                pass
            case "c":
                pass
            case "q":
                return ErrCode.NO_ERROR
            case "" | _:
                continue

        return ErrCode.NO_ERROR


if __name__ == "__main__":
    status: int = main(len(sys.argv), sys.argv)
    sys.exit(status)
