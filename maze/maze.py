from enum import IntEnum

from .error import SetterError

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


# !! USE PYDANTIC !!
# class Maze(BaseModel): ...


class Maze:

    def __init__(self) -> None:
        self._map: list[list[int]] | None = None
        self._width: int = 0
        self._height: int = 0
        self._entry: tuple[int, int] | None = None
        self._exit: tuple[int, int] | None = None
        self._output_file: str | None = None
        self._perfect: bool | None = None
        self._is_dirty: bool = True
        self.active: tuple[int, int] = (0, 0)

    @property
    def map(self) -> list[list[int]] | None:
        return self._map

    @map.setter
    def map(self, value: list[list[int]]) -> None:
        self._map = value

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, value: str) -> None:
        try:
            width: int = int(value)
            if not MINIMUM_EDGE_SIZE <= width <= MAXIMUM_EDGE_SIZE:
                raise SetterError(f"invalid width: {value}")
            self._width = width
        except ValueError:
            raise SetterError(f"invalid width: {value}")

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, value: str) -> None:
        try:
            height: int = int(value)
            if not MINIMUM_EDGE_SIZE <= height <= MAXIMUM_EDGE_SIZE:
                raise SetterError(f"invalid height: {value}")
            self._height = height
        except ValueError:
            raise SetterError(f"invalid height: {value}")

    @property
    def entry(self) -> tuple[int, int] | None:
        return self._entry

    @entry.setter
    def entry(self, value: str) -> None:
        try:
            pos: list[int] = list(map(int, value.split(",")))
            if len(pos) != 2:
                raise SetterError(f"invalid entry: {value}")
            x, y = pos
            self._entry = (x, y)
        except ValueError:
            raise SetterError(f"invalid entry: {value}")

    @property
    def exit(self) -> tuple[int, int] | None:
        return self._exit

    @exit.setter
    def exit(self, value: str) -> None:
        try:
            pos: list[int] = list(map(int, value.split(",")))
            if len(pos) != 2:
                raise SetterError(f"invalid entry: {value}")
            x, y = pos
            self._exit = (x, y)
        except ValueError:
            raise SetterError(f"invalid exit: {value}")

    @property
    def output_file(self) -> str | None:
        return self._output_file

    @output_file.setter
    def output_file(self, value: str) -> None:
        v = value.strip()
        if not v:
            raise SetterError("invalid output_file: cannot be empty")
        self._output_file = v

    @property
    def perfect(self) -> bool | None:
        return self._perfect

    @perfect.setter
    def perfect(self, value: str) -> None:
        if value == "True":
            self._perfect = True
        elif value == "False":
            self._perfect = False
        else:
            raise SetterError(f"invalid perfect: {value}")

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value: bool) -> None:
        self._is_dirty = value

    def set(self, x: int, y: int, flag: int) -> None:
        if self.out_of_bound(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        if not self.map:
            raise ValueError("map is not set")
        if not self.has_flag(x, y, flag):
            self.map[y][x] |= flag
            self._synchronize_neighborgh(x, y)
            self._is_dirty = True

    def unset(self, x: int, y: int, flag: int) -> None:
        if self.out_of_bound(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        if not self.map:
            raise ValueError("map is not set")
        if self.has_flag(x, y, flag):
            self.map[y][x] &= ~flag
            self._synchronize_neighborgh(x, y)
            self._is_dirty = True

    def neighbourgh(self, x: int, y: int) -> list[tuple[int, int]]:
        if self.out_of_bound(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        if not self.map:
            raise ValueError("map is not set")

        neighbourgh: list[tuple[int, int]] = []

        if not self.has_flag(x, y, CellFlag.EAST) and not self.out_of_bound(
                x + 1, y):
            neighbourgh.append((x + 1, y))
        if not self.has_flag(x, y, CellFlag.SOUTH) and not self.out_of_bound(
                x, y + 1):
            neighbourgh.append((x, y + 1))
        if not self.has_flag(x, y, CellFlag.WEST) and not self.out_of_bound(
                x - 1, y):
            neighbourgh.append((x - 1, y))
        if not self.has_flag(x, y, CellFlag.NORTH) and not self.out_of_bound(
                x, y - 1):
            neighbourgh.append((x, y - 1))
        return neighbourgh

    def has_flag(self, x: int, y: int, flag: int) -> bool:
        if self.out_of_bound(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        if not self.map:
            raise ValueError("map is not set")
        return bool(self.map[y][x] & flag)

    def out_of_bound(self, x: int, y: int) -> bool:
        return x < 0 or y < 0 or x >= self.width or y >= self.height

    def _synchronize_neighborgh(self, x: int, y: int):
        if self.out_of_bound(x, y):
            raise ValueError(f"out of bound ({x}, {y})")
        if not self.map:
            raise ValueError("map is not set")

        if not self.out_of_bound(x + 1, y):
            if not self.has_flag(x, y, CellFlag.EAST):
                self.unset(x + 1, y, CellFlag.WEST)
            else:
                self.set(x + 1, y, CellFlag.WEST)

        if not self.out_of_bound(x - 1, y):
            if not self.has_flag(x, y, CellFlag.WEST):
                self.unset(x - 1, y, CellFlag.EAST)
            else:
                self.set(x - 1, y, CellFlag.EAST)

        if not self.out_of_bound(x, y - 1):
            if not self.has_flag(x, y, CellFlag.NORTH):
                self.unset(x, y - 1, CellFlag.SOUTH)
            else:
                self.set(x, y - 1, CellFlag.SOUTH)

        if not self.out_of_bound(x, y + 1):
            if not self.has_flag(x, y, CellFlag.SOUTH):
                self.unset(x, y + 1, CellFlag.NORTH)
            else:
                self.set(x, y + 1, CellFlag.NORTH)
