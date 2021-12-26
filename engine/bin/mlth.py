#!/usr/bin/env python3

"""
The malthusia command line tool!
"""
import binascii

import typer
import os
import faulthandler
import errno
import json
import sys
import marshal
import dis
from types import CodeType
from typing import List, Optional
import struct

from malthusia import CodeContainer, Game, GameConstants
from malthusia.engine.container.instrument import Instrument

app = typer.Typer()


@app.command()
def prepare(bots: List[str], action_file: str, robot_type: Optional[List[int]] = None,
            round: Optional[List[int]] = None, creator: str = "player", append: bool = False):
    """
    combine flatten and genactions
    """
    flattened_bots = []
    for bot in bots:
        flattened_bots.append(flatten(bot))
    genactions(flattened_bots, action_file, robot_type, round, creator, append)



@app.command()
def genactions(flattened_bots: List[str], action_file: str, robot_type: Optional[List[int]] = None,
               round: Optional[List[int]] = None, creator: str = "player", append: bool = False):
    actions = []

    if not robot_type:
        robot_type = [0 for _ in flattened_bots]
    elif len(robot_type) != len(flattened_bots):
        raise typer.BadParameter("must specify robot types for all robots")
    if not round:
        round = [1 for _ in flattened_bots]
    elif len(round) != len(flattened_bots):
        raise typer.BadParameter("must specify round for all robots")

    for i, bot in enumerate(flattened_bots):
        with open(bot, "r") as f:
            code = f.read()
        action = {
            "type": "new_robot",
            "round": round[i],
            "robot_type": robot_type[i],
            "creator": creator,
            "uid": binascii.b2a_hex(os.urandom(4)).decode('utf-8'),
            "code": code,
        }
        actions.append(action)

    with open(action_file, "w" if not append else "a") as f:
        f.write("\n".join([json.dumps(action) for action in actions]))


@app.command()
def run(bots: Optional[List[str]] = typer.Argument(None), action_file: Optional[str] = None, output_file: str = None,
        map_file: str = None, raw_text: bool = False, seed: int = GameConstants.DEFAULT_SEED, debug: bool = True, stdin_turn: bool = False):
    global game
    # The faulthandler makes certain errors (segfaults) have nicer stacktraces.
    faulthandler.enable()

    if len(bots) > 0 and action_file is not None:
        raise ValueError(
            "Cannot read both from bots and an action file, because the bots will overwrite the action file.")
    if len(bots) == 0 and action_file is None:
        raise typer.BadParameter("Need to specify either bots or an action-file. Run --help for more info.")

    if action_file is None:
        action_file = "actions.jsonl"
        prepare(bots=bots, action_file=action_file)

    # the round delimiter is a string that can never appear inside a valid JSON file.
    # each round will start and end with this string
    ROUND_PADDING = '""""'

    def replay_saver(serialized_map):
        # TODO: fail more nicely on ctrl-c (don't want to corrupt the file)
        if output_file is not None:
            with open(output_file, "a") as f:
                f.write(ROUND_PADDING)
                json.dump(serialized_map, f)
                f.write(ROUND_PADDING)

    game_args = {}
    if map_file is not None:
        game_args["map_file"] = map_file

    if output_file is not None:
        # overwrite the replay file
        try:
            os.remove(output_file)
        except OSError as e:  # this would be "except OSError, e:" before Python 2.6
            if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
                raise  # re-raise exception if a different error occurred

    # This is how you initialize a game,
    game = Game(action_file, seed=seed, debug=debug, colored_logs=not raw_text,
                round_callback=replay_saver,
                **game_args)

    # Here we check if the script is run using the -i flag.
    # If it is not, then we simply play the entire game.
    if not sys.flags.interactive:
        while True:
            if stdin_turn:
                input()
            game.turn()
    else:
        # print out help message!
        print("Run game.turn() to step through the game.")


@app.command()
def flatten(bot_folder: str, output_file: str = None):
    if output_file is None:
        output_file = bot_folder.rstrip("/").split("/")[-1] + ".txt"

    # Try to read contents of bot_folder
    try:
        files = os.listdir(bot_folder)
    except FileNotFoundError:
        if bot_folder.endswith('.py'):
            print(
                'It appears you have selected a python file, not a folder. Please enter the folder containing your bot.py')
        else:
            print('It appears you have not selected a valid folder')
        return

    # ensure there is 'bot.py' in bot_folder
    if 'bot.py' not in files:
        print('It appears there is no \'bot.py\' in this folder')
        return

    files = [os.path.abspath(os.path.join(bot_folder, f)) for f in os.listdir(bot_folder) if
             f[-3:] == '.py' and os.path.isfile(os.path.join(bot_folder, f))]

    code = {}
    for location in files:
        with open(location) as f:
            code[os.path.basename(location)] = f.read()

    dirfile = CodeContainer.directory_dict_to_dirfile(code)

    with open(output_file, "w") as f:
        f.write(dirfile)

    return output_file


# inspired by https://gist.github.com/stecman/3751ac494795164efa82a683130cabe5
def _pack_uint32(val):
    """ Convert integer to 32-bit little-endian bytes """
    return struct.pack("<I", val)


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


def code_to_bytecode(code, mtime=0, source_size=0):
    """
    Serialise the passed code object (PyCodeObject*) to bytecode as a .pyc file
    The args mtime and source_size are inconsequential metadata in the .pyc file.
    """

    # Get the magic number for the running Python version
    if sys.version_info >= (3, 4):
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
    if sys.version_info >= (3, 7):
        # Blank bit field value to indicate traditional pyc header
        data.extend(_pack_uint32(0))

    data.extend(_pack_uint32(int(mtime)))

    # Handle extra 32-bit field for source size from Python 3.2 onwards
    # See: https://www.python.org/dev/peps/pep-3147/
    if sys.version_info >= (3, 2):
        data.extend(_pack_uint32(source_size))

    data.extend(marshal.dumps(code))

    return data


@app.command()
def instrument(filename: str, replace_builtins: bool = True, instrument: bool = True,
               instrument_binary_multiply: bool = True,
               reraise_dangerous_exceptions: bool = True, write_dis: bool = True):
    with open(filename, "r") as f:
        source = f.read()
    compiled_source = compile(source, filename, "exec")
    instrumented = Instrument.instrument(compiled_source, replace_builtins=replace_builtins, instrument=instrument,
                                         instrument_binary_multiply=instrument_binary_multiply,
                                         reraise_dangerous_exceptions=reraise_dangerous_exceptions)
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


if __name__ == "__main__":
    try:
        app()
    except SystemExit as e:
        if e.code != 0:
            raise
