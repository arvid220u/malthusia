import sys
import traceback
import logging
import collections.abc

from ..restrictedpython import safe_builtins, limited_builtins, utility_builtins, Guards
from time import sleep
from .instrument import Instrument
from .builtins import *
from . import memory

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

    @staticmethod
    def validate_arguments(*args, error_type):
        for i, arg in enumerate(args):
            if "DANGEROUS" in type(arg).__module__:
                raise error_type(f"arguments are invalid; argument {i} has type {type(arg)} which is user-defined and possibly dangerous")

    def __init__(self, code, game_methods, log_method, error_method, config: RobotRunnerConfig, debug=False):
        self.builtins = Builtins(self)
        self.config = config
        self.globals = {
            '__builtins__': dict(i for dct in [safe_builtins, limited_builtins] for i in dct.items()),
            '__name__': 'DANGEROUS_main'
        }

        self.globals['__builtins__']['RecursionError'] = RecursionError

        builtin_errors = {"ArithmeticError",
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
        not_instrumented_builtins = {"None", "False", "True"}
        builtin_classes = {"bytes", "complex", "float", "int", "range", "tuple", "zip", "list", "set", "frozenset", "str", "bool", "slice", "type"}
        builtin_functions = {"abs", "callable", "chr", "divmod", "hash", "hex", "isinstance", "issubclass", "len", "oct", "ord", "pow", "repr", "round", "sorted", "__build_class__", "setattr", "delattr", "_getattr_", "__import__", "_getitem_", "sum"}
        builtin_instrumentation_artifacts = {"__metaclass__", "__instrument__", "__multinstrument__", "_write_", "_getiter_", "_inplacevar_", "_unpack_sequence_", "_iter_unpack_sequence_", "log", "enumerate", "__safe_type__", "__instrument_binary_multiply__", "_print_"}
        disallowed_builtins = ["id"]

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

        self.globals['__builtins__']['_print_'] = self.print_call
        self.globals['__builtins__']['log'] = log_method
        self.globals['__builtins__']['type'] = type
        self.globals['__builtins__']['sum'] = sum
        self.globals['__builtins__']['OutOfBytecode'] = OutOfBytecode
        self.globals['__builtins__']['range'] = range
        self.globals['__builtins__']['__safe_type__'] = type
        self.globals['__builtins__']['enumerate'] = enumerate
        self.globals['__builtins__']['set'] = set
        self.globals['__builtins__']['frozenset'] = frozenset
        self.globals['__builtins__']['sorted'] = sorted

        for builtin in disallowed_builtins:
            del self.globals["__builtins__"][builtin]

        logger.debug("BUILTINS")
        for builtin in self.globals['__builtins__']:
            logger.debug(self.globals['__builtins__'][builtin])
            if builtin in not_instrumented_builtins:
                continue
            elif builtin in builtin_functions:
                instrumented_builtin = getattr(self.builtins, builtin)
                self.globals['__builtins__'][builtin] = instrumented_builtin(self.globals['__builtins__'][builtin])
            elif builtin in builtin_classes:
                # class methods/functions are instrumented using _getattr_
                continue
            elif builtin in builtin_errors:
                # errors are fine, there's nothing really resource intensive you can do with them
                continue
            elif builtin in builtin_instrumentation_artifacts:
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
            if object_type.__module__ != "builtins":
                return getattr(object, name, default)
            if object_type.__qualname__ == "module" and object.__name__ != "math":
                return getattr(object, name, default)
            logger.debug("ok gets here")
            real_attr = getattr(object, name, default)
            logger.debug("full name of attr: " + get_full_name(real_attr))
            if get_full_name(real_attr) not in {"builtins.builtin_function_or_method", "builtins.method_descriptor"}:
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
            if get_full_name(real_attr.__self__) == "builtins.module":
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
        except (KeyboardInterrupt, SystemError):
            # TODO: also handle other dangerous exceptions and decide what to do with them
            raise
        except:
            self.error_method(traceback.format_exc(limit=5))
        if not self.initialized:
            raise RobotRunnerError("Failed to initialize robot.")
        self.check_memory()

    def do_turn(self):
        if 'turn' in self.globals and isinstance(self.globals['turn'], type(lambda: 1)):
            try:
                exec(self.globals['turn'].__code__, self.globals, {})
            except (KeyboardInterrupt, SystemError):
                # TODO: also handle other dangerous exceptions and decide what to do with them
                raise
            except:
                self.error_method(traceback.format_exc(limit=5))
        else:
            self.error_method('Couldn\'t find turn function.')
        self.check_memory()

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
        if self.config.chess_clock_mechanism:
            self.bytecode = max(self.bytecode, 0) + self.config.bytecode_per_turn
        else:
            self.bytecode = self.config.bytecode_per_turn
        self.bytecode = min(self.config.max_bytecode, self.bytecode)

        if not self.initialized:
            self.init_robot()

        self.do_turn()

    def kill(self):
        pass
