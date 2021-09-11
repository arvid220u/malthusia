

class CommonRobot:
    """
    All functions that can be called by all robots.
    """

    def __init__(self, game, robot):
        self.game = game
        self.robot = robot

    def get_type(self):
        return self.robot.type

    def get_last_memory_usage(self):
        return self.robot.runner.last_memory_usage,

    def get_bytecode(self):
        return self.robot.runner.bytecode,
