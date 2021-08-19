# snek

This repository contains all the code for the Battlecode Python engine.

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
