from typing import Protocol

from .maze import Maze
"""
examples:

render(TerminalRenderer, maze)
render(GraphicalRenderer, maze)
"""


class Renderer(Protocol):

    def render(self) -> None:
        ...


class TerminalRenderer:

    def render(self) -> None:
        raise NotImplementedError("terminal render method not implemented")


class GraphicalRenderer:

    def render(self) -> None:
        raise NotImplementedError("graphical render method not implemented")


def render(maze: Maze, renderer: type[Renderer]) -> None:
    raise NotImplementedError("render method not implemented")
