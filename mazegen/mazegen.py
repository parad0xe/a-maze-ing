# standard modules
import logging
import random
from enum import IntEnum
from typing import Annotated, Any, Iterator, TypeAlias, cast

# extern modules
import numpy as np
import numpy.typing as npt
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SkipValidation,
    field_validator,
)

# logger config
logger: logging.Logger = logging.getLogger(__name__)

# defines
MIN_EDGE_SIZE: int = 1
MAX_EDGE_SIZE: int = 50

MAZE_ARRAY_DT = np.dtype([("walls", np.int16), ("state", np.int16)])
MazeArray: TypeAlias = npt.NDArray[np.void]
Cell: TypeAlias = np.void


# enums
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


# main class
class Maze(BaseModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    width: int = Field(frozen=True, ge=MIN_EDGE_SIZE, le=MAX_EDGE_SIZE)
    height: int = Field(frozen=True, ge=MIN_EDGE_SIZE, le=MAX_EDGE_SIZE)
    entry: tuple[int, int]
    exit: tuple[int, int]
    perfect: bool
    shortest_path: list[str] = Field(default_factory=list)
    seed: int | None = None

    output_file: str = Field(min_length=1)

    array: Annotated[MazeArray, SkipValidation] = Field(
        default_factory=lambda: np.zeros((0, 0), dtype=MAZE_ARRAY_DT)
    )

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

    def __setattr__(self, name: str, value: Any) -> None:
        if not name.startswith("_"):
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
    def _parse_coordinates(cls, v: Any) -> tuple[int, int] | Any:
        if isinstance(v, str):
            logger.debug("Parse string entry/exit coordinates")
            coords: list[int] = [int(p.strip()) for p in v.split(",")]
            if len(coords) != 2:
                raise ValueError(f"Invalid coordinate ({v})")
            return (coords[0], coords[1])
        return v

    def initialize(self) -> None:
        self.set(walls=0xF, state=0x0)
        self.display_42()

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
            if (not self.get_cell(*new_exit)["state"] & CellState.UNREACHABLE
                    and new_exit != new_entry):
                break
        self.exit = new_exit

    def display_42(self) -> None:
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

        self.array[sy:ey, sx:ex]["state"] = answer

    def get_cell(self, x: int, y: int) -> Cell:
        if self.is_out_of_bounds(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        return cast(Cell, self.array[y][x])

    def mask(self, walls: int | None = None, state: int | None = None) -> None:
        if walls is not None:
            walls, _ = self._demux(walls)
            self.array["walls"] &= walls
        if state is not None:
            _, state = self._demux(state)
            self.array["state"] &= state

    def set(self, walls: int | None = None, state: int | None = None) -> None:
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

    def export(self) -> None:
        logger.debug("Generating file")
        with open(self.output_file, "w", encoding="utf-8") as f:
            i_x, i_y, e_x, e_y = (*self.entry, *self.exit)
            h, w = self.height, self.width
            shortest_path: str = "".join(reversed(self.shortest_path))
            for y in range(h):
                f.write(
                    "".join(
                        format(int(self.array[y, x]["walls"]), "X")
                        for x in range(w)
                    )
                )
                f.write("\n")
            f.write("\n")
            f.write(f"{i_x},{i_y}\n")
            f.write(f"{e_x},{e_y}\n")
            f.write(f"{shortest_path}")

    # solve
    def iter_solve(self) -> Iterator[int]:
        def cell_data(
            x: int, y: int, step: int, parent: dict[str, Any] | None
        ) -> dict[str, Any]:
            dist = abs(x - e_x) + abs(y - e_y)
            return {
                "x": x,
                "y": y,
                "cell": brd[y][x],
                "step": step,
                "dist": dist,
                "score": step + dist,
                "parent": parent,
            }

        brd: MazeArray = self.array
        e_x, e_y = self.exit
        i_x, i_y = self.entry

        processing: list[dict[str, Any]] = []
        processed: set[tuple[int, int]] = set()
        path: dict[tuple[int, int], int] = {(i_x, i_y): 0}
        processing.append(cell_data(i_x, i_y, 0, None))

        while processing:
            cur = processing.pop(
                min(
                    range(len(processing)),
                    key=lambda i: processing[i]["score"],
                )
            )
            c_x: int = cur["x"]
            c_y: int = cur["y"]
            if not self.get_cell(
                    c_x,
                    c_y,
            )["state"] & (CellState.ENTRY | CellState.EXIT):
                self.set_state(c_x, c_y, CellState.SEEK)
            yield 1
            if cur["step"] != path.get((c_x, c_y), cur["step"]):
                continue
            processed.add((c_x, c_y))
            if c_x == e_x and c_y == e_y:
                break

            for flag, (d_x, d_y) in WallDescriptor.walls:
                n_x = c_x + d_x
                n_y = c_y + d_y
                if (not cur["cell"]["walls"] & flag and
                        not self.is_out_of_bounds(n_x, n_y) and
                    (n_x, n_y) not in processed and
                    ((n_x, n_y) not in path or
                     cur["step"] + 1 < path[(n_x, n_y)])):
                    path[n_x, n_y] = cur["step"] + 1
                    if not self.get_cell(
                            n_x,
                            n_y,
                    )["state"] & (CellState.ENTRY | CellState.EXIT):
                        self.set_state(n_x, n_y, CellState.SEEK_PREMIUM)
                    yield 1
                    processing.append(
                        cell_data(n_x, n_y, cur["step"] + 1, cur)
                    )

        self.unset(state=(CellState.SEEK | CellState.SEEK_PREMIUM))
        yield 1

        self.shortest_path.clear()
        while cur is not None:
            parent = cur["parent"]
            if parent is not None:
                dx = cur["x"] - parent["x"]
                dy = cur["y"] - parent["y"]

                if dx == 1 and dy == 0:
                    self.shortest_path.append("E")
                elif dx == -1 and dy == 0:
                    self.shortest_path.append("W")
                elif dx == 0 and dy == 1:
                    self.shortest_path.append("S")
                elif dx == 0 and dy == -1:
                    self.shortest_path.append("N")

            if not self.get_cell(cur["x"], cur["y"])["state"] & (
                    CellState.ENTRY | CellState.EXIT):
                self.set_state(cur["x"], cur["y"], CellState.PATH)
            cur = parent
            yield 1

    def solve(self) -> None:
        for _ in self.iter_solve():
            pass

    # generation
    def iter_generate(self) -> Iterator[int]:
        viewed: list[tuple[int, int]] = []
        path: list[tuple[int, int]] = [(0, 0)]
        turn: int = 0
        last_by_prob: bool = False

        if self.perfect:
            viewed.append((0, 0))

        while True:
            turn += 1
            if len(path) == 0:
                break
            cx, cy = path[-1]
            self.set_state(cx, cy, CellState.CURSOR)
            yield 1
            added = False
            random_walls = WallDescriptor.walls.copy()
            random.shuffle(random_walls)
            prob: float = random.random()
            prob_ok: bool = False
            for wall, (dx, dy) in random_walls:
                nx = cx + dx
                ny = cy + dy
                if not self.is_out_of_bounds(nx, ny):
                    next_cell = self.get_cell(nx, ny)
                    if (not self.perfect and turn % 10 == 0 and prob < 0.5 and
                            not last_by_prob):
                        prob_ok = True
                    else:
                        last_by_prob = False
                    if next_cell["state"] != CellState.UNREACHABLE and (
                            prob_ok or (nx, ny) not in viewed):
                        if (nx, ny) in viewed:
                            last_by_prob = True
                        self.unset_walls(cx, cy, wall)
                        viewed.append((nx, ny))
                        path.append((nx, ny))
                        added = True
                        break
            self.set_state(cx, cy, CellState.EMPTY)
            if not added:
                path.pop(-1)
        self.set_state(*self.entry, CellState.ENTRY)
        self.set_state(*self.exit, CellState.EXIT)
        yield 1

    def generate(self) -> None:
        for _ in self.iter_generate():
            pass
