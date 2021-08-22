# snek

This repository contains all the code for the Malthusia engine, based on the [battlehack20 engine](https://github.com/battlecode/battlehack20/tree/master/engine) by MIT Battlecode.

## Installation and Usage

1. Install `poetry`.
2. Install Python 3.7.
3. `poetry env use python3.7`
4. `poetry shell`
5. `poetry install`

Test it out by running:

```bash
python run.py examplefuncsplayer examplefuncsplayer
```

(this needs to be after running `poetry shell`)

You should see a game between `examplefuncsplayer` and `examplefuncsplayer` being played.
If your code is in a directory `~/yourcode/coolplayer` then you can run it against examplefuncsplayer using

```
python run.py examplefuncsplayer ~/yourcode/coolplayer
```

### Testing

```
pytest
```

### Running Interactively

Run

```
python -i run.py examplefuncsplayer examplefuncsplayer
```

This will open an interactive Python shell. There, you can run

```
>>> step()
```

which advances the game 1 turn. This is very useful for debugging.


### Advanced Usage

Interacting directly with the `malthusia` API will give you more freedom and might make it easier to debug your code. The following is a minimal example of how to do that.

```
python
>>> import malthusia as m
>>> code = m.CodeContainer.from_directory('./examplefuncsplayer')
>>> game = m.Game([code, code], debug=True)
>>> game.turn()
```

You should see the output:
```
[Game info] Turn 1
[Game info] Queue: {}
[Game info] Lords: [<ROBOT WHITE HQ WHITE>, <ROBOT BLACK HQ BLACK>]
[Robot WHITE HQ log] Starting Turn!
[Robot WHITE HQ log] Team: Team.WHITE
[Robot WHITE HQ log] Type: RobotType.OVERLORD
[Robot WHITE HQ log] Bytecode: 4981
[Robot WHITE HQ log] Spawned unit at: (0, 0)
[Robot WHITE HQ log] done!
[Robot WHITE HQ info] Remaining bytecode: 4955
[Robot BLACK HQ log] Starting Turn!
[Robot BLACK HQ log] Team: Team.BLACK
[Robot BLACK HQ log] Type: RobotType.OVERLORD
[Robot BLACK HQ log] Bytecode: 4981
[Robot BLACK HQ log] Spawned unit at: (7, 6)
[Robot BLACK HQ log] done!
[Robot BLACK HQ info] Remaining bytecode: 4954
```

If you're curious, this is how the `run.py` script works. Study the source code of `run.py` to figure out how to set up a viewer.

## Bytecode Instrumentation

Helpful resource: https://towardsdatascience.com/understanding-python-bytecode-e7edaae8734d

The engine counts the number of bytecodes used by code. It does this by inserting a function call, `__increment__()`, in between every single bytecode (each function call requires 3 bytecodes, so this increases the code size by 4x).

Python bytecode post-3.6 consists of two bytes each. The first byte corresponds to the instruction, and the second byte to the argument. In case the argument needs to be bigger than one byte, additional `EXTENDED_ARG` are inserted before, containing the higher bits of the argument. At most 3 of them are allowed per instruction.

The bytecodes operate on a stack machine. That is, most operations are performed on the top x stack elements. Here is a list of all bytecode instructions: https://docs.python.org/3/library/dis.html#python-bytecode-instructions.

The bytecode instrumentation is not perfect, because many of the bytecodes are not constant time. For example, `BUILD_STRING(i)` concatenates `i` strings, which should probably cost `i` bytecodes and not 1 bytecode. But meh, seems relatively benign.

Note: `is_jump_target` is never set on the extended args, but always on the root instruction. However, the jump target is the extended args instruction.

### `sys.settrace` idea

Instead of modifying the bytecode directly, one could use `sys.settrace`. This might lead to a simpler and more robust implementation. See https://gist.github.com/j-mao/1d833c66fc72c773c28c6ecf272e4d02 for a proof of concept.

### Pause vs Error on Bytecode Limit

An initial version of the engine pauses code upon reaching the bytecode limit. This requires thread manipulation, and is sometimes confusing (the turn function is no longer atomic, so you have to think about interleaving issues), but makes for a nicer interface if you want to perform a one-time expensive computation.
Another option is to raise an exception when the limit is reached, and always restarting computation from the beginning of the turn function.