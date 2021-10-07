from ..container.runner import RobotRunner
from ..container.runner import RobotRunnerConfig
from ..container.runner import RobotRunnerError, RobotDied
from .robottype import RobotType
from .constants import GameConstants
from ..config import DEBUG


class Robot:

    def __init__(self, x, y, id: str, creator: str, type: RobotType, kill_robot_callback):
        self.id = id
        self.type = type
        self.creator = creator
        self.x = x
        self.y = y
        self.has_moved = False
        self.kill_robot_callback = kill_robot_callback

        self.runner = None
        self.debug = False
        self.alive = False

        self.check_rep()

    def check_rep(self):
        if not DEBUG:
            return
        assert (self.alive and self.runner is not None) or (not self.alive and self.runner is None)

    def animate(self, code, methods, debug=False):
        config = RobotRunnerConfig(starting_bytecode=0, bytecode_per_turn=GameConstants.BYTECODE_PER_TURN,
                                   max_bytecode=GameConstants.MAX_BYTECODE, chess_clock_mechanism=True,
                                   memory_limit=GameConstants.MEMORY_LIMIT)
        self.runner = RobotRunner(code, methods, self.log, self.error, config, debug=debug)
        self.debug = debug
        self.alive = True

        self.check_rep()

    def kill(self, reason=None):
        self.status(f"Died :(. {reason if reason is not None else ''}")

        self.runner.kill()
        del self.runner
        self.alive = False

        self.kill_robot_callback(self)

        self.check_rep()

    def status(self, msg):
        if not self.debug:
            return

        msg = str(msg)

        print(f'[Robot {self.id} status]', msg)

    def log(self, msg):
        if not self.debug:
            return

        msg = str(msg)

        print(f'[Robot {self.id} log]', msg)

    def error(self, msg):
        if not self.debug:
            return

        msg = str(msg)

        print(f'\u001b[31m[Robot {self.id} error]\u001b[0m', msg)

    def fatal_error(self, msg):
        if not self.debug:
            return

        msg = str(msg)

        print(f'\u001b[31m[Robot {self.id} FATAL ERROR]\u001b[0m', msg)

    def turn(self):
        if not self.alive:
            raise RuntimeError("Cannot call turn() on unanimated or dead robot.")

        self.has_moved = False

        try:
            self.runner.run()
        except RobotRunnerError as e:
            self.fatal_error(str(e))
            self.kill()
        except RobotDied as e:
            self.kill(reason=str(e))

        self.check_rep()

    def __str__(self):
        t = str(self.type)[0]
        abbreviated_id = self.id[:2]
        return f"{t}:{abbreviated_id}"

    def __repr__(self):
        t = str(self.type)
        return f'<ROBOT {self.id} ({t})>'


class RobotError(Exception):
    """Raised for illegal robot inputs"""
    pass

