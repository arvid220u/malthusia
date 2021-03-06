import os

from .robottype import RobotType

class GameConstants:

    # the default seed
    DEFAULT_SEED = 1337

    # the bytecode added per turn
    BYTECODE_PER_TURN = 20_000

    # the max bytecode available
    MAX_BYTECODE = 50_000

    # the memory limit in bytes on inter-turn stored memory (e.g. globals)
    MEMORY_LIMIT = 10 * (2 ** 10) # 10 KB

    # the probability that a chickpea will spawn in a given location at a given round
    CHICKPEA_SPAWN_DENSITY = 1/100
    # the function that transforms old health into new health given a chickpea
    CHICKPEA_FN = lambda old: old + 20 - (old % 10)
    # the maximum health a robot can have
    MAX_HEALTH = 100
    # the start health
    START_HEALTH = 100

    MOVE_ELEVATION_THRESHOLD = 10

    # the default elevation, outside specified map locations
    DEFAULT_ELEVATION = -10

    STARTING_MAPFILE = os.path.join(os.path.dirname(__file__), "maps/Hatchery.json")

    # a robot can see all locations within a euclidean distance of their vision radius (<=)
    VISION_RADIUS = {
        RobotType.WANDERER: 5
    }