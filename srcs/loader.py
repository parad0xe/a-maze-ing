import mazegen
from typing import Any


class ParseError(Exception):
    pass


def load(input_file: str) -> mazegen.Maze:
    """
    [TODO:description]

    Args:
        input_file: [TODO:description]

    Returns:
        [TODO:description]

    Raises:
        ParseError: [TODO:description]
        FileNotFoundError: [TODO:description]
        OSError: [TODO:description]
        ValidationError: [TODO:description]
    """
    values: dict[str, Any] = {}
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("#"):
                continue
            if "=" not in line:
                raise ParseError("Invalid file format")
            key, value = line.split("=", 1)
            key = key.strip().lower()
            value = value.strip()
            if not key:
                raise ParseError("Key cannot be empty")
            if not value:
                raise ParseError("Value cannot be empty")
            values[key] = value
    return mazegen.Maze(**values)
