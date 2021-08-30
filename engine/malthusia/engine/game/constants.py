class GameConstants:

    # the default seed
    DEFAULT_SEED = 1337

    # the bytecode added per turn
    BYTECODE_PER_TURN = 20_000

    # the max bytecode available
    MAX_BYTECODE = 50_000

    # the memory limit in bytes on inter-turn stored memory (e.g. globals)
    MEMORY_LIMIT = 10 * (2 ** 10) # 10 KB