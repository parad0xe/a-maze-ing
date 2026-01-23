import logging
import os
import random
import sys

from maze import Maze
from maze.engine import (
    CellFlag,
    EngineConfig,
    GraphicalEngine,
    Palette,
    UpdateCallback,
    UpdateCallbackParams,
)
from maze.error import ErrCode

logger = logging.getLogger(__name__)


def menu() -> tuple[UpdateCallback, dict]:
    def update(params: UpdateCallbackParams) -> None:
        (context, maze, config, switch) = params
        print("menu")
        config.palette.border = random.choice([0xFF0000FF, 0x00FFFFFF])
        input("enter to swtich")
        switch("generator")

    return (update, {})


def generator() -> tuple[UpdateCallback, dict]:
    def update(params: UpdateCallbackParams) -> None:
        (context, maze, config, switch) = params

        active = context["active"]
        neighbours_iter = maze.iter_neighbours(active[0], active[1])
        next_cell = random.choice(list(neighbours_iter))
        maze.unset(active[0], active[1], CellFlag.CURSOR)
        maze.set(active[0], active[1], CellFlag.PATH)
        maze.set(next_cell[0], next_cell[1], CellFlag.CURSOR)
        context["active"] = next_cell

        print(context["iter"])
        if context["iter"] == 200:
            switch("menu")
        else:
            context["iter"] += 1

    return (update, {"active": (0, 0), "iter": 0})


def solver() -> tuple[UpdateCallback, dict]:
    def update(params: UpdateCallbackParams) -> None:
        pass

    return (update, {})


def main(argc: int, argv: list[str]) -> int:
    if argc < 2:
        logger.error(
            f"Usage: python3 {os.path.basename(__file__)} <config_file>"
        )
        return ErrCode.INPUT_ERROR

    # try:
    #    maze: Maze = load(argv[1])
    # except ParseError as e:
    #    logger.error(f"parse error: {e}")
    #    return ErrCode.PARSE_ERROR

    # fmt: off
    maze = Maze.model_validate({
        "map_data": [
          [9, 5, 1, 5, 3, 9, 1, 5, 3, 9, 5, 5, 1, 7, 9, 5, 1, 5, 1, 1, 5, 1, 1, 5, 3],
          [14, 11, 10, 11, 10, 14, 8, 1, 2, 8, 5, 3, 12, 1, 4, 1, 2, 11, 10, 8, 1, 2, 8, 1, 2],
          [9, 6, 10, 8, 4, 1, 6, 10, 8, 4, 5, 4, 5, 4, 1, 2, 10, 12, 4, 2, 8, 2, 12, 2, 10],
          [12, 3, 10, 8, 3, 8, 1, 6, 10, 9, 3, 9, 5, 3, 8, 4, 4, 5, 3, 10, 8, 2, 0, 0, 2],
          [9, 6, 8, 4, 2, 10, 8, 5, 2, 10, 12, 0, 7, 10, 10, 13, 1, 3, 10, 8, 2, 8, 3, 12, 2],
          [12, 1, 2, 9, 6, 12, 4, 3, 10, 10, 11, 8, 3, 10, 10, 9, 2, 10, 10, 8, 6, 8, 6, 11, 10],
          [9, 2, 14, 8, 5, 3, 9, 6, 8, 4, 2, 8, 4, 4, 4, 6, 8, 2, 10, 12, 1, 2, 9, 0, 2],
          [10, 12, 3, 8, 1, 4, 4, 5, 2, 143, 10, 8, 3, 143, 143, 143, 8, 2, 12, 5, 2, 12, 4, 2, 10],
          [8, 5, 6, 8, 4, 1, 1, 7, 10, 143, 12, 6, 8, 5, 7, 143, 10, 12, 1, 3, 8, 3, 13, 0, 6],
          [12, 5, 3, 10, 13, 0, 4, 3, 10, 143, 143, 143, 10, 143, 143, 143, 8, 5, 6, 10, 10, 8, 1, 4, 3],
          [9, 1, 4, 4, 1, 2, 9, 4, 2, 9, 7, 143, 10, 143, 13, 5, 0, 1, 1, 4, 2, 12, 6, 11, 10],
          [10, 10, 9, 1, 2, 10, 12, 3, 8, 4, 3, 143, 10, 143, 143, 143, 8, 2, 8, 5, 6, 13, 5, 2, 10],
          [8, 4, 2, 10, 8, 6, 9, 2, 10, 9, 2, 11, 8, 5, 1, 7, 12, 4, 4, 5, 1, 5, 5, 2, 10],
          [8, 1, 6, 10, 12, 3, 8, 4, 4, 6, 8, 2, 8, 5, 2, 9, 3, 9, 1, 7, 4, 9, 5, 4, 2],
          [12, 4, 1, 6, 9, 2, 8, 5, 1, 3, 12, 4, 4, 3, 10, 8, 2, 8, 4, 5, 6, 12, 3, 11, 10],
          [9, 1, 4, 1, 6, 10, 10, 9, 2, 12, 3, 9, 3, 10, 8, 2, 8, 0, 1, 5, 5, 3, 10, 10, 10],
          [10, 8, 1, 2, 9, 2, 10, 10, 8, 1, 4, 6, 8, 2, 12, 6, 10, 8, 6, 9, 3, 12, 6, 10, 10],
          [10, 8, 4, 4, 2, 12, 6, 12, 2, 12, 1, 1, 6, 8, 5, 5, 2, 12, 1, 6, 10, 9, 5, 4, 2],
          [8, 6, 9, 5, 6, 9, 5, 1, 6, 9, 2, 12, 1, 4, 5, 5, 4, 1, 6, 9, 2, 8, 5, 5, 2],
          [12, 5, 4, 5, 5, 4, 5, 4, 5, 6, 12, 5, 4, 5, 5, 5, 5, 4, 5, 4, 4, 4, 5, 5, 6],
        ],
        "width": "25",
        "height": "20",
        "entry": "1,1",
        "exit": "19,14",
        "output_file": "test.txt",
        "perfect": "False"
    })
    # fmt: on

    engine = GraphicalEngine(
        maze=maze,
        config=EngineConfig(
            border_size=1,
            cell_size=30,
            space_size=0,
            palette=Palette(
                border=0x0000AAFF,
                unreachable=0xAAAAAAFF,
                cursor=0x00FF00FF,
                path=0x00FF0055,
                default=0x000000FF,
            ),
        ),
        loops={
            "menu": menu,
            "generator": generator,
            "solver": solver,
        },
    )
    engine.loop("generator")
    return ErrCode.NO_ERROR


if __name__ == "__main__":
    status: int = main(len(sys.argv), sys.argv)
    sys.exit(status)
