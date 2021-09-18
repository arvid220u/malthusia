import logging

from .location import InternalLocation, Location
from .direction import Direction
from .robot import RobotError
from .robottype import RobotType
from .constants import GameConstants

logger = logging.getLogger(__name__)


class Wanderer:
    """
    This class contains all functions that can be called by a wanderer.
    """

    def __init__(self, game, robot):
        self.game = game
        self.robot = robot

    def check_location(self, x, y) -> Location:
        if (x-self.robot.x)**2 + (y-self.robot.y)**2 > GameConstants.VISION_RADIUS[RobotType.WANDERER]**2:
            raise RobotError(f"this location is outside the robot's vision radius of {GameConstants.VISION_RADIUS[RobotType.WANDERER]}")
        return self.game.map.get_location(x, y).to_public()

    def get_location(self) -> (int, int):
        x, y = self.robot.x, self.robot.y
        if self.game.map.get_location(x, y).robot != self.robot:
            raise RobotError('something went wrong; please contact the devs')
        return x, y

    def move(self, direction: Direction):
        if self.robot.has_moved:
            raise RobotError('this unit has already moved this turn; robots can only move once per turn')

        x, y = self.robot.x, self.robot.y
        old_loc: InternalLocation = self.game.map.get_location(x, y)

        if old_loc.robot != self.robot:
            raise RobotError('something went wrong; please contact the devs')

        new_x, new_y = [v1 + v2 for v1, v2 in zip((x, y), direction.value)]
        new_loc: InternalLocation = self.game.map.get_location(new_x, new_y)

        if new_loc.robot is not None:
            raise RobotError('you cannot move to a space that is already occupied')

        self.robot.x = new_x
        self.robot.y = new_y

        self.game.map.update_location(new_loc.x, new_loc.y, robot=self.robot)
        self.game.map.update_location(old_loc.x, old_loc.y, robot=None)

        self.robot.has_moved = True
