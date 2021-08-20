import math

class Builtins:

    def __init__(self, runner):
        self.runner = runner

    def instrumented_sorted(self, iterable, **kwargs):
        cost = len(iterable) * int(math.log(len(iterable) + 3))
        self.runner.multinstrument_call(cost)
        return sorted(iterable, **kwargs)
