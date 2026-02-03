import random
from typing import Any

from pydantic import BaseModel


class Palette(BaseModel):
    """
    This model stores RGBA colors for each maze element and tracks changes.

    Attributes:
        entry: RGBA color for the entry cell.
        exit: RGBA color for the exit cell.
        unreachable: RGBA color for unreachable cells.
        cursor: RGBA color for the generation cursor.
        seek: RGBA color for visited cells during solving.
        seek_premium: RGBA color for priority frontier cells.
        path: RGBA color for the final path cells.
        wall: RGBA color for walls.
        empty: RGBA color for empty background.
    """

    entry: int
    exit: int
    unreachable: int
    cursor: int
    seek: int
    seek_premium: int
    path: int
    wall: int
    empty: int
    idle_path: int

    _is_dirty: bool = True

    def __setattr__(self, name: str, value: Any) -> None:
        """
        This sets an attribute and marks the palette dirty on public changes.

        Args:
            name: Attribute name to assign.
            value: New attribute value.
        """
        super().__setattr__(name, value)

        if not name.startswith("_"):
            self._is_dirty = True

    def is_dirty(self) -> bool:
        """
        This returns True when the palette has changed since the last flush.

        Returns:
            True if the palette is dirty.
        """
        return self._is_dirty

    def flush(self) -> bool:
        """
        This returns the dirty state then resets it to clean.

        Returns:
            Previous dirty state.
        """
        is_dirty: bool = self._is_dirty
        self._is_dirty = False
        return is_dirty

    def randomize(self) -> None:
        """
        This randomizes all colors except empty.
        """
        for key in vars(self):
            if key != "empty":
                setattr(self, key, random_color())


class Rgba(BaseModel):
    """
    This model stores RGBA channels and converts between int and bytes.

    Attributes:
        r: Red channel value.
        g: Green channel value.
        b: Blue channel value.
        a: Alpha channel value.
    """

    r: int
    g: int
    b: int
    a: int

    def to_bytes(self) -> bytes:
        """
        This converts channels into BGRA byte order.

        Returns:
            A 4 byte BGRA sequence.
        """
        return bytes([self.b, self.g, self.r, self.a])

    @staticmethod
    def from_int(color: int) -> "Rgba":
        """
        This builds an RGBA object from a packed 0xRRGGBBAA integer.

        Args:
            color: Packed color integer.

        Returns:
            A new Rgba instance.
        """
        rgba = Rgba(
            a=color & 0xFF,
            r=(color >> 24) & 0xFF,
            g=(color >> 16) & 0xFF,
            b=(color >> 8) & 0xFF,
        )
        return rgba

    @staticmethod
    def bytes_from_int(color: int) -> bytes:
        """
        This converts a packed integer into BGRA bytes.

        Args:
            color: Packed color integer.

        Returns:
            A 4 byte BGRA sequence.
        """
        rgba = Rgba.from_int(color)
        return rgba.to_bytes()


def random_color() -> int:
    """
    This return a random bright packed 0xRRGGBBAA color with alpha set to 0xFF.

    Returns:
        A packed color integer.
    """
    color = 0
    color |= random.randint(0x55, 0xFF) << 24
    color |= random.randint(0x55, 0xFF) << 16
    color |= random.randint(0x55, 0xFF) << 8
    color |= 0xFF
    return color
