
from malthusia.stubs import *

# This is an example bot written by the developers!
# Use this to help write your own code, or run it against your bot to see how well you can do!

def turn():
    """
    MUST be defined for robot to run
    This function will be called at the beginning of every turn and should contain the bulk of your robot commands
    """
    mem = get_last_memory_usage()
    log(f"last memory usage: {mem}")
    bytecode = get_bytecode()
    log(f"bytecode remaining: {bytecode}")
