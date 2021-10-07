# Malthusia

_Join the world of autonomous robots._

Version: 0.0.1.

# Overview

Malthusia is a grid-based world of water and islands. It is inhabited by no humans, and, initially, no one else either. One day, however, robot wanderers start appearing, each controlled by its own tiny computer program. Soon, robot landscapers follow. Now you can create your own wanderer or landscaper!

# Game Mechanics

## Turns

Each round is broken down into sequential turns, one for each robot.
In the order they were spawned, each robot may sense its surroundings and then optionally take an action.

## Chickpeas

Wanderers and landscapers need chickpeas to survive. Both have a health level, decreasing by 1 every turn. By eating chickpeas, the robots can bring their health level back up. One chickpea brings the health level to the next multiple of 10, and then adds 10 more. Then, 1 health point is subtracted, as usual. For example, the following table illustrates the health level at the end of turn 1 and at the end of turn 2, given that the robot eats a chickpea in turn 2.

Turn 1 health | Turn 2 health
-------------- | ----
-1 | dead :(
0 | 19
1 | 19
2 | 19
3 | 19
4 | 19
5 | 19
6 | 19
7 | 19
8 | 19
9 | 19
10 | 29
11 | 29
etc | etc

# Robot Limits

## Bytecode

Robots are also very limited in the amount of computation they are allowed to perform per **turn**.
**Bytecodes** are a convenient measure of computation in languages like Python,
where one bytecode corresponds roughly to one operation,
and a single line of code generally contains several bytecodes.
Because bytecodes are a feature of the compiled code itself, the same program will always compile to the same bytecodes and thus take the same amount of computation on the same inputs.
This is great, because it allows us to avoid using _time_ as a measure of computation, which leads to problems such as nondeterminism.

Every round each robot sequentially takes its turn, by running the `turn()` function defined in every robot code. If a robot attempts to exceed its bytecode limit (usually unexpectedly, if you have too big of a loop or something), it will throw an error. The next turn, `turn()` will be called anew as normal.

The bytecode remaining at the end of the turn is added to the limit for the next turn. Every robot gets 20K bytecode per turn, up to 50K max.

Robots can get their current bytecode with `get_bytecode()`. This is the amount of bytecode the robots have remaining for the turn.

## Memory

Robots are limited to 10 KB in memory persisted between turns. Robots can get the number of bytes used at the end of the previous turn with `get_last_memory_usage()`.

# API Reference

Below is a quick reference of all methods available to robots. Make sure not to define your own functions with the same name as an API method, since that would overwrite the API method.

#### Shared methods

All robots will have these:

- `log()`: to print anything out, e.g. for debugging. Python's `print` will NOT work.
- `get_bytecode()`: returns the number of bytecodes left.
- `get_last_memory_usage()`: returns the number of bytes used at the end of the last turn
- `get_type()`: returns the `RobotType` of the robot

#### Wanderer methods

- `check_location(x, y)`: returns a `LocationInfo` object, or throws a `RobotError` if outside the vision range
- `get_location()`: returns a `(x, y)` tuple of the robot's location.
- `move(direction)`: moves one step in the specified direction (which is of type `Direction`), but it can only climb at most 10 units of elevation up (and fall any elevation down)

#### Landscaper methods

- all of the Wanderer's methods, plus
- `dig(x, y)`: digs 1 unit of dirt from the specified location, or throws a `RobotError` if not a neighboring location or the elevation difference is too big
- `place(x, y)`: places 1 unit of dirt at the specified location, or throws a `RobotError` if not a neighboring location, the elevation difference is too big, or the robot does not hold enough dirt in stock

# Known Limitations and Bugs

The Malthusia engine is a work in progress. Please report any weird behavior or bugs by submitting an issue in the [malthusia repo](https://github.com/arvid220u/malthusia/issues).

If you are able to escape the sandbox and get into our servers, please send us an email at [arvid@mit.edu](mailto:arvid@mit.edu) — do not post it publicly on GitHub, please.

# Changelog

- 0.0.1 (8/30/21)