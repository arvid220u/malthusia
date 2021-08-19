# Malthusia

_Join the world of autonomous robots._
The rules may change slightly, but there will never be any breaking changes. Current version: 0.0.1

# Overview

Malthusia is a grid-based 2D world. It is inhabited by no humans, and, initially, no one else either. One day, however, cows start appearing, each controlled by its own tiny computer program. Now you can create your own cow!

# Game Mechanics

## Turns

Each round is broken down into sequential turns, one for each cow.
In the order they were spawned, each cow may sense its surroundings and then optionally take an action.

# Bytecode Limits

Robots are also very limited in the amount of computation they are allowed to perform per **turn**.
**Bytecodes** are a convenient measure of computation in languages like Python,
where one bytecode corresponds roughly to one operation,
and a single line of code generally contains several bytecodes.
Because bytecodes are a feature of the compiled code itself, the same program will always compile to the same bytecodes and thus take the same amount of computation on the same inputs.
This is great, because it allows us to avoid using _time_ as a measure of computation, which leads to problems such as nondeterminism.

Every round each robot sequentially takes its turn.
If a robot attempts to exceed its bytecode limit (usually unexpectedly, if you have too big of a loop or something),
its computation will be paused and then resumed at exactly that point next turn.
The code will resume running just fine, but this can cause problems if, for example, you check if a tile is empty, then the robot is cut off and the others take their turns, and then you attempt to move into a now-occupied tile.
Instead, simply return from the `turn()` function to end your turn.
This will pause computation where you choose, and resume on the next line next turn.

The per-turn bytecode limits for various robots are as follows:
- Cow: 20000 per turn

Robots can get their current bytecode with `get_bytecode()`. This is the amount of bytecode the robots have remaining for the turn.

# API Reference

Below is a quick reference of all methods available to robots. Make sure not to define your own functions with the same name as an API method, since that would overwrite the API method.

#### Cow methods

- `log()`: to print anything out, e.g. for debugging. Python's `print` will NOT work.
- `get_bytecode()`: returns the number of bytecodes left.
- `check_location(x, y)`: returns a `LocationInfo` object, or throws a `RobotError` if outside the vision range
- `get_location()`: returns a `(x, y)` typle of the robot's location.
- `move(direction)`: moves one step in the specified direction (which is of type `Direction`)

# Known Limitations and Bugs

The Malthusia engine is a work in progress. Please report any weird behavior or bugs by submitting an issue in the [malthusia repo](https://github.com/arvid220u/malthusia/issues).

If you are able to escape the sandbox and get into our servers, please send us an email at [arvid@mit.edu](mailto:arvid@mit.edu) — do not post it publicly on GitHub, please.

# Changelog

- 0.0.1 (8/19/21)