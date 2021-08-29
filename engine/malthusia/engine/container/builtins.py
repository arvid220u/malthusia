import math
from typing import Tuple, Optional, Literal, Iterable, Any

class Builtins:
    """
    Builtins contains cost instrumentation of all builtin functions, methods and constructors.
    Instead of re-implementing every builtin, we compute a cost based on the arguments (e.g. len * log(len) for sorted)
    and subtract it before calling the original implementation.
    """

    def __init__(self, runner):
        self.runner = runner

    #
    # cost helpers
    #

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

    def generic_internal_cost_one_arg_optional(self, real_implementation, cost_fn):
        def internal(*args, **kwargs):
            if len(args) > 0:
                cost = int(cost_fn(args[0]))
            else:
                cost = 1
            self.runner.multinstrument_call(cost)
            return real_implementation(*args, **kwargs)
        return internal

    def generic_internal_cost_args_and_kwargs(self, real_implementation, cost_fn):
        def internal(*args, **kwargs):
            cost = int(cost_fn(args, kwargs))
            self.runner.multinstrument_call(cost)
            return real_implementation(*args, **kwargs)
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

    #
    # global functions
    #

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

    def sum(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))


    #
    # type methods
    #

    # string

    def capitalize(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def casefold(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def center(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda s, w: max(len(s), w))

    def ljust(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda s, w: max(len(s), w))

    def count(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def endswith(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda s, suffix: len(suffix))

    def expandtabs(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def find(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def isdecimal(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def isdigit(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def isascii(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def isidentifier(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def islower(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def isnumeric(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def isprintable(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def isspace(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def istitle(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def isupper(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def join(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda s, seq: len(seq) + len(s)/8)

    def index(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def lower(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def lstrip(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def partition(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq)/4)

    def removeprefix(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda s, prefix: len(prefix))

    def removesuffix(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda s, suffix: len(suffix))

    def replace(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def rfind(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def rindex(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def rjust(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def rpartition(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def rsplit(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def rstrip(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def split(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def splitlines(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def startswith(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda s, p: len(p))

    def strip(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def swapcase(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def title(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def translate(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def upper(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda s: len(s))

    def zfill(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda s, w: w + len(s))

    def encode(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    # set

    def isdisjoint(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def issubset(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def issuperset(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def union(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def intersection(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def difference(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def symmetric_difference(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def copy(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda a: len(a))

    def update(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def intersection_update(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def difference_update(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def symmetric_difference_update(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: math.log(len(a)+1) + math.log(len(b)+1))

    def add(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda a: math.log(len(a)+1))

    def remove(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda a: math.log(len(a)+1))

    def discard(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda a: math.log(len(a)+1))

    def pop(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda a: math.log(len(a)+1))

    def clear(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda a: math.log(len(a)+1))

    # dict

    def copy(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda a: len(a))

    def copy(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def items(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def keys(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def values(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def reversed(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def pop(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 4)

    def popitem(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def update(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a, b: len(b) + math.log(len(a)+1))


    # list

    def append(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def sort(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda l: len(l) * math.log(len(l)+3))

    def reverse(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda l: len(l))

    #
    # module methods
    #

    # math

    def factorial(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: n*n*math.log(abs(n)+1))

    def comb(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda n, k: n)

    def fsum(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def gcd(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a,b: math.log(abs(a) + 1) + math.log(abs(b) + 1))

    def isqrt(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: math.log(abs(n)+1)/4)

    def lcm(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda a,b: math.log(abs(a) + 1) + math.log(abs(b) + 1))

    def perm(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda n, k: n)

    def prod(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda seq: len(seq))

    def exp(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: math.log(abs(n)+1)/4)

    def expm1(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: math.log(abs(n)+1)/4)

    def log(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: math.log(abs(n)+1)/4)

    def log1p(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: math.log(abs(n)+1)/4)

    def log2(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: math.log(abs(n)+1)/4)

    def log10(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: math.log(abs(n)+1)/4)

    def sqrt(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda n: math.log(abs(n)+1)/4)

    def pow(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda b, e: math.log(abs(e)+1)*1 + math.log(abs(b)+1)/4)

    def dist(self, real_implementation):
        return self.generic_internal_cost_two_args(real_implementation, lambda x, y: len(x) + len(y))

    def hypot(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda x: len(x))

    # random

    def seed(self, real_implementation):
        def internal_seed(a=None, version=2):
            if a is None:
                raise RuntimeError("Need to seed random with an actual value; system time is not available.")
            cost = 1
            self.runner.multinstrument_call(cost)
            return real_implementation(a=a, version=version)
        return internal_seed

    def getstate(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 100)

    def setstate(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 100)

    def randbytes(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda x: x)

    def randrange(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def randint(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def getrandbits(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda x: x)

    def choice(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda x: len(x))

    def choices(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda x: len(x))

    def shuffle(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda x: len(x))

    def sample(self, real_implementation):
        return self.generic_internal_cost_one_arg(real_implementation, lambda x: len(x))

    def random(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)

    def uniform(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def triangular(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def betavariate(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def expovariate(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def gammavariate(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def gauss(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def lognormvariate(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def normalvariate(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def vonmisesvariate(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def paretovariate(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)

    def weibullvariate(self, real_implementation):
        return self.generic_internal_cost_args_and_kwargs(real_implementation, lambda a, kw: math.log(max([abs(x) for x in a + tuple(kw.values())])+1)/4 + 1)


    #
    # type initialization methods
    #

    def str(self, real_implementation):
        return self.generic_internal_cost_output(real_implementation, lambda s: len(s))

    def range(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 3)

    def list(self, real_implementation):
        return self.generic_internal_cost_one_arg_optional(real_implementation, lambda seq: len(seq))

    def bytes(self, real_implementation):
        def cost_fn(arg):
            if isinstance(arg, int):
                return arg
            return len(arg)
        return self.generic_internal_cost_one_arg_optional(real_implementation, cost_fn)

    def complex(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 2)

    def dict(self, real_implementation):
        def cost_fn(args, kwargs):
            cost = len(kwargs)
            if len(args) > 0:
                cost += len(args[0])
            return cost
        return self.generic_internal_cost_args_and_kwargs(real_implementation, cost_fn)

    def frozenset(self, real_implementation):
        return self.generic_internal_cost_one_arg_optional(real_implementation, lambda seq: len(seq))

    def int(self, real_implementation):
        def cost_fn(arg):
            if hasattr(arg, "__len__"):
                return len(arg)
            return 1
        return self.generic_internal_cost_one_arg_optional(real_implementation, cost_fn)

    def set(self, real_implementation):
        return self.generic_internal_cost_one_arg_optional(real_implementation, lambda seq: len(seq))

    def slice(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 2)

    def tuple(self, real_implementation):
        return self.generic_internal_cost_one_arg_optional(real_implementation, lambda seq: len(seq))

    def type(self, real_implementation):
        return self.generic_internal_cost_const(real_implementation, 1)
