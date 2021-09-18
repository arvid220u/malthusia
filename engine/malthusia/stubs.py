from typing import List, Optional, Tuple, Union

from .engine import RobotType, RobotError, GameError, GameConstants, Location, Direction


# The stubs in this file make it possible for editors to auto-complete the global methods
# They can be imported using "from battlehack20.stubs import *"
# This import is preprocessed away before instrumenting the code

# The dummy implementations in this file exist so that editors won't give warnings like
# "Assigning result of a function call, where the function has no return"


def log(msg: str) -> None:
    """
    Type-agnostic method.

    Logs a message.
    """
    log(msg)


def get_bytecode() -> int:
    """
    Type-agnostic method.

    Returns the number of bytecodes left.
    """
    return get_bytecode()


def get_last_memory_usage() -> int:
    """
    Type-agnostic method.

    Returns the memory usage in bytes at the end of the previous round.
    """
    return get_last_memory_usage()


def get_type() -> RobotType:
    """
    Type-agnostic method.

    Returns the robot’s type, either `RobotType.OVERLORD` or `RobotType.PAWN`.
    """
    return get_type()


def get_location() -> Location:
    return get_location()


def move(direction: Direction):
    return move(direction)
