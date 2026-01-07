import sys

from errors import Err, ParseError
from parsing import parse
from maze import Maze
from generator import maze_generator
from solver import solve


def main(argc: int) -> int:
    maze = Maze()
    if argc < 2:
        return Err.INPUT_ERROR
    try:
        parse(maze, sys.argv[1])
    except ParseError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return Err.PARSE_ERROR
    maze_generator(maze)
    solve(maze)
    #  print function
    while True:
        command = input(
            """=== A-Maze-Ing ===
            [r] Re-generate a new maze
            [s] Show/Hide path from entry to exit
            [c] Rotate maze colors
            [q] Quit
            Choice ? [r/s/c/q]: """
        ).strip().lower()
        match command:
            case "r":
                maze_generator(maze)
                solve(maze)
                #  clean function
                #  print function
            case "s":
                solve(maze)
            case "c":
                pass  # rotate maze colors
            case "q":
                return
            case "" | _:
                continue
    return Err.NO_ERROR


if __name__ == "__main__":
    sys.exit(main(len(sys.argv)))
