class GameConstants:

    # the maximum number of rounds, until the winner is decided by a coinflip
    MAX_ROUNDS = 500

    # the board size
    BOARD_SIZE = 16

    # the default seed
    DEFAULT_SEED = 1337

    # the bytecode added per turn
    BYTECODE_PER_TURN = 20_000

    # the max bytecode available
    MAX_BYTECODE = 100_000

    # the memory limit in bytes on inter-turn stored memory (e.g. globals)
    MEMORY_LIMIT = 2 ** 20