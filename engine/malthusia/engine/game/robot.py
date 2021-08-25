from ..container.runner import RobotRunner
from ..container.runner import RobotRunnerError
from .robottype import RobotType

class Robot:
    STARTING_HEALTH = 1

    def __init__(self, row, col, team, id, type=RobotType.PAWN):
        self.id = id
        self.type = type

        self.row = row
        self.col = col
        self.has_moved = False

        self.health = Robot.STARTING_HEALTH
        self.logs = []

        self.team = team

        self.runner = None
        self.debug = False
        self.alive = False

    def animate(self, code, methods, debug=False):
        self.runner = RobotRunner(code, methods, self.log, self.error, debug=debug)
        self.debug = debug
        self.alive = True

    def kill(self):
        self.runner.kill()
        self.alive = False

    def log(self, msg):
        msg = str(msg)
        self.logs.append({'type': 'log', 'msg': msg})

        if self.debug:
            if self.type == RobotType.OVERLORD:
                print(f'[Robot {self.id} log]', msg)
            else:
                team = 'BLACK' if self.team.value else 'WHITE'
                print(f'[Robot {self.id} {team} log]', msg)

    def error(self, msg):
        if not isinstance(msg, str):
            raise RuntimeError('Can only error strings.')

        self.logs.append({'type': 'error', 'msg': msg})

        if self.debug:
            if self.type == RobotType.OVERLORD:
                print(f'\u001b[31m[Robot {self.id} error]\u001b[0m', msg)
            else:
                team = 'BLACK' if self.team.value else 'WHITE'
                print(f'\u001b[31m[Robot {self.id} {team} error]\u001b[0m', msg)

    def fatal_error(self, msg):
        if not isinstance(msg, str):
            raise RuntimeError('Can only error strings.')

        self.logs.append({'type': 'fatal_error', 'msg': msg})

        if self.debug:
            if self.type == RobotType.OVERLORD:
                print(f'\u001b[31m[Robot {self.id} FATAL ERROR]\u001b[0m', msg)
            else:
                team = 'BLACK' if self.team.value else 'WHITE'
                print(f'\u001b[31m[Robot {self.id} {team} FATAL ERROR]\u001b[0m', msg)

    def turn(self):
        if not self.alive:
            raise RuntimeError("Cannot call turn() on unanimated or dead robot.")
        self.logs.clear()
        self.has_moved = False

        try:
            self.runner.run()
        except RobotRunnerError as e:
            self.fatal_error(str(e))
            self.alive = False

    def __str__(self):
        team = 'B' if self.team.value else 'W'
        return '%s%3d' % (team, self.id)

    def __repr__(self):
        team = 'BLACK' if self.team.value else 'WHITE'
        return f'<ROBOT {self.id} {team}>'
