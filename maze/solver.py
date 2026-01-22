from .maze import Maze
from enum import IntEnum
from typing import Any


class Cell(IntEnum):
    NORTH = (1 << 0)
    EAST = (1 << 1)
    SOUTH = (1 << 2)
    WEST = (1 << 3)
    CURSOR = (1 << 4)
    SEEK = (1 << 5)
    PATH = (1 << 6)


def compute_cell(
        maze: list[list[int]],
        e_x: int,
        e_y: int,
        x: int,
        y: int,
        step: int,
        parent: dict[str, Any] | None
) -> dict:
    dist: int = abs(x - e_x) + abs(y - e_y)
    return {
        'x': x,
        'y': y,
        'cell': maze[y][x],
        'step': step,
        'dist': dist,
        'score': step + dist,
        'parent': parent
    }


def solve(maze: Maze) -> None:
    brd: list[list[int]] = maze.map
    processed: set[tuple[int, int]] = set()
    processing: list = []
    e_x, e_y = maze.exit
    i_x, i_y = maze.entry
    best_step: dict[tuple[int, int], int] = {(i_x, i_y): 0}
    processing.append(
        compute_cell(
            brd, e_x, e_y, i_x, i_y, 0, None
        )
    )
    while processing:
        cur = processing.pop(
            min(range(len(processing)), key=lambda i: processing[i]['score'])
        )
        c_x: int = cur['x']
        c_y: int = cur['y']
        if cur['step'] != best_step.get((c_x, c_y), cur['step']):
            continue
        processed.add((c_x, c_y))
        if c_x == e_x and c_y == e_y:
            break
        if (
            not cur['cell'] & Cell.NORTH
            and c_y > 0
            and ((c_x, c_y - 1) not in best_step
            or cur['step'] + 1 < best_step[(c_x, c_y - 1)])
        ):
            best_step[c_x, c_y - 1] = cur['step'] + 1
            processing.append(
                compute_cell(
                    brd, e_x, e_y, c_x, c_y - 1, cur['step'] + 1, cur
                )
            )
        if (
            not cur['cell'] & Cell.EAST
            and c_x < maze.width - 1
            and ((c_x + 1, c_y) not in best_step
            or cur['step'] + 1 < best_step[(c_x + 1, c_y)])
        ):
            best_step[c_x + 1, c_y] = cur['step'] + 1
            processing.append(
                compute_cell(
                    brd, e_x, e_y, c_x + 1, c_y, cur['step'] + 1, cur
                )
            )
        if (
            not cur['cell'] & Cell.SOUTH
            and c_y < maze.height - 1
            and ((c_x, c_y + 1) not in best_step
            or cur['step'] + 1 < best_step[(c_x, c_y + 1)])
        ):
            best_step[c_x, c_y + 1] = cur['step'] + 1
            processing.append(
                compute_cell(
                    brd, e_x, e_y, c_x, c_y + 1, cur['step'] + 1, cur
                )
            )
        if (
            not cur['cell'] & Cell.WEST
            and c_x > 0
            and ((c_x - 1, c_y) not in best_step
            or cur['step'] + 1 < best_step[(c_x - 1, c_y)])
        ):
            best_step[c_x - 1, c_y] = cur['step'] + 1
            processing.append(
            processing.append(
                compute_cell(
                    brd, e_x, e_y, c_x - 1, c_y, cur['step'] + 1, cur
                )
            )

    while cur is not None:
        brd[cur['y']][cur['x']] |= Cell.PATH
        cur = cur['parent']
