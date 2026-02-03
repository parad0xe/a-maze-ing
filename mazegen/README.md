_This project has been created as part of the 42 curriculum by nlallema and ldecavel_

### DEPENDENCIES
- numpy  
- pydantic  

### STRUCTURE
The module contains a main class called **_Maze_**. The main methods you may use
in your project are :  
- ``Maze.export()``  
- ``Maze.generate()`` 
- ``Maze.solve()``  
- ``Maze.initialize()``

To get an empty maze, you simply need to instantiate a ``Maze()`` and Pydantic will automatically
fill the numpy table with closed walls. You then only need to call ``Maze.generate()`` to build walls,
and then ``Maze.solve()`` to get the shortest path from the entry to the exit. If you want to get a
formatted output with the maze specs, you can use ``Maze.export()``. To clear the current maze, 
you can use ``Maze.initialize()``. It will automatically display 42 in the center.

To create a ``Maze()`` instance, you can pass it these attributes :
- **width** (int between 1 and 50)  
- **height** (int between 1 and 50)  
- **entry** (tuple[int, int] in maze boundaries)  
- **exit** (tuple[int, int] in maze boundaries)  
- **perfect** (bool)
- **seed** (int | None)
Any invalid attribute will raise a **_ValidationError_**.  

After you called the ``Maze.solve()`` method, your maze's **shortest_path** attribute (list[str])
will contain the shortest path between the entry and the exit. Finally, your maze's **array** attribute
is the concrete maze (list[int16, int16]) handled by numpy.

### ADVANCED FEATURE

If you need to interract more precisely with the tiles of the maze, the helper classes (mostly enums):
**Cell**, **CellWall**, **CellState**, **WallDescriptor** helps doing bitwise operations on the tiles 
without knowing by heart each bit. For example you can use ``CellState.EXIT`` to do an ``&`` operation
and know if the tile is the exit tile or not.
