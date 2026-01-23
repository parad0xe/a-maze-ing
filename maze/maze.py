from enum import IntEnum
from typing import Any, Iterator

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    ValidationInfo,
    field_validator,
    model_validator,
)

MINIMUM_EDGE_SIZE: int = 1
MAXIMUM_EDGE_SIZE: int = 500


class CellFlag(IntEnum):
    NORTH = 1
    EAST = 1 << 1
    SOUTH = 1 << 2
    WEST = 1 << 3
    ENTRY = 1 << 4
    EXIT = 1 << 5
    UNREACHABLE = 1 << 6
    CURSOR = 1 << 7
    SEEK = 1 << 8
    PATH = 1 << 9
    SEEK_PREMIUM = 1 << 10


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
    model_config = ConfigDict(extra="forbid")

    width: int = Field(frozen=True, ge=MINIMUM_EDGE_SIZE, le=MAXIMUM_EDGE_SIZE)
    height: int = Field(
        frozen=True, ge=MINIMUM_EDGE_SIZE, le=MAXIMUM_EDGE_SIZE
    )
    map_data: list[list[int]] = []
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str = Field(frozen=True, min_length=1)
    perfect: bool = Field(frozen=True)
    hide_path: bool = Field(default=False)
    _is_dirty: bool = PrivateAttr(default=True)

    def __setattr__(self, name, value: Any):
        if not name.startswith("_"):
            self._is_dirty = True
            if name == "entry":
                x, y = value
                self.unset(*self.entry, CellFlag.ENTRY)
                self.set(x, y, CellFlag.ENTRY)
            elif name == "exit":
                x, y = value
                self.unset(*self.exit, CellFlag.EXIT)
                self.set(x, y, CellFlag.EXIT)
        super().__setattr__(name, value)

    def flush(self) -> bool:
        was_dirty: bool = self._is_dirty
        self._is_dirty = False
        return was_dirty

    @model_validator(mode="after")
    def _initialize_grid(self) -> "Maze":
        if not self.map_data:
            self.map_data = np.zeros((self.height, self.width),
                                     dtype=np.int32).tolist()

        return self

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def _parse_coordinates(cls, v: Any,
                           info: ValidationInfo) -> tuple[int, int]:
        if isinstance(v, str):
            coords: list[int] = [int(p.strip()) for p in v.split(",")]
            if len(coords) != 2:
                raise ValueError(f"Invalid coordinate ({v})")
            width, height = (info.data["width"], info.data["height"])
            x, y = coords
            if x < 0 or y < 0 or x >= width or y >= height:
                raise ValueError(f"Coordinates is out of bounds ({coords})")
            return (coords[0], coords[1])
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

    def clear(self) -> None:
        self.map_data = np.zeros((self.height, self.width),
                                 dtype=np.int32).tolist()

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
