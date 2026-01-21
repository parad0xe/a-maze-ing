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
