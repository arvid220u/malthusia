import logging

from .location import Location
from .direction import Direction
from .robot import RobotError

logger = logging.getLogger(__name__)


class Wanderer:
    """
    This class contains all functions that can be called by a wanderer.
    """

    def __init__(self, game, robot):
        self.game = game
        self.robot = robot

    def check_location(self, x, y) -> Location:
        raise NotImplementedError

    def get_location(self):
        x, y = self.robot.x, self.robot.y
        if self.game.board[x][y] != self.robot:
            raise RobotError('something went wrong; please contact the devs')
        return x, y

    def move(self, direction: Direction):
        if self.robot.has_moved:
            raise RobotError('this unit has already moved this turn; robots can only move once per turn')

        x, y = self.robot.x, self.robot.y
        if self.game.board[x][y] != self.robot:
            raise RobotError('something went wrong; please contact the devs')

        new_x, new_y = (x, y) + direction.value

        if self.game.board[new_x][new_y]:
            raise RobotError('you cannot move to a space that is already occupied')

        self.game.board[new_x][new_y] = None
        self.robot.x = new_x
        self.robot.y = new_y
        self.game.board[new_x][new_y] = self.robot

        self.robot.has_moved = True
