from typing import Any

import mazegen
from src.errors import ParseError


def load(input_file: str) -> mazegen.Maze:
    """
    This loads a key value config file and builds a Maze from it.

    Args:
        input_file: Path to the configuration file to read.

    Returns:
        A validated Maze instance built from the parsed values.

    Raises:
        ParseError: The file contains invalid lines or empty keys or values.
        FileNotFoundError: The input file does not exist.
        OSError: An OS level error occurred while reading the file.
        ValidationError: The parsed values dont satisfy Maze validation rules.
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
