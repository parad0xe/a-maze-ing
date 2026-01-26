import logging
import random
from typing import Iterator

from .maze import CellState, Maze, WallDescriptor

logger: logging.Logger = logging.getLogger(__name__)


def generate(maze: Maze) -> Iterator[int]:
    viewed: list[tuple[int, int]] = []
    path: list[tuple[int, int]] = [(0, 0)]
    turn: int = 0
    last_by_prob: bool = False

    if maze.perfect:
        viewed.append((0, 0))

    while True:
        turn += 1
        if len(path) == 0:
            break
        cx, cy = path[-1]
        maze.set_state(cx, cy, CellState.CURSOR)
        yield 1
        added = False
        random_walls = WallDescriptor.walls.copy()
        random.shuffle(random_walls)
        prob: float = random.random()
        prob_ok: bool = False
        for wall, (dx, dy) in random_walls:
            nx = cx + dx
            ny = cy + dy
            if not maze.is_out_of_bounds(nx, ny):
                next_cell = maze.get_cell(nx, ny)
                if (not maze.perfect and turn % 10 == 0 and prob < 0.5 and
                        not last_by_prob):
                    prob_ok = True
                else:
                    last_by_prob = False
                if next_cell["state"] != CellState.UNREACHABLE and (
                        prob_ok or (nx, ny) not in viewed):
                    if (nx, ny) in viewed:
                        last_by_prob = True
                    maze.unset_walls(cx, cy, wall)
                    viewed.append((nx, ny))
                    path.append((nx, ny))
                    added = True
                    break
        maze.set_state(cx, cy, CellState.EMPTY)
        if not added:
            path.pop(-1)
    maze.set_state(*maze.entry, CellState.ENTRY)
    maze.set_state(*maze.exit, CellState.EXIT)
    yield 1
