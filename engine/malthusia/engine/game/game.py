import random
import base64

from .robot import Robot
from .robottype import RobotType
from .constants import GameConstants
from ..container.runner import RobotRunner
from .commonrobot import CommonRobot
from .wanderer import Wanderer
from .map import Map
from ..container.code_container import CodeContainer


def new_uid():
    return base64.b64encode(random.randbytes(64)).decode("utf-8")


class Game:

    def __init__(self, map_file=GameConstants.STARTING_MAPFILE, seed=GameConstants.DEFAULT_SEED, debug=False, colored_logs=True):
        random.seed(seed)

        self.debug = debug
        self.colored_logs = colored_logs

        self.robot_count = 0
        self.queue = {}
        self.dead_robots = []

        self.map = Map.from_file(map_file)

        self.round = 0

        self.map_states = []

        if self.debug:
            self.log_info(f'Seed: {seed}')

    def turn(self):
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

        self.map_states.append(self.map.serialize())

    def delete_robot(self, i):
        robot = self.queue[i]
        self.map.delete_robot(robot)
        robot.kill()
        del self.queue[i]
        self.dead_robots.append(robot)

    def log_info(self, msg):
        if self.colored_logs:
            print(f'\u001b[32m[Game info] {msg}\u001b[0m')
        else:
            print(f'[Game info] {msg}')

    def new_robot_xy(self):
        # generate a random location in [-100,100]x[-100,100], making sure the location is free
        sz = 100
        max_tries = sz*sz*5
        i = 0
        while i < max_tries:
            x, y = random.randint(-sz, sz), random.randint(-sz, sz)
            if self.map.spawnable(x, y):
                return x, y
            i += 1
        raise GameError(f"Cannot spawn robot; no spawnable location found after {max_tries} tries.")

    def new_robot(self, creator: str, code: CodeContainer, robot_type: RobotType):
        uid = new_uid()
        x, y = self.new_robot_xy()
        robot = Robot(x, y, uid, creator, robot_type)

        methods = {
            'GameError': GameError,
            'RobotType': RobotType,
            'RobotError': RobotError,
            'GameConstants': GameConstants,
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
            methods.update(wrap_methods(Wanderer(self, robot)))
        else:
            raise NotImplementedError

        robot.animate(code, methods, debug=self.debug)

        self.queue[self.robot_count] = robot
        self.map.add_robot(robot, x, y)

        self.robot_count += 1


class RobotError(Exception):
    """Raised for illegal robot inputs"""
    pass


class GameError(Exception):
    """Raised for errors that arise within the Game"""
    pass
