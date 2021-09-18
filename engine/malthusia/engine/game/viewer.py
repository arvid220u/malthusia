import time
import sys
import datetime
from typing import NamedTuple

from .constants import GameConstants


class Rectangle(NamedTuple):
    # all are inclusive
    l: int
    t: int
    r: int
    b: int

    def height(self):
        return self.t - self.b + 1


class BasicViewer:
    def __init__(self, view_box: (int, int, int, int), map_states, colors=True):
        self.view_box = Rectangle(*view_box)
        self.map_states = map_states
        self.colors = colors

    def play(self, delay=0.5, keep_history=False):
        print('')

        for state_index in range(len(self.map_states)):
            self.view(state_index)
            time.sleep(delay)
            if not keep_history:
                self.clear()

        self.view(-1)

    def play_synchronized(self, poison_pill, delay=0.5, keep_history=False):
        print('')
        
        state_index = 0
        last_time = datetime.datetime.now().timestamp()
        while state_index < len(self.map_states) or not poison_pill.is_set():
            while len(self.map_states) <= state_index or datetime.datetime.now().timestamp() - last_time < delay:
                time.sleep(0.1)
            if not keep_history and state_index > 0:
                self.clear()
            self.view(state_index)
            last_time = datetime.datetime.now().timestamp()
            state_index += 1

    def clear(self):
        for i in range(self.view_box.height()):
            sys.stdout.write("\033[F")  # back to previous line
            sys.stdout.write("\033[K")  # clear line
    
    def view(self, index=-1):
        print(self.view_board(self.map_states[index]))

    def view_board(self, map):
        view_map = {}
        for x in range(self.view_box.l, self.view_box.r+1):
            view_map[x] = {}
            for y in range(self.view_box.b, self.view_box.t+1):
                view_map[x][y] = (GameConstants.DEFAULT_ELEVATION, None, [])

        for loc in map:
            x, y = loc['x'], loc['y']
            if x in view_map and y in view_map[x]:
                view_map[x][y] = (loc['elevation'], loc['robot'], loc['dead_robots'])

        new_board = ''
        for y in range(self.view_box.t, self.view_box.b-1, -1):
            for x in range(self.view_box.l, self.view_box.r+1):
                elevation, robot, dead_robots = view_map[x][y]
                if robot is not None:
                    new_board += '['
                    new_board += str(robot)
                    if self.colors:
                        new_board += '\033[0m\u001b[0m'
                    new_board += '] '
                else:
                    new_board += f'[{elevation: <3}] '
            new_board += '\n'
        return new_board
