from typing import Any, Iterator

from .maze import DIRECTIONS, CellFlag, Maze


def cell_data(
    maze: list[list[int]],
    e_x: int,
    e_y: int,
    x: int,
    y: int,
    step: int,
    parent: dict[str, Any] | None,
) -> dict:
    dist: int = abs(x - e_x) + abs(y - e_y)
    return {
        "x": x,
        "y": y,
        "cell": maze[y][x],
        "step": step,
        "dist": dist,
        "score": step + dist,
        "parent": parent,
    }


def solve(maze: Maze) -> Iterator[int]:
    brd: list[list[int]] = maze.map_data
    e_x, e_y = maze.exit
    i_x, i_y = maze.entry

    processing: list = []
    processed: set[tuple[int, int]] = set()
    path: dict[tuple[int, int], int] = {(i_x, i_y): 0}
    processing.append(cell_data(brd, e_x, e_y, i_x, i_y, 0, None))

    while processing:
        cur = processing.pop(
            min(range(len(processing)), key=lambda i: processing[i]["score"])
        )
        c_x: int = cur["x"]
        c_y: int = cur["y"]
        maze.set(c_x, c_y, CellFlag.SEEK)
        yield 1
        if cur["step"] != path.get((c_x, c_y), cur["step"]):
            continue
        processed.add((c_x, c_y))
        if c_x == e_x and c_y == e_y:
            break

        for flag, (d_x, d_y) in DIRECTIONS:
            n_x = c_x + d_x
            n_y = c_y + d_y
            if (not cur["cell"] & flag and
                    not maze.is_out_of_bounds(n_x, n_y) and
                (n_x, n_y) not in processed and
                ((n_x, n_y) not in path or
                 cur["step"] + 1 < path[(n_x, n_y)])):
                path[n_x, n_y] = cur["step"] + 1
                maze.set(n_x, n_y, CellFlag.SEEK_PREMIUM)
                yield 1
                processing.append(
                    cell_data(brd, e_x, e_y, n_x, n_y, cur["step"] + 1, cur)
                )

    while cur is not None:
        maze.set(cur["x"], cur["y"], CellFlag.PATH)
        cur = cur["parent"]
        yield 1
