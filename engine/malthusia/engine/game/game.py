import random
from .robot import Robot
from .team import Team
from .robottype import RobotType
from .constants import GameConstants
from ..container.runner import RobotRunner
from .commonrobot import CommonRobot
from .wanderer import Wanderer


class Game:

    def __init__(self, seed=GameConstants.DEFAULT_SEED, debug=False, colored_logs=True):
        random.seed(seed)

        self.debug = debug
        self.colored_logs = colored_logs
        self.running = True

        self.robot_count = 0
        self.queue = {}
        self.dead_robots = []

        self.map = Map()

        self.round = 0

        self.board_states = []

        if self.debug:
            self.log_info(f'Seed: {seed}')

    def turn(self):
        if self.running:
            self.round += 1

            if self.debug:
                self.log_info(f'Turn {self.round}')
                self.log_info(f'Queue: {self.queue}')

            for i in range(self.robot_count):
                if i in self.queue:
                    robot = self.queue[i]
                    robot.turn()

                    if not robot.alive:
                        self.delete_robot(i)
                    self.check_over()

            if self.running:
                self.board_states.append([row[:] for row in self.board])
        else:
            raise GameError('game is over')

    def delete_robot(self, i):
        robot = self.queue[i]
        self.board[robot.row][robot.col] = None
        robot.kill()
        del self.queue[i]
        self.dead_robots.append(robot)

    def serialize(self):
        def serialize_robot(robot):
            if robot is None:
                return None

            return {'id': robot.id, 'team': robot.team, 'health': robot.health, 'logs': robot.logs[:]}

        return [[serialize_robot(c) for c in r] for r in self.board]

    def log_info(self, msg):
        if self.colored_logs:
            print(f'\u001b[32m[Game info] {msg}\u001b[0m')
        else:
            print(f'[Game info] {msg}')

    def new_robot(self, row, col, team, robot_type):
        # TODO: another way of getting ID?
        id = self.robot_count
        robot = Robot(row, col, team, id, robot_type)

        methods = {
            'GameError': GameError,
            'RobotType': RobotType,
            'RobotError': RobotError,
            'GameConstants': GameConstants,
            'Team': Team,
        }

        def wrap_methods(modelrobot):
            methods = {}
            for method in [m for m in dir(modelrobot) if callable(getattr(modelrobot, m))]:
                def this_method(*args):
                    RobotRunner.validate_arguments(*args, error_type=RobotRunner)
                    return getattr(modelrobot, method)(*args)
                methods[method] = this_method
            return methods

        methods.update(wrap_methods(CommonRobot(self, robot)))

        if robot_type == RobotType.WANDERER:
            methods.update(Wanderer(self, robot))
        else:
            raise NotImplementedError

        robot.animate(self.code[team.value], methods, debug=self.debug)

        self.queue[self.robot_count] = robot
        self.board[row][col] = robot

        self.robot_count += 1

class RobotError(Exception):
    """Raised for illegal robot inputs"""
    pass


class GameError(Exception):
    """Raised for errors that arise within the Game"""
    pass
