import logging
import random
from enum import IntEnum
from typing import Annotated, Any, TypeAlias

import numpy as np
import numpy.typing as npt
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    SkipValidation,
    field_validator,
)

MIN_EDGE_SIZE: int = 1
MAX_EDGE_SIZE: int = 500

logger: logging.Logger = logging.getLogger(__name__)


class CellWall(IntEnum):
    NORTH = 1
    EAST = 1 << 1
    SOUTH = 1 << 2
    WEST = 1 << 3


class CellState(IntEnum):
    EMPTY = 0
    ENTRY = 1 << 4
    EXIT = 1 << 5
    UNREACHABLE = 1 << 6
    CURSOR = 1 << 7
    SEEK = 1 << 8
    PATH = 1 << 9
    SEEK_PREMIUM = 1 << 10


class WallDescriptor:
    walls: list[tuple[CellWall, tuple[int, int]]] = [
        (CellWall.NORTH, (0, -1)),
        (CellWall.SOUTH, (0, 1)),
        (CellWall.WEST, (-1, 0)),
        (CellWall.EAST, (1, 0)),
    ]

    opposites: dict[CellWall, tuple[CellWall, tuple[int, int]]] = {
        CellWall.NORTH: (CellWall.SOUTH, (0, -1)),
        CellWall.SOUTH: (CellWall.NORTH, (0, 1)),
        CellWall.WEST: (CellWall.EAST, (-1, 0)),
        CellWall.EAST: (CellWall.WEST, (1, 0)),
    }


MAZE_ARRAY_DT = np.dtype([("walls", np.int16), ("state", np.int16)])
MazeArray: TypeAlias = npt.NDArray[np.void]
Cell: TypeAlias = np.void


class Maze(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    width: int = Field(frozen=True, ge=MIN_EDGE_SIZE, le=MAX_EDGE_SIZE)
    height: int = Field(frozen=True, ge=MIN_EDGE_SIZE, le=MAX_EDGE_SIZE)
    entry: tuple[int, int]
    exit: tuple[int, int]
    perfect: bool
    output_file: str = Field(min_length=1)

    array: Annotated[MazeArray, SkipValidation] = Field(
        default_factory=lambda: np.zeros((0, 0), dtype=MAZE_ARRAY_DT)
    )

    _is_dirty: bool = PrivateAttr(default=True)

    def model_post_init(self, _: Any) -> None:
        if self.is_out_of_bounds(*self.entry):
            raise ValueError(
                f"Entry coordinates is out of bounds {self.entry}"
            )
        if self.is_out_of_bounds(*self.exit):
            raise ValueError(f"Exit coordinates is out of bounds {self.exit}")

        self.output_file = self.output_file.strip()

        logger.debug(
            f"Initialize map data with zeros ({self.width} x {self.height})"
        )
        self.array = np.zeros((self.height, self.width), dtype=MAZE_ARRAY_DT)
        self.initialize()

        if self.get_cell(*self.entry)["state"] & CellState.UNREACHABLE:
            raise ValueError("entry cannot be spawn on unreachable cell")
        if self.get_cell(*self.exit)["state"] & CellState.UNREACHABLE:
            raise ValueError("entry cannot be spawn on unreachable cell")

        logger.debug("Maze model intialized")

    def __setattr__(self, name, value: Any):
        if not name.startswith("_"):
            self._is_dirty = True
            if name == "entry":
                x, y = value
                if self.get_cell(x, y)["state"] & CellState.UNREACHABLE:
                    raise ValueError(
                        "entry cannot be spawn on unreachable cell"
                    )
                self.set_state(*self.entry, CellState.EMPTY)
                self.set_state(x, y, CellState.ENTRY)
            elif name == "exit":
                x, y = value
                if self.get_cell(x, y)["state"] & CellState.UNREACHABLE:
                    raise ValueError(
                        "exit cannot be spawn on unreachable cell"
                    )
                self.set_state(*self.exit, CellState.EMPTY)
                self.set_state(x, y, CellState.EXIT)
        super().__setattr__(name, value)

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def _parse_coordinates(cls, v: Any) -> tuple[int, int]:
        if isinstance(v, str):
            logger.debug("Parse string entry/exit coordinates")
            coords: list[int] = [int(p.strip()) for p in v.split(",")]
            if len(coords) != 2:
                raise ValueError(f"Invalid coordinate ({v})")
            return (coords[0], coords[1])
        return v

    def is_dirty(self) -> bool:
        return self._is_dirty

    def flush(self) -> bool:
        was_dirty: bool = self._is_dirty
        self._is_dirty = False
        return was_dirty

    def initialize(self) -> None:
        self.set(walls=0xF, state=0x0)
        self.display_life_answer()

    def random_entry_exit(self) -> None:
        while True:
            new_entry: tuple[int, int] = (
                random.randint(0, self.width - 1),
                random.randint(0, self.height - 1),
            )
            if not self.get_cell(*new_entry)["state"] & CellState.UNREACHABLE:
                break
        self.entry = new_entry
        while True:
            new_exit: tuple[int, int] = (
                random.randint(0, self.width - 1),
                random.randint(0, self.height - 1),
            )
            if not self.get_cell(*new_exit)["state"] & CellState.UNREACHABLE:
                break
        self.exit = new_exit

    def display_life_answer(self) -> None:
        # fmt: off
        answer = np.array([
            [1, 0, 0, 0, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [0, 0, 1, 0, 1, 0, 0],
            [0, 0, 1, 0, 1, 1, 1],
        ], dtype=np.int16) * CellState.UNREACHABLE
        # fmt: on

        sx: int = (self.width // 2) - (answer.shape[1] // 2)
        sy: int = (self.height // 2) - (answer.shape[0] // 2)
        ex: int = sx + answer.shape[1]
        ey: int = sy + answer.shape[0]

        if ex >= self.width or ey >= self.height:
            raise ValueError("maze is too small for display the life answer")

        self.array[sy:ey, sx:ex]["state"] |= answer

    def get_cell(self, x: int, y: int) -> Cell:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        return self.array[y][x]

    def mask(self, walls: int | None = None, state: int | None = None) -> None:
        if walls is not None:
            walls, _ = self._demux(walls)
            self.array["walls"] &= walls
        if state is not None:
            _, state = self._demux(state)
            self.array["state"] &= state

    def set(
        self,
        walls: int | None = None,
        state: int | None = None,
    ) -> None:
        if state is not None:
            _, state = self._demux(state)
            self.array["state"] = state
        if walls is not None:
            walls, _ = self._demux(walls)
            self.array["walls"] = walls

    def unset(
        self,
        walls: int | None = None,
        state: int | None = None,
    ) -> None:
        if state is not None:
            _, state = self._demux(state)
            self.array["state"] &= ~state
        if walls is not None:
            walls, _ = self._demux(walls)
            self.array["walls"] &= ~walls

    def set_walls(self, x: int, y: int, walls: int) -> None:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        walls, _ = self._demux(walls)
        if self._apply_walls(x, y, walls, on=True):
            self._sync_neighbours(x, y, walls, on=True)

    def unset_walls(self, x: int, y: int, walls: int) -> None:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        walls, _ = self._demux(walls)
        if self._apply_walls(x, y, walls, on=False):
            self._sync_neighbours(x, y, walls, on=False)

    def set_state(self, x: int, y: int, state: int) -> None:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        _, state = self._demux(state)
        self.array[y][x]["state"] = state

    def has_walls(
        self, x: int, y: int, walls: int, strict: bool = True
    ) -> bool:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        if strict:
            return bool(self.array[y][x]["walls"] & walls)
        else:
            mask = self.array[y][x]["walls"] | ~walls
            return bool(((self.array[y][x]["walls"] | ~walls) ^ mask) | walls)

    def is_out_of_bounds(self, x: int, y: int) -> bool:
        return x < 0 or y < 0 or x >= self.width or y >= self.height

    def _apply_walls(self, x: int, y: int, walls: int, on: bool) -> bool:
        last: int = self.array[y][x]["walls"]
        if on:
            self.array[y][x]["walls"] |= walls
        else:
            self.array[y][x]["walls"] &= ~walls
        if last != self.array[y][x]["walls"]:
            self._is_dirty = True
            return True
        return False

    def _sync_neighbours(self, x: int, y: int, walls: int, on: bool) -> None:
        for wall in WallDescriptor.opposites:
            if not wall & walls:
                continue
            opposite_wall, (dx, dy) = WallDescriptor.opposites[wall]
            nx = x + dx
            ny = y + dy
            if not self.is_out_of_bounds(nx, ny):
                self._apply_walls(nx, ny, opposite_wall, on=on)

    def _demux(self, flags: int) -> tuple[int, int]:
        walls = flags & 0xF
        state = flags & ~0xF
        return (walls, state)
