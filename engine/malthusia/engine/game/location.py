from typing import NamedTuple, List, Optional
from .robot import Robot

class Location(NamedTuple):
    """
    A location has an (x,y) coordinate as well as metadata such as elevation or if there is a robot there.
    It is immutable
    """
    x: int
    y: int
    elevation: int
    robot: Optional[Robot]
    dead_robots: List[Robot]

    @classmethod
    def from_dict(cls, d):
        return Location(robot=None, dead_robots=[], **d)

    def copy_and_change_unsafe(self, **kwargs):
        """
        unsafe: please discard self after this; will share mutable objects
        """
        return Location(x=self.x if "x" not in kwargs else kwargs["x"],
                        y=self.y if "y" not in kwargs else kwargs["y"],
                        elevation=self.elevation if "elevation" not in kwargs else kwargs["elevation"],
                        robot=self.robot if "robot" not in kwargs else kwargs["robot"],
                        dead_robots=self.dead_robots if "dead_robots" not in kwargs else kwargs["dead_robots"])

    def serialize(self):
        return self._asdict()
