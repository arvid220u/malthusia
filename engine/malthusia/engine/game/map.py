from typing import List, Dict
from .location import InternalLocation
from .constants import GameConstants
import json


def default_location(x, y):
    return InternalLocation(x=x, y=y, elevation=GameConstants.DEFAULT_ELEVATION, water=True, robot=None, dead_robots=[])


class Map:
    """
    An infinite map of locations.
    """

    def __init__(self, locations: List[InternalLocation]):
        # locations is indexed [x][y]
        self.locations: Dict[Dict[InternalLocation]] = {}
        self.add_locations(locations)

    def update_location(self, x, y, **fields):
        old_loc = self.get_location(x, y)
        loc = old_loc.copy_and_change_unsafe(**fields)
        if loc.x not in self.locations:
            self.locations[loc.x] = {}
        self.locations[loc.x][loc.y] = loc

    def add_locations(self, locations):
        """
        precondition: none of the locations already exist
        """
        for loc in locations:
            if loc.x not in self.locations:
                self.locations[loc.x] = {}
            assert loc.y not in self.locations[loc.x]
            self.locations[loc.x][loc.y] = loc

    def get_location(self, x, y) -> InternalLocation:
        if x not in self.locations or y not in self.locations[x]:
            return default_location(x, y)
        return self.locations[x][y]

    def serialize(self):
        return [loc.serialize() for locdict in self.locations.values() for loc in locdict.values()]

    @classmethod
    def from_list(cls, l: List[Dict]):
        locations = [InternalLocation.from_dict(d) for d in l]
        return cls(locations)

    @classmethod
    def from_file(cls, filename):
        with open(filename, "r") as f:
            l = json.load(f)
        return cls.from_list(l)

    def remove_robot(self, robot):
        assert not robot.alive
        new_dead_robots = self.get_location(robot.x, robot.y).dead_robots
        new_dead_robots.append(robot)
        self.update_location(robot.x, robot.y, robot=None, dead_robots=new_dead_robots)

    def add_robot(self, robot, x, y):
        """
        precondition: x,y is spawnable
        """
        assert self.spawnable(x, y)

        self.update_location(x, y, robot=robot)

    def spawnable(self, x, y):
        """
        :param x:
        :param y:
        :return: true iff a robot can spawn on this location
        """
        loc = self.get_location(x, y)
        # spawnable iff no robot is there
        return loc.robot is None
