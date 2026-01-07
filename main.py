import sys
from .errors import Err, ParseError
from .parsing import parse
from .maze import Maze


def main(argc: int) -> int:
    maze = Maze()
    if argc < 2:
        return Err.INPUT_ERROR
    try:
        parse(maze, sys.argv[1])
    except ParseError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return Err.PARSE_ERROR
    return Err.NO_ERROR


if __name__ == "__main__":
    sys.exit(main(len(sys.argv)))
