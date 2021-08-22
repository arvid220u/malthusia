#!/usr/bin/env python

# utility tool to compile a program using the instrumenter

import typer
import sys
from malthusia.engine.container.instrument import Instrument
import importlib
import marshal
import dis
from types import CodeType
import struct

# inspired by https://gist.github.com/stecman/3751ac494795164efa82a683130cabe5
def _pack_uint32(val):
    """ Convert integer to 32-bit little-endian bytes """
    return struct.pack("<I", val)
def code_to_bytecode(code, mtime=0, source_size=0):
    """
    Serialise the passed code object (PyCodeObject*) to bytecode as a .pyc file
    The args mtime and source_size are inconsequential metadata in the .pyc file.
    """

    # Get the magic number for the running Python version
    if sys.version_info >= (3,4):
        from importlib.util import MAGIC_NUMBER
    else:
        import imp
        MAGIC_NUMBER = imp.get_magic()

    # Add the magic number that indicates the version of Python the bytecode is for
    #
    # The .pyc may not decompile if this four-byte value is wrong. Either hardcode the
    # value for the target version (eg. b'\x33\x0D\x0D\x0A' instead of MAGIC_NUMBER)
    # or see trymagicnum.py to step through different values to find a valid one.
    data = bytearray(MAGIC_NUMBER)

    # Handle extra 32-bit field in header from Python 3.7 onwards
    # See: https://www.python.org/dev/peps/pep-0552
    if sys.version_info >= (3,7):
        # Blank bit field value to indicate traditional pyc header
        data.extend(_pack_uint32(0))

    data.extend(_pack_uint32(int(mtime)))

    # Handle extra 32-bit field for source size from Python 3.2 onwards
    # See: https://www.python.org/dev/peps/pep-3147/
    if sys.version_info >= (3,2):
        data.extend(_pack_uint32(source_size))

    data.extend(marshal.dumps(code))

    return data

def main(filename: str, replace_builtins: bool = True, instrument: bool = True, instrument_binary_multiply: bool = True, reraise_dangerous_exceptions: bool = True, write_dis: bool = True):
    with open(filename, "r") as f:
        source = f.read()
    compiled_source = compile(source, filename, "exec")
    instrumented = Instrument.instrument(compiled_source, replace_builtins=replace_builtins, instrument=instrument, instrument_binary_multiply=instrument_binary_multiply, reraise_dangerous_exceptions=reraise_dangerous_exceptions)
    with open(filename + "c", 'wb') as fc:
        fc.write(code_to_bytecode(instrumented))
    typer.echo(f"wrote binary instrumented code to {filename}c")
    with open(filename + "c.original", 'wb') as fc:
        fc.write(code_to_bytecode(compiled_source))
    typer.echo(f"wrote binary original code to {filename}c.original")
    if write_dis:
        with open(filename + "h", 'w') as fc:
            dis.dis(instrumented, file=fc)
        typer.echo(f"wrote human readable instrumented code to {filename}h")
        with open(filename + "h.original", 'w') as fc:
            dis.dis(compiled_source, file=fc)
        typer.echo(f"wrote human readable original code to {filename}h.original")

    print_codetype(instrumented)
    for const in instrumented.co_consts:
        if type(const) == CodeType:
            print_codetype(const)
        

def print_codetype(instrumented):
    print(instrumented.co_argcount)
    print(instrumented.co_posonlyargcount)
    print(instrumented.co_kwonlyargcount)
    print(instrumented.co_nlocals)
    print(instrumented.co_stacksize)
    print(instrumented.co_flags)
    print(instrumented.co_code)
    print(instrumented.co_consts)
    print(instrumented.co_names)
    print(instrumented.co_varnames)
    print(instrumented.co_filename)
    print(instrumented.co_name)
    print(instrumented.co_firstlineno)
    print(instrumented.co_lnotab)
    print(instrumented.co_freevars)
    print(instrumented.co_cellvars)

if __name__ == "__main__":
    typer.run(main)
