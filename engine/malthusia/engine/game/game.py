import random
import logging
import base64
import json

from .robot import Robot, RobotError
from .robottype import RobotType
from .constants import GameConstants
from ..container.runner import RobotRunner
from .commonrobot import CommonRobot
from .wanderer import Wanderer
from .map import Map
from ..container.code_container import CodeContainer
from .direction import Direction
from .location import LocationInfo

logger = logging.getLogger(__name__)


def new_uid():
    return base64.b64encode(random.randbytes(64)).decode("utf-8")


class Game:

    def __init__(self, action_file, map_file=GameConstants.STARTING_MAPFILE, seed=GameConstants.DEFAULT_SEED,
                 debug=False, colored_logs=True, round_callback=None):
        random.seed(seed)

        self.action_file = action_file
        self.action_file_offset = 0
        self.deferred_actions = {}

        self.debug = debug
        self.colored_logs = colored_logs

        self.queue = []  # invariant: all alive robots are here; there may be newly killed robots here too
        self.dead_robots = []  # invariant: all robots here are dead; all dead robots are here

        self.map = Map.from_file(map_file)

        self.round = 0

        self.round_callback = round_callback

        if self.debug:
            self.log_info(f'Seed: {seed}')

    def check_actions(self):
        with open(self.action_file, "r") as f:
            f.seek(self.action_file_offset)
            for l in f.readlines():
                action = json.loads(l)
                self.process_action(action)
            self.action_file_offset = f.tell()
        self.process_actions()

    def process_action(self, action):
        if "type" not in action:
            raise GameError(f"Action object does not have a type attribute: {action}")
        if "round" not in action or type(action["round"]) is not int:
            raise GameError(f"Action object does not have a valid round attribute: {action}")
        if action["round"] < self.round:
            # if this happens we are screwed
            raise GameError(
                f"We received action from the past. This is not good. We need to rerun everything. Action: {action}")
        if action["round"] not in self.deferred_actions:
            self.deferred_actions[action["round"]] = []
        self.deferred_actions[action["round"]].append(action)

    def process_actions(self):
        if self.round not in self.deferred_actions:
            return
        for action in self.deferred_actions[self.round]:
            if action["type"] == "new_robot":
                # TODO: add some kind of error handling here
                code = CodeContainer.from_dirfile(action["code"])
                robot_type = RobotType(action["robot_type"])
                self.new_robot(action["creator"], code, robot_type, action["uid"])
            else:
                raise GameError(f"Action object type attribute is unintelligible: {action}")
        del self.deferred_actions[self.round]

    def turn(self):
        self.round += 1

        self.check_actions()

        if self.debug:
            self.log_info(f'Turn {self.round}')
            self.log_info(f'Queue: {self.queue}')

        # invariants: we never remove from the queue while iterating here;
        #             we may add to the end (robot spawn other robot), which is why we are not using iterators
        i = 0
        while i < len(self.queue):
            robot = self.queue[i]
            # this robot may have been killed
            if robot.alive:
                robot.turn()
            i += 1

        # invariant: we never change the queue while iterating here
        newqueue = []
        for robot in self.queue:
            if robot.alive:
                newqueue.append(robot)
        self.queue = newqueue

        if self.round_callback is not None:
            self.round_callback(self.serialize_round())

    def serialize_round(self):
        return {
            "round": self.round,
            "map": self.map.serialize(),
        }

    def log_info(self, msg):
        if self.colored_logs:
            print(f'\u001b[32m[Game info] {msg}\u001b[0m')
        else:
            print(f'[Game info] {msg}')

    def new_robot_xy(self):
        # generate a random location in [-100,100]x[-100,100], making sure the location is free
        sz = 100
        max_tries = sz * sz * 5
        i = 0
        while i < max_tries:
            x, y = random.randint(-sz, sz), random.randint(-sz, sz)
            if self.map.spawnable(x, y):
                return x, y
            i += 1
        raise GameError(f"Cannot spawn robot; no spawnable location found after {max_tries} tries.")

    def new_robot(self, creator: str, code: CodeContainer, robot_type: RobotType, uid: str):
        x, y = self.new_robot_xy()

        def kill_robot_callback(robot):
            assert not robot.alive
            self.map.remove_robot(robot)
            self.dead_robots.append(robot)

        robot = Robot(x, y, uid, creator, robot_type, kill_robot_callback)

        methods = {
            'GameError': GameError,
            'RobotType': RobotType,
            'RobotError': RobotError,
            'GameConstants': GameConstants,
            'Direction': Direction,
            'LocationInfo': LocationInfo,
        }

        logger.debug(methods)

        def wrapper_method(modelrobot, method, *args):
            logger.debug(method)
            RobotRunner.validate_arguments(*args, error_type=RobotRunner)
            return getattr(modelrobot, method)(*args)

        def wrap_methods(modelrobot):
            wrapped_methods = {}
            for method in [m for m in dir(modelrobot) if callable(getattr(modelrobot, m)) and not m.startswith("_")]:
                logger.debug(method)
                logger.debug(type(method))
                wrapped_methods[method] = (
                    lambda modelrobot, method: lambda *args: wrapper_method(modelrobot, method, *args))(modelrobot,
                                                                                                        method)
            logger.debug(wrapped_methods)
            return wrapped_methods

        methods.update(wrap_methods(CommonRobot(self, robot)))
        logger.debug(methods)

        if robot_type == RobotType.WANDERER:
            methods.update(wrap_methods(Wanderer(self, robot)))
        else:
            raise NotImplementedError

        logger.debug(methods)

        robot.animate(code, methods, debug=self.debug)

        self.queue.append(robot)
        self.map.add_robot(robot, x, y)


class GameError(Exception):
    """Raised for errors that arise within the Game"""
    pass
