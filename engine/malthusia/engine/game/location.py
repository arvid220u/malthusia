class Location:
    """
    A location has an (x,y) coordinate as well as metadata such as elevation or if there is a robot there.
    """
    def __init__(self, x, y, elevation, robot, dead_robots):
        self.x = x
        self.y = y
        self.elevation = elevation
        self.robot = robot
        self.dead_robots = dead_robots