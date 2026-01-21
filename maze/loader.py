from .error import ParseError, SetterError
from .maze import KEYS, Maze


def is_valid_pos(maze: Maze, pos: tuple[int, int]) -> bool:
    x, y = pos
    if not 0 <= y < maze.height:
        return False
    if not 0 <= x < maze.width:
        return False
    return True


def load(input_file: str) -> Maze:
    try:
        maze: Maze = Maze()
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("#"):
                    continue
                if "=" not in line:
                    raise ParseError("invalid file format")
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
            if not maze.entry or not is_valid_pos(maze, maze.entry):
                raise ParseError("invalid entry")
            if not maze.exit or not is_valid_pos(maze, maze.exit):
                raise ParseError("invalid exit")
        return maze
    except FileNotFoundError:
        raise ParseError(f"config file '{input_file}' not found")
    except OSError as e:
        raise ParseError(f"error when opening config file '{input_file}': {e}")
