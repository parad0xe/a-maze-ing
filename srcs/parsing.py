from .maze import Maze
from .errors import ParseError, SetterError


KEYS: set[str] = {
        "width",
        "height",
        "entry",
        "exit",
        "output_file",
        "perfect"
        }


def is_valid_pos(maze: Maze, pos: tuple[int, int]) -> bool:
    x, y = pos
    if not 0 <= y < maze.height:
        return False
    if not 0 <= x < maze.width:
        return False


def parse(maze: Maze, input_file: str) -> None:
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if not key:
                raise ParseError("invalid key: cannot be empty")
            if not value:
                raise ParseError("invalid value: cannot be empty")
            if key in KEYS:
                try:
                    setattr(maze, key, value)
                except SetterError as e:
                    raise ParseError(f"invalid value: {e}")
            else:
                raise ParseError("invalid key")
        if not is_valid_pos(maze, maze.entry):
            raise ParseError("invalid entry")
        if not is_valid_pos(maze, maze.exit):
            raise ParseError("invalid exit")
