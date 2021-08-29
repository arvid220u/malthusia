import sys
import traceback
import logging
import collections.abc
import re
import os
import random

from ..restrictedpython import safe_builtins, Guards
from time import sleep
from .instrument import Instrument
from .builtins import *
from . import memory
from .code_container import CodeContainer

logger = logging.getLogger(__name__)

class OutOfBytecode(Exception):
    pass

class RobotRunnerError(Exception):
    pass

class RobotRunnerConfig:

    def __init__(self, starting_bytecode, bytecode_per_turn, max_bytecode, chess_clock_mechanism,
                 memory_limit):
        """
        Create a RobotRunner configuration.
        :param starting_bytecode: the amount of bytecode the robot starts with
        :param bytecode_per_turn: bytecode added before every turn (including first; so first turn gets starting + this)
        :param max_bytecode: the max bytecode allowed for a single turn. caps the accumulation in chess mode. be cautious about setting this too high, as memory is currently only checked inter-turns and not intra-turns
        :param chess_clock_mechanism: if true, adds the last turn's unused bytecode to the next turn. otherwise does not.
        :param memory_limit: the max number of bytes allowed for a bot to persist in between turns
        """
        self.starting_bytecode = starting_bytecode
        self.bytecode_per_turn = bytecode_per_turn
        self.max_bytecode = max_bytecode
        self.chess_clock_mechanism = chess_clock_mechanism
        self.memory_limit = memory_limit

class RobotRunner:
    """
    RobotRunner is initialized with a code container, and is responsible for running the instrumented code.
    It injects the builtins that are necessary and allowed, and modifies some of them to include instrumentation.
    __init__(), run() and kill() are the primary methods.
    """

    NOT_INSTRUMENTED_BUILTINS= {"None", "False", "True"}
    BUILTIN_CLASSES = {"bytes", "complex", "float", "int", "range", "tuple", "zip", "list", "set", "frozenset", "str", "bool", "slice", "type"}
    BUILTIN_FUNCTIONS= {"abs", "callable", "chr", "divmod", "hash", "hex", "isinstance", "issubclass", "len", "oct", "ord", "pow", "repr", "round", "sorted", "__build_class__", "setattr", "delattr", "_getattr_", "__import__", "_getitem_", "sum"}
    BUILTIN_INSTRUMENTATION_ARTIFACTS= {"__metaclass__", "__instrument__", "__multinstrument__", "_write_", "_getiter_", "_inplacevar_", "_unpack_sequence_", "_iter_unpack_sequence_", "log", "enumerate", "__safe_type__", "__instrument_binary_multiply__", "_print_", "_apply_"}
    DISALLOWED_BUILTINS= ["id"]
    BUILTIN_ERRORS = {"ArithmeticError",
                      "AssertionError",
                      'AttributeError',
                      'BaseException',
                      'BufferError',
                      'BytesWarning',
                      'DeprecationWarning',
                      'EOFError',
                      'EnvironmentError',
                      'Exception',
                      'FloatingPointError',
                      'FutureWarning',
                      'GeneratorExit',
                      'IOError',
                      'ImportError',
                      'ImportWarning',
                      'IndentationError',
                      'IndexError',
                      'KeyError',
                      'KeyboardInterrupt',
                      'LookupError',
                      'MemoryError',
                      'NameError',
                      'NotImplementedError',
                      'OSError',
                      'OverflowError',
                      'PendingDeprecationWarning',
                      'RecursionError',
                      'ReferenceError',
                      'RuntimeError',
                      'RuntimeWarning',
                      'StopIteration',
                      'SyntaxError',
                      'SyntaxWarning',
                      'SystemError',
                      'SystemExit',
                      'TabError',
                      'TypeError',
                      'UnboundLocalError',
                      'UnicodeDecodeError',
                      'UnicodeEncodeError',
                      'UnicodeError',
                      'UnicodeTranslateError',
                      'UnicodeWarning',
                      'UserWarning',
                      'ValueError',
                      'Warning',
                      'ZeroDivisionError',
                      'OutOfBytecode'}

    @staticmethod
    def validate_arguments(*args, error_type):
        for i, arg in enumerate(args):
            if "DANGEROUS" in type(arg).__module__:
                raise error_type(f"arguments are invalid; argument {i} has type {type(arg)} which is user-defined and possibly dangerous")

    def __init__(self, code: CodeContainer, game_methods, log_method, error_method, config: RobotRunnerConfig, debug=False):
        self.builtins = Builtins(self)
        self.config = config
        self.globals = {
            '__builtins__': {k: v for k, v in safe_builtins.items()},
            '__name__': 'DANGEROUS_main'
        }

        self.globals['__builtins__']['RecursionError'] = RecursionError
        self.globals['__builtins__']['__metaclass__'] = type
        self.globals['__builtins__']['__instrument__'] = self.instrument_call
        self.globals['__builtins__']['__instrument_binary_multiply__'] = self.instrument_binary_multiply_call
        self.globals['__builtins__']['__multinstrument__'] = self.multinstrument_call
        self.globals['__builtins__']['__import__'] = self.import_call
        self.globals['__builtins__']['_getitem_'] = self.getitem_call
        self.globals['__builtins__']['_write_'] = lambda obj: self.write_call(obj, set(game_methods.values()))
        self.globals['__builtins__']['_getiter_'] = lambda i: i
        self.globals['__builtins__']['_inplacevar_'] = self.inplacevar_call
        self.globals['__builtins__']['_unpack_sequence_'] = Guards.guarded_unpack_sequence
        self.globals['__builtins__']['_iter_unpack_sequence_'] = Guards.guarded_iter_unpack_sequence
        self.globals['__builtins__']['_getattr_'] = self.create_getattr_call(self.globals['__builtins__']['_getattr_'])
        self.globals['__builtins__']['_apply_'] = self.apply_call
        self.globals['__builtins__']['_print_'] = self.print_call
        self.globals['__builtins__']['log'] = log_method
        self.globals['__builtins__']['type'] = type
        self.globals['__builtins__']['sum'] = sum
        self.globals['__builtins__']['OutOfBytecode'] = OutOfBytecode
        self.globals['__builtins__']['range'] = range
        self.globals['__builtins__']['list'] = list
        self.globals['__builtins__']['tuple'] = tuple
        self.globals['__builtins__']['__safe_type__'] = type
        self.globals['__builtins__']['enumerate'] = enumerate
        self.globals['__builtins__']['set'] = set
        self.globals['__builtins__']['frozenset'] = frozenset
        self.globals['__builtins__']['sorted'] = sorted

        for builtin in self.DISALLOWED_BUILTINS:
            del self.globals["__builtins__"][builtin]

        logger.debug("BUILTINS")
        for builtin in self.globals['__builtins__']:
            logger.debug(self.globals['__builtins__'][builtin])
            if builtin in self.NOT_INSTRUMENTED_BUILTINS:
                continue
            elif builtin in self.BUILTIN_FUNCTIONS:
                instrumented_builtin = getattr(self.builtins, builtin)
                self.globals['__builtins__'][builtin] = instrumented_builtin(self.globals['__builtins__'][builtin])
            elif builtin in self.BUILTIN_CLASSES:
                # class methods/functions are instrumented using _getattr_
                continue
            elif builtin in self.BUILTIN_ERRORS:
                # errors are fine, there's nothing really resource intensive you can do with them
                continue
            elif builtin in self.BUILTIN_INSTRUMENTATION_ARTIFACTS:
                continue
            else:
                logger.error("builtin not expected:")
                logger.error(builtin)
                assert(False)

        # make the dangerous exceptions start with _ so that they cannot be raised by user code
        for excp in Instrument.DANGEROUS_EXCEPTIONS:
            assert excp in self.globals['__builtins__']
            self.globals['__builtins__']['_' + excp] = self.globals['__builtins__'][excp]
            del self.globals['__builtins__'][excp]

        logger.debug("BUILTINS")
        logger.debug(self.globals['__builtins__'])
        logger.debug("END BUILTINS")

        for key, value in game_methods.items():
            self.globals['__builtins__'][key] = value

        self.error_method = error_method
        self.game_methods = game_methods
        self.code = code
        self.imports = {}

        self.bytecode = self.config.starting_bytecode
        self.last_memory_usage = 0

        self.initialized = False
        self.killed = False

        self.debug = debug

    def print_call(self, *args, **kwargs):
        class P:
            def _call_print(self):
                raise SyntaxError("print() is not allowed. Please use log() instead.")
        return P

    def create_getattr_call(self, old_getattr):
        def get_full_name(t):
            return type(t).__module__ + "." + type(t).__qualname__

        def instrument_getattr(object, name, default=None):
            logger.debug("in instrument getattr!!!!")
            object_type = type(object)
            if object_type.__qualname__ == "type" and object_type.__module__ == "builtins":
                object_type = object
            if object_type.__module__ not in {"builtins", "random", "math"}:
                return getattr(object, name, default)
            if object_type.__qualname__ == "module" and object.__name__ != "math":
                return getattr(object, name, default)
            logger.debug("ok gets here")
            real_attr = getattr(object, name, default)
            logger.debug("full name of attr: " + get_full_name(real_attr))
            if get_full_name(real_attr) not in {"builtins.builtin_function_or_method", "builtins.method_descriptor", "builtins.method"}:
                # we only care about builtin functions or methods
                # we also care about method descriptors
                return real_attr
            # we want to instrument this!
            instrumented_builtin = getattr(self.builtins, name)
            logger.debug("method descriptor? " + get_full_name(real_attr))
            if get_full_name(real_attr) == "builtins.method_descriptor":
                # we need to do nothing more
                return instrumented_builtin(real_attr)
            # otherwise, we need to check if __self__ is a module or not
            logger.debug("module? " + get_full_name(real_attr.__self__))
            if get_full_name(real_attr.__self__) in {"builtins.module", "random.Random"}:
                # we need to do nothing more
                return instrumented_builtin(real_attr)
            # the last case is we need to unbound the method, then rebind it
            unbound_attr = getattr(type(object), name, default)
            unbound_instrumented = instrumented_builtin(unbound_attr)
            def rebind_attr(*args, **kwargs):
                return unbound_instrumented(object, *args, **kwargs)
            return rebind_attr

        def new_getattr(object, name, default=None):
            return old_getattr(object, name, default, getattr=instrument_getattr)

        return new_getattr

    def inplacevar_call(self, op, x, y):
        if not isinstance(op, str):
            raise SyntaxError('Unsupported in place op.')

        if op == '+=':
            return x + y

        elif op == '-=':
            return x - y

        elif op == '*=':
            self.instrument_binary_multiply_call(x, y)
            return x * y

        elif op == '/=':
            return x / y

        elif op == '//=':
            return x // y

        elif op == '%=':
            return x % y

        elif op == '<<=':
            return x << y

        elif op == '>>=':
            return x >> y

        elif op == '^=':
            return x ^ y

        elif op == '|=':
            return x | y

        elif op == '&=':
            return x & y

        else:
            raise SyntaxError('Unsupported in place op "' + op + '".')

    @staticmethod
    def write_call(obj, disallowed_objs):
        if isinstance(obj, type(sys)):
            raise RuntimeError('Can\'t write to modules.')

        if isinstance(obj, type(lambda: 1)):
            raise RuntimeError('Can\'t write to functions.')

        if isinstance(obj, type) and obj.__module__ == "random":
            raise RuntimeError("Can't write to random.")

        if isinstance(obj, collections.abc.Hashable):
            # all internal disallowed objs must be hashable because in a set
            if obj in disallowed_objs:
                raise RuntimeError(f'Can\'t write to {obj}')

        return obj

    @staticmethod
    def getitem_call(accessed, attribute):
        if isinstance(attribute, str) and len(attribute) > 0:
            if attribute[0] == '_':
                raise RuntimeError('Cannot access attributes that begin with "_".')

        return accessed[attribute]

    def instrument_call(self):
        self.bytecode -= 1
        self.check_bytecode()

    def instrument_binary_multiply_call(self, a, b):
        if isinstance(a, collections.abc.Sized) and isinstance(b, int):
            self.multinstrument_call(len(a) * b)
        elif isinstance(b, collections.abc.Sized) and isinstance(a, int):
            self.multinstrument_call(len(b) * a)
        elif isinstance(a, int) and isinstance(b, int):
            self.multinstrument_call(int(math.log(abs(a)+1) + math.log(abs(b)+1)))
        elif isinstance(b, collections.abc.Sized) and isinstance(a, collections.abc.Sized):
            self.multinstrument_call(len(a)+len(b))
        else:
            logger.debug("not sure how to instrument binary multiply of non-integer/non-sequence")

    def apply_call(self, func, *args, **kwargs):
        logger.debug(f"IN APPLY CALL for {func}")
        if type(func) == type and func.__module__ == "builtins":
            logger.debug(f"FOR BUILTIN TYPE: {func}")
            instrumented_builtin = getattr(self.builtins, func.__name__)
            return instrumented_builtin(func)(*args, **kwargs)
        return func(*args, **kwargs)


    def multinstrument_call(self, n):
        if n < 0:
            raise ValueError('n must be greater than or equal to 0')
        self.bytecode -= n
        self.check_bytecode()

    def check_bytecode(self):
        if self.bytecode <= 0:
            raise OutOfBytecode(f'Ran out of bytecode. Remaining bytecode: {self.bytecode}')

    def import_call(self, name, globals=None, locals=None, fromlist=(), level=0, caller='robot'):
        if not isinstance(name, str) or not (isinstance(fromlist, tuple) or fromlist is None):
            raise ImportError('Invalid import.')

        if name == '':
            # This should be easy to add, but it's work.
            raise ImportError('No relative imports (yet).')

        if not name in self.code:
            # almost all libraries will be very unsafe
            # for example, any library containing a class will allow bots to communicate with each other
            # by writing to a new class property.
            # math is fine, because it contains only functions and primitive types
            if name == 'math':
                import math
                return math
            if name == "random":
                # we could do importlib.reload(random) here and return random after del random.SystemRandom, del random.seed, etc etc etc
                # reloading random could have effects elsewhere where we use random though, which is not desirable - we don't want bots to affect other game randomness
                # instead, we just return a new instance of random.Random, seeded with the current randomness
                # we need to add random.Random in self.write_call
                # we also need to modify code in the getattr call to (1) instrument, and (2) restrict seed
                return random.Random(random.random())

            raise ImportError('Module "' + name + '" does not exist.')

        my_builtins = dict(self.globals['__builtins__'])
        my_builtins['__import__'] = lambda n, g, l, f, le: self.import_call(n, g, l, f, le, caller=name)
        run_globals = {'__builtins__': my_builtins, '__name__': "DANGEROUS_" + name}

        # Loop check: keep dictionary of who imports who.  If loop, error.
        # First, we build a directed graph:
        if not caller in self.imports:
            self.imports[caller] = {name}
        else:
            self.imports[caller].add(name)

        # Next, we search for cycles.
        path = set()

        def visit(vertex):
            path.add(vertex)
            for neighbour in self.imports.get(vertex, ()):
                if neighbour in path or visit(neighbour):
                    return True
            path.remove(vertex)
            return False

        if any(visit(v) for v in self.imports):
            raise ImportError('Infinite loop in imports: ' + ", ".join(path))

        exec(self.code[name], run_globals)
        new_module = type(sys)(name)
        new_module.__dict__.update(run_globals)

        return new_module

    def init_robot(self):
        try:
            locals = {}
            exec(self.code['bot'], self.globals, locals)
            self.globals.update(locals) # we need to update the globals with the locals in the module space, because later we are just calling the turn function
            self.initialized = True
        except (KeyboardInterrupt, SystemError, OSError, SystemExit, MemoryError):
            raise
        except:
            self.report_error()
        if not self.initialized:
            raise RobotRunnerError("Failed to initialize robot.")
        self.check_memory()

    def do_turn(self):
        if 'turn' in self.globals and isinstance(self.globals['turn'], type(lambda: 1)):
            try:
                exec(self.globals['turn'].__code__, self.globals, {})
            except (KeyboardInterrupt, SystemError, OSError, SystemExit, MemoryError):
                raise
            except:
                self.report_error()
        else:
            raise RobotRunnerError('Couldn\'t find turn() function.')
        self.check_memory()

    def report_error(self):
        error_str = traceback.format_exc(limit=1000)
        this_file = os.path.abspath(__file__)
        # remove apply_call, because it just clutters up everything while providing little of value
        remove_apply = r'^\s*File "' + this_file.replace("/","\/") + r'", line \d+, in apply_call\s*\n\s*return func\(\*args, \*\*kwargs\)\s*\n'
        modified_error_str = re.sub(remove_apply, "", error_str, flags=re.MULTILINE)
        self.error_method(modified_error_str)


    def check_memory(self):
        mem_usage = memory.bytes_usage({k: v for k, v in self.globals.items() if k != "__builtins__"})
        if mem_usage > self.config.memory_limit:
            raise RobotRunnerError(f"Out of memory! Robot uses {mem_usage} bytes in round-persistent memory (e.g. globals), which is more than the allowed {self.config.memory_limit} bytes.")
        self.last_memory_usage = mem_usage


    def run(self):
        """
        Runs one turn of the robot, initializing it if needed.
        :raises: RobotRunnerError if an error occurred from which the runner cannot recover (failed to initialize, out of memory)
        """
        if self.killed:
            raise RuntimeError("Cannot run a killed RobotRunner")

        if self.config.chess_clock_mechanism:
            self.bytecode = max(self.bytecode, 0) + self.config.bytecode_per_turn
        else:
            self.bytecode = self.config.bytecode_per_turn
        self.bytecode = min(self.config.max_bytecode, self.bytecode)

        if not self.initialized:
            self.init_robot()

        self.do_turn()

    def kill(self):
        logger.debug(f"Killing RobotRunner {self}")
        self.killed = True
        # release some memory
        del self.globals
        del self.code
