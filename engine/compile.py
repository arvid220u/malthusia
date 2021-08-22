#!/usr/bin/env python

# utility tool to compile a program using the instrumenter

import typer
import sys
from malthusia.engine.container.instrument import Instrument
import importlib
import marshal
import dis
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

def main(filename: str, replace_builtins: bool = True, instrument: bool = True, instrument_binary_multiply: bool = True, reraise_dangerous_exceptions: bool = True):
    with open(filename, "r") as f:
        source = f.read()
    compiled_source = compile(source, filename, "exec")
    instrumented = Instrument.instrument(compiled_source, replace_builtins=replace_builtins, instrument=instrument, instrument_binary_multiply=instrument_binary_multiply, reraise_dangerous_exceptions=reraise_dangerous_exceptions)
    with open(filename + "c", 'wb') as fc:
        fc.write(code_to_bytecode(compiled_source))


if __name__ == "__main__":
    typer.run(main)
