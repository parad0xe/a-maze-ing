from .maze import Maze
from .errors import ParseError, SetterError


def parse(maze: Maze, input_file: str) -> None:
    with open("r", input_file) as f:
        for line in f:
            if line.strip().startswith("#"):
                continue
            key, value = line.split("=")
            key = key.lower()
            if hasattr(maze, key):
                try:
                    setattr(maze, key, value)
                except SetterError as e:
                    raise ParseError(f"invalid value: {e}")
            else:
                raise ParseError("invalid key")
