from enum import IntEnum
from typing import Any, Iterator

from pydantic import BaseModel, Field, PrivateAttr, field_validator

MINIMUM_EDGE_SIZE: int = 1
MAXIMUM_EDGE_SIZE: int = 500

KEYS: set[str] = {  # keys = main.slots ou juste utiliser slots
    "width",
    "height",
    "entry",
    "exit",
    "output_file",
    "perfect",
}


class CellFlag(IntEnum):
    NORTH = 1
    EAST = 1 << 1
    SOUTH = 1 << 2
    WEST = 1 << 3
    CURSOR = 1 << 4
    SEEK = 1 << 5
    PATH = 1 << 6
    UNREACHABLE = 1 << 7


DIRECTIONS: list[tuple[CellFlag, tuple[int, int]]] = [
    (CellFlag.NORTH, (0, -1)),
    (CellFlag.SOUTH, (0, 1)),
    (CellFlag.WEST, (-1, 0)),
    (CellFlag.EAST, (1, 0)),
]

OPPOSITES: dict[int, tuple[CellFlag, tuple[int, int]]] = {
    CellFlag.NORTH: (CellFlag.SOUTH, (0, -1)),
    CellFlag.SOUTH: (CellFlag.NORTH, (0, 1)),
    CellFlag.WEST: (CellFlag.EAST, (-1, 0)),
    CellFlag.EAST: (CellFlag.WEST, (1, 0)),
}


class Maze(BaseModel):
    width: int = Field(frozen=True, ge=MINIMUM_EDGE_SIZE, le=MAXIMUM_EDGE_SIZE)
    height: int = Field(
        frozen=True, ge=MINIMUM_EDGE_SIZE, le=MAXIMUM_EDGE_SIZE
    )
    map_data: list[list[int]] = Field(frozen=True)
    entry: tuple[int, int] = Field(frozen=True)
    exit: tuple[int, int] = Field(frozen=True)
    output_file: str = Field(frozen=True, min_length=1)
    perfect: bool = Field(frozen=True)
    _is_dirty: bool = PrivateAttr(default=True)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)

        if not name.startswith("_"):
            self._is_dirty = True

    def flush(self) -> bool:
        was_dirty: bool = self._is_dirty
        self._is_dirty = False
        return was_dirty

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def _parse_coordinates(cls, v: Any) -> tuple[int, int]:
        if isinstance(v, str):
            try:
                coords: list[int] = [int(p.strip()) for p in v.split(",")]
                if len(coords) != 2:
                    raise ValueError(f"invalid coordinate ({v})")
                return (coords[0], coords[1])
            except ValueError:
                raise ValueError(f"invalid coordinate format: ({v})")
        return v

    @field_validator("output_file", mode="before")
    @classmethod
    def _strip_string(cls, v: Any) -> str:
        return v.strip() if isinstance(v, str) else v

    def get_cell(self, x: int, y: int) -> int:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        return self.map_data[y][x]

    def set(self, x: int, y: int, flag: int) -> None:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        if not self.has_flag(x, y, flag):
            self._apply_flag_state(x, y, flag, on=True)
            self._sync_neighbours(x, y, flag, on=True)

    def unset(self, x: int, y: int, flag: int) -> None:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        if self.has_flag(x, y, flag):
            self._apply_flag_state(x, y, flag, on=False)
            self._sync_neighbours(x, y, flag, on=False)

    def iter_neighbours(self, x: int, y: int) -> Iterator[tuple[int, int]]:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")

        for flag, (dx, dy) in DIRECTIONS:
            if not self.has_flag(x, y, flag):
                nx = x + dx
                ny = y + dy
                if not self.is_out_of_bounds(nx, ny):
                    yield (nx, ny)

    def has_flag(self, x: int, y: int, flag: int) -> bool:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        return bool(self.map_data[y][x] & flag)

    def is_out_of_bounds(self, x: int, y: int) -> bool:
        return x < 0 or y < 0 or x >= self.width or y >= self.height

    def _apply_flag_state(self, x: int, y: int, flag: int, on: bool) -> None:
        if on:
            self.map_data[y][x] |= flag
        else:
            self.map_data[y][x] &= ~flag
        self._is_dirty = True

    def _sync_neighbours(self, x: int, y: int, flag: int, on: bool) -> None:
        if flag not in OPPOSITES:
            return

        flag_to_set, (dx, dy) = OPPOSITES[flag]

        nx = x + dx
        ny = y + dy
        if not self.is_out_of_bounds(nx, ny):
            self._apply_flag_state(nx, ny, flag_to_set, on=on)
