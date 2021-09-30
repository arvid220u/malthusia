#!/usr/bin/env python3

"""
Build a map using the Google Sheets map builder.
1. Make a map in Google Sheets.
2. Copy the entire sheet to your clipboard.
3. Run `./gsheet.py`.
4. Maps will be dumped in the maps/ directory.
"""

from pandas.io.clipboard import clipboard_get
from malthusia.engine.game.location import InternalLocation
import json
import typer
import os


def main(force: bool = False):
    # Obtain input data
    gsheets = [line.split() for line in clipboard_get().split('\n')]

    # Parse map metadata
    _, name, _, symmetry, _, width, _, height, _, offset_x, _, offset_y = gsheets[0][:12]

    terrain = gsheets[2:]

    # output JSON!
    loc_list = []
    for row in terrain:
        y = int(row[0]) + int(offset_y)
        for ix, sq in enumerate(row[1:]):
            x = ix + int(offset_x)
            water = "W" in sq
            elevation = int(sq.strip("W") if len(sq.strip("W")) > 0 else "-10")
            loc = InternalLocation(x=x, y=y, elevation=elevation, water=water, robot=None, dead_robots=[])
            loc_list.append(loc)

    serialized = [loc.serialize() for loc in loc_list]
    for ser in serialized:
        del ser["robot"]
        del ser["dead_robots"]

    fname = f"malthusia/engine/game/maps/{name}.json"
    if not force and os.path.exists(fname):
        raise RuntimeError(f"Map {fname} already exists. Pass --force flag if you want to overwrite.")

    with open(fname, "w") as f:
        json.dump(serialized, f)

    print(f"Created map! {fname}")

if __name__ == "__main__":
    typer.run(main)
