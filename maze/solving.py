from typing import Any, Iterator

from .maze import CellState, Maze, MazeArray, WallDescriptor


def cell_data(
    maze: MazeArray,
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
    brd: MazeArray = maze.array
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
        if not maze.get_cell(
                c_x,
                c_y,
        )["state"] & (CellState.ENTRY | CellState.EXIT):
            maze.set_state(c_x, c_y, CellState.SEEK)
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
                    not maze.is_out_of_bounds(n_x, n_y) and
                (n_x, n_y) not in processed and
                ((n_x, n_y) not in path or
                 cur["step"] + 1 < path[(n_x, n_y)])):
                path[n_x, n_y] = cur["step"] + 1
                if not maze.get_cell(
                        n_x,
                        n_y,
                )["state"] & (CellState.ENTRY | CellState.EXIT):
                    maze.set_state(n_x, n_y, CellState.SEEK_PREMIUM)
                yield 1
                processing.append(
                    cell_data(brd, e_x, e_y, n_x, n_y, cur["step"] + 1, cur)
                )

    while cur is not None:
        if not maze.get_cell(
                cur["x"],
                cur["y"],
        )["state"] & (CellState.ENTRY | CellState.EXIT):
            maze.set_state(cur["x"], cur["y"], CellState.PATH)
        cur = cur["parent"]
        yield 1
