import random
from typing import Any

from pydantic import BaseModel


class Palette(BaseModel):
    entry: int
    exit: int
    unreachable: int
    cursor: int
    seek: int
    seek_premium: int
    path: int
    wall: int
    empty: int

    _is_dirty = True

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)

        if not name.startswith("_"):
            self._is_dirty = True

    def is_dirty(self) -> bool:
        return self._is_dirty

    def flush(self) -> bool:
        is_dirty: bool = self._is_dirty
        self._is_dirty = False
        return is_dirty


class Rgba(BaseModel):
    r: int
    g: int
    b: int
    a: int

    def to_bytes(self) -> bytes:
        return bytes([self.b, self.g, self.r, self.a])

    @staticmethod
    def from_int(color: int) -> "Rgba":
        rgba = Rgba(
            a=color & 0xFF,
            r=(color >> 24) & 0xFF,
            g=(color >> 16) & 0xFF,
            b=(color >> 8) & 0xFF,
        )
        return rgba

    @staticmethod
    def bytes_from_int(color: int) -> bytes:
        rgba = Rgba.from_int(color)
        return rgba.to_bytes()


def random_color() -> int:
    color = 0
    color |= random.randint(0x55, 0xFF) << 24
    color |= random.randint(0x55, 0xFF) << 16
    color |= random.randint(0x55, 0xFF) << 8
    color |= 0xFF
    return color
