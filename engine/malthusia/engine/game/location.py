from typing import NamedTuple, List, Optional
from .robot import Robot


class LocationInfo(NamedTuple):
    """
    This is the location information that can be visible by robots.
    """
    x: int
    y: int
    elevation: int
    water: bool
    occupied: bool


class InternalLocation(NamedTuple):
    """
    A location has an (x,y) coordinate as well as metadata such as elevation or if there is a robot there.
    It is immutable
    """
    x: int
    y: int
    elevation: int
    water: bool
    robot: Optional[Robot]
    dead_robots: List[Robot]

    @classmethod
    def from_dict(cls, d):
        return InternalLocation(robot=None, dead_robots=[], **d)

    def copy_and_change_unsafe(self, **kwargs):
        """
        unsafe: please discard self after this; will share mutable objects
        """
        return InternalLocation(x=self.x if "x" not in kwargs else kwargs["x"],
                                y=self.y if "y" not in kwargs else kwargs["y"],
                                elevation=self.elevation if "elevation" not in kwargs else kwargs["elevation"],
                                water=self.water if "water" not in kwargs else kwargs["water"],
                                robot=self.robot if "robot" not in kwargs else kwargs["robot"],
                                dead_robots=self.dead_robots if "dead_robots" not in kwargs else kwargs["dead_robots"])

    def serialize(self):
        d = self._asdict()
        d["robot"] = d["robot"].serialize() if d["robot"] is not None else None
        d["dead_robots"] = [r.serialize() for r in d["dead_robots"]]
        return d

    def to_location_info(self):
        return LocationInfo(x=self.x, y=self.y, elevation=self.elevation, water=self.water, occupied=self.robot is not None)
