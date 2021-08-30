from ..container.runner import RobotRunner
from ..container.runner import RobotRunnerConfig
from ..container.runner import RobotRunnerError
from .robottype import RobotType
from .constants import GameConstants

class Robot:

    def __init__(self, x, y, id: str, creator: str, type: RobotType):
        self.id = id
        self.type = type
        self.creator = creator
        self.x = x
        self.y = y
        self.has_moved = False

        self.runner = None
        self.debug = False
        self.alive = False

    def animate(self, code, methods, debug=False):
        config = RobotRunnerConfig(starting_bytecode=0, bytecode_per_turn=GameConstants.BYTECODE_PER_TURN,
                                   max_bytecode=GameConstants.MAX_BYTECODE, chess_clock_mechanism=True,
                                   memory_limit=GameConstants.MEMORY_LIMIT)
        self.runner = RobotRunner(code, methods, self.log, self.error, config, debug=debug)
        self.debug = debug
        self.alive = True

    def kill(self):
        self.runner.kill()
        del self.runner
        self.alive = False

    def log(self, msg):
        if not self.debug:
            return

        msg = str(msg)

        if self.type == RobotType.OVERLORD:
            print(f'[Robot {self.id} log]', msg)
        else:
            team = 'BLACK' if self.team.value else 'WHITE'
            print(f'[Robot {self.id} {team} log]', msg)

    def error(self, msg):
        if not self.debug:
            return

        msg = str(msg)

        if self.type == RobotType.OVERLORD:
            print(f'\u001b[31m[Robot {self.id} error]\u001b[0m', msg)
        else:
            team = 'BLACK' if self.team.value else 'WHITE'
            print(f'\u001b[31m[Robot {self.id} {team} error]\u001b[0m', msg)

    def fatal_error(self, msg):
        if not self.debug:
            return

        msg = str(msg)

        if self.type == RobotType.OVERLORD:
            print(f'\u001b[31m[Robot {self.id} FATAL ERROR]\u001b[0m', msg)
        else:
            team = 'BLACK' if self.team.value else 'WHITE'
            print(f'\u001b[31m[Robot {self.id} {team} FATAL ERROR]\u001b[0m', msg)

    def turn(self):
        if not self.alive:
            raise RuntimeError("Cannot call turn() on unanimated or dead robot.")

        self.has_moved = False

        try:
            self.runner.run()
        except RobotRunnerError as e:
            self.fatal_error(str(e))
            self.kill()

    def __str__(self):
        type = str(self.type)[0]
        abbreviated_id = self.id[:4]
        return f"{type}:{abbreviated_id}"

    def __repr__(self):
        type = str(self.type)
        return f'<ROBOT {self.id} ({type})>'
