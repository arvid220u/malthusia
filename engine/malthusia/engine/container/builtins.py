import math

class Builtins:

    def __init__(self, runner):
        self.runner = runner

    def generic_internal_cost_const(self, real_implementation, cost):
        def internal(*args, **kwargs):
            self.runner.multinstrument_call(cost)
            return real_implementation(*args, **kwargs)
        return internal

    def generic_internal_cost_one_arg(self, real_implementation, cost_fn):
        def internal(arg, *args, **kwargs):
            cost = int(cost_fn(arg))
            self.runner.multinstrument_call(cost)
            return real_implementation(arg, *args, **kwargs)
        return internal

    def generic_internal_cost_two_args(self, real_implementation, cost_fn):
        def internal(arg1, arg2, *args, **kwargs):
            cost = int(cost_fn(arg1, arg2))
            self.runner.multinstrument_call(cost)
            return real_implementation(arg1, arg2, *args, **kwargs)
        return internal

    def generic_internal_cost_output(self, real_implementation, cost_fn):
        def internal(*args, **kwargs):
            output = real_implementation(*args, **kwargs)
            cost = int(cost_fn(output))
            self.runner.multinstrument_call(cost)
            return output
        return internal

    def abs(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def callable(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def chr(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def divmod(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: (math.log(abs(a)+1)+math.log(abs(b)+1))/4)

    def hash(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda obj: sys.getsizeof(obj) / 4)

    def hex(self, real_implementation):
        return self.generic_internal_cost_output(real_implementation, lambda hexnum: math.log(abs(int(hexnum, base=16)) + 1) / 4)

    def isinstance(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def issubclass(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def len(self, real_implementation):
        return self.generic_internal_cost_output(real_implementation, lambda l: math.log(abs(l) + 1))

    def oct(self, real_implementation):
        return self.generic_internal_cost_output(real_implementation, lambda octnum: math.log(abs(int(octnum, base=8)) + 1))

    def ord(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def pow(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda b, e: math.log(abs(e)+1)*1 + math.log(abs(b)+1)/4)

    def repr(self, real_implementation):
        return self.generic_internal_cost_output(real_implementation, lambda s: len(s) / 4)

    def round(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda x: math.log(abs(x)+1)/4)

    def sorted(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda iterable: len(iterable) * int(math.log(len(iterable) + 3)))

    def __build_class__(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def setattr(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def delattr(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def _getattr_(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def __import__(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def _getitem_(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)
