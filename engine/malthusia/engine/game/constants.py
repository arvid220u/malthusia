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
    CHICKPEA_FN = lambda old : old + 20 - (old % 10)