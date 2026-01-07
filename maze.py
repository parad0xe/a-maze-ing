class Maze:

    def __init__(self) -> None:
        self._map: list[list[int]] | None = None
        self._width: int = 0
        self._height: int = 0
        self._entry: tuple[int, int] | None = None
        self._exit: tuple[int, int] | None = None
        self._output_file: str | None = None
        self._perfect: bool | None = None

    @map.setter
    def map(self, value: list[list[int]]) -> None:
        self._map = value

    # setters and getters
