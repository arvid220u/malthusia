import logging

from .location import InternalLocation, LocationInfo
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

    def check_location(self, x, y) -> LocationInfo:
        if (x-self.robot.x)**2 + (y-self.robot.y)**2 > GameConstants.VISION_RADIUS[RobotType.WANDERER]**2:
            raise RobotError(f"Out of vision radius: attempted to check location {(x, y)}, which is a distance {((x-self.robot.x)**2 + (y-self.robot.y)**2)**.5} away from the robot's location of {(self.robot.x, self.robot.y)}. The robot's vision radius is {GameConstants.VISION_RADIUS[RobotType.WANDERER]}.")
        return self.game.map.get_location(x, y).to_location_info()

    def get_location(self) -> (int, int):
        x, y = self.robot.x, self.robot.y
        if self.game.map.get_location(x, y).robot != self.robot:
            raise RobotError("Something went wrong; please contact the devs!")
        return x, y

    def move(self, direction: Direction):
        if self.robot.has_moved:
            raise RobotError("Already moved: this unit has already moved this turn, and robots can only move once per turn.")

        x, y = self.robot.x, self.robot.y
        old_loc: InternalLocation = self.game.map.get_location(x, y)

        if old_loc.robot != self.robot:
            raise RobotError("Something went wrong; please contact the devs!")

        new_x, new_y = [v1 + v2 for v1, v2 in zip((x, y), direction.value)]
        new_loc: InternalLocation = self.game.map.get_location(new_x, new_y)

        if new_loc.robot is not None:
            raise RobotError(f"Occupied space: attempted to move to {(new_loc.x, new_loc.y)}, which is occupied.")

        if new_loc.elevation - old_loc.elevation > GameConstants.MOVE_ELEVATION_THRESHOLD:
            raise RobotError(f"Current location {(old_loc.x, old_loc.y)} is below new location {(new_loc.x, new_loc.y)} by more than the allowed threshold of {GameConstants.MOVE_ELEVATION_THRESHOLD}.")

        if new_loc.water:
            raise NotImplementedError # should die!!!

        self.robot.x = new_x
        self.robot.y = new_y

        self.game.map.update_location(new_loc.x, new_loc.y, robot=self.robot)
        self.game.map.update_location(old_loc.x, old_loc.y, robot=None)

        self.robot.has_moved = True
