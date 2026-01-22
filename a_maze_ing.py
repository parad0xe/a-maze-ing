import logging
import os
import sys

from maze import Maze, generate, load, render, solve
from maze.error import ErrCode, ParseError
from maze.renderer import GraphicalRenderer
from typing import Any

logger = logging.getLogger(__name__)


def main(argc: int, argv: list[str]) -> int:
    if argc < 2:
        logger.error(
            f"Usage: python3 {os.path.basename(__file__)} <config_file>"
        )
        return ErrCode.INPUT_ERROR

    #try:
    #    maze: Maze = load(argv[1])
    #except ParseError as e:
    #    logger.error(f"parse error: {e}")
    #    return ErrCode.PARSE_ERROR

    maze = Maze()
    maze.map = [
      [9, 5, 1, 5, 3, 9, 1, 5, 3, 9, 5, 5, 1, 7, 9, 5, 1, 5, 1, 1, 5, 1, 1, 5, 3],
      [14, 11, 10, 11, 10, 14, 8, 1, 2, 8, 5, 3, 12, 1, 4, 1, 2, 11, 10, 8, 1, 2, 8, 1, 2],
      [9, 6, 10, 8, 4, 1, 6, 10, 8, 4, 5, 4, 5, 4, 1, 2, 10, 12, 4, 2, 8, 2, 12, 2, 10],
      [12, 3, 10, 8, 3, 8, 1, 6, 10, 9, 3, 9, 5, 3, 8, 4, 4, 5, 3, 10, 8, 2, 0, 0, 2],
      [9, 6, 8, 4, 2, 10, 8, 5, 2, 10, 12, 0, 7, 10, 10, 13, 1, 3, 10, 8, 2, 8, 3, 12, 2],
      [12, 1, 2, 9, 6, 12, 4, 3, 10, 10, 11, 8, 3, 10, 10, 9, 2, 10, 10, 8, 6, 8, 6, 11, 10],
      [9, 2, 14, 8, 5, 3, 9, 6, 8, 4, 2, 8, 4, 4, 4, 6, 8, 2, 10, 12, 1, 2, 9, 0, 2],
      [10, 12, 3, 8, 1, 4, 4, 5, 2, 15, 10, 8, 3, 15, 15, 15, 8, 2, 12, 5, 2, 12, 4, 2, 10],
      [8, 5, 6, 8, 4, 1, 1, 7, 10, 15, 12, 6, 8, 5, 7, 15, 10, 12, 1, 3, 8, 3, 13, 0, 6],
      [12, 5, 3, 10, 13, 0, 4, 3, 10, 15, 15, 15, 10, 15, 15, 15, 8, 5, 6, 10, 10, 8, 1, 4, 3],
      [9, 1, 4, 4, 1, 2, 9, 4, 2, 9, 7, 15, 10, 15, 13, 5, 0, 1, 1, 4, 2, 12, 6, 11, 10],
      [10, 10, 9, 1, 2, 10, 12, 3, 8, 4, 3, 15, 10, 15, 15, 15, 8, 2, 8, 5, 6, 13, 5, 2, 10],
      [8, 4, 2, 10, 8, 6, 9, 2, 10, 9, 2, 11, 8, 5, 1, 7, 12, 4, 4, 5, 1, 5, 5, 2, 10],
      [8, 1, 6, 10, 12, 3, 8, 4, 4, 6, 8, 2, 8, 5, 2, 9, 3, 9, 1, 7, 4, 9, 5, 4, 2],
      [12, 4, 1, 6, 9, 2, 8, 5, 1, 3, 12, 4, 4, 3, 10, 8, 2, 8, 4, 5, 6, 12, 3, 11, 10],
      [9, 1, 4, 1, 6, 10, 10, 9, 2, 12, 3, 9, 3, 10, 8, 2, 8, 0, 1, 5, 5, 3, 10, 10, 10],
      [10, 8, 1, 2, 9, 2, 10, 10, 8, 1, 4, 6, 8, 2, 12, 6, 10, 8, 6, 9, 3, 12, 6, 10, 10],
      [10, 8, 4, 4, 2, 12, 6, 12, 2, 12, 1, 1, 6, 8, 5, 5, 2, 12, 1, 6, 10, 9, 5, 4, 2],
      [8, 6, 9, 5, 6, 9, 5, 1, 6, 9, 2, 12, 1, 4, 5, 5, 4, 1, 6, 9, 2, 8, 5, 5, 2],
      [12, 5, 4, 5, 5, 4, 5, 4, 5, 6, 12, 5, 4, 5, 5, 5, 5, 4, 5, 4, 4, 4, 5, 5, 6],
    ]
    maze.width = "25" # offset by one
    maze.height = "20" # offset by one
    maze.entry = "2,19"
    maze.exit = "23,0"
    maze.output_file = "test.txt"
    maze.perfect = "False"

    #generate(maze)
    solve(maze)
    mlx_renderer = GraphicalRenderer(maze, 60)
    render(maze, mlx_renderer)

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
