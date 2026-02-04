_This project has been created as part of the 42 curriculum by nlallema and ldecavel_

### DEPENDENCIES
- numpy  
- pydantic  

### STRUCTURE
The module contains a main class called **_Maze_**. The main methods you may use
in your project are :  
- [Maze.export()](mazegen.py#L274)  
- [Maze.generate()](mazegen.py#L435) 
- [Maze.solve()](mazegen.py#L383)  
- [Maze.initialize()](mazegen.py#L137)

To get an empty maze, you simply need to instantiate a ``Maze()`` with appropriate attributes, and Pydantic will automatically
fill the numpy table with closed walls. You then only need to call ``Maze.generate()`` to build walls,
and then ``Maze.solve()`` to get the shortest path from the entry to the exit. If you want to get a
formatted output with the maze specs, you can use ``Maze.export()``. To clear the current maze, 
you can use ``Maze.initialize()``. It will automatically turn on all walls and display 42 in the center.

To create a ``Maze()`` instance, you can pass it these attributes :
- **width** (int between 1 and 150)  
- **height** (int between 1 and 150)  
- **entry** (tuple[int, int] in maze boundaries)  
- **exit** (tuple[int, int] in maze boundaries)  
- **perfect** (bool)
- **seed** (int | None)
Seed is optional, default to None. Any invalid attribute will raise a **_ValidationError_**.  

After you called the ``Maze.solve()`` method, your maze's **shortest_path** attribute (list[str])
will contain the shortest path between the entry and the exit. Finally, your maze's **array** attribute
is the concrete maze (list[int16, int16]) handled by numpy.

### ADVANCED FEATURE

If you need to interract more precisely with the tiles of the maze, the helper classes (mostly enums):
**Cell**, **CellWall**, **CellState**, **WallDescriptor** helps doing bitwise operations on the tiles 
without knowing by heart each bit. For example you can use ``CellState.EXIT`` to do an ``&`` operation
and know if the tile is the exit tile or not.

There is also a set of helper methods to interact with maze cells:
- [Maze.get_cell()](mazegen.py#L181)
- [Maze.mask()](mazegen.py#L186)
- [Maze.set()](mazegen.py#L194)
- [Maze.unset()](mazegen.py#L202)
- [Maze.set_walls()](mazegen.py#L214)
- [Maze.unset_walls()](mazegen.py#L221)
- [Maze.set_state()](mazegen.py#L228)
- [Maze.has_walls()](mazegen.py#L234)
- [Maze.is_out_of_bounds()](mazegen.py#L245)  
 

> [!NOTE]
> if you need more precise informations about methods signatures or usage,
> please read the docstrings in the [**mazegen.py**](mazegen.py) file.


