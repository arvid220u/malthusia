import argparse
import faulthandler
import sys
import threading
import json
import os
import errno

from malthusia import CodeContainer, Game, GameConstants, RobotType


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:  # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT:  # errno.ENOENT = no such file or directory
            raise  # re-raise exception if a different error occurred


"""
This is a simple script for running bots and debugging them.

Feel free to change this script to suit your needs!

Usage:

    python3 run.py examplefuncsplayer

        Runs examplefuncsplayer against itself. (You can omit the second argument if you want to.)

    python3 -i run.py examplefuncsplayer examplefuncsplayer

        Launches an interactive shell where you can step through the game using step().
        This is great for debugging.
    
    python3 -i run.py examplefuncsplayer exampelfuncsplayer --debug false

        Runs the script without printing logs. Instead shows the viewer in real time.

    python3 run.py -h

        Shows a help message with more advanced options.
"""


def step(number_of_turns=1):
    """
    This function steps through the game the specified number of turns.
    """

    for i in range(number_of_turns):
        game.turn()


def play_all(delay=0.8, keep_history=False, real_time=False, viewer=False):
    """
    This function plays the entire game, and views it in a nice animated way.

    If played in real time, make sure that the game does not print anything.
    """

    if real_time and viewer:
        viewer_poison_pill = threading.Event()
        viewer_thread = threading.Thread(target=viewer.play_synchronized, args=(viewer_poison_pill,),
                                         kwargs={'delay': delay, 'keep_history': keep_history})
        viewer_thread.daemon = True
        viewer_thread.start()

    try:
        while True:
            game.turn()
    finally:
        if real_time and viewer:
            viewer_poison_pill.set()
            viewer_thread.join()
        elif viewer:
            viewer.play(delay=delay, keep_history=keep_history)


# the round delimiter is a string that can never appear inside a valid JSON file.
# each round will start and end with this string
ROUND_PADDING = '""""'


def replay_saver(serialized_map):
    # TODO: fail more nicely on ctrl-c (dont wanna corrupt the file)
    if replay_file is not None:
        with open(replay_file, "a") as f:
            f.write(ROUND_PADDING)
            json.dump(serialized_map, f)
            f.write(ROUND_PADDING)


if __name__ == '__main__':

    # This is just for parsing the input to the script. Not important.
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw-text', action='store_true',
                        help="Makes playback text-only by disabling colors and cursor movements.")
    parser.add_argument('--delay', default=0.8, help="Playback delay in seconds.")
    parser.add_argument('--debug', default='true', choices=('true', 'false'),
                        help="In debug mode (defaults to true), bot logs and additional information are displayed.")
    parser.add_argument('--map-file', default=None, help="Path to map file")
    parser.add_argument('--action-file', default="actions.jsonl", help="Path to action file")
    parser.add_argument('--seed', default=GameConstants.DEFAULT_SEED, type=int,
                        help="Override the seed used for random.")
    parser.add_argument('--view-box', default=10, help="max coordinate value in viewer")
    parser.add_argument('--viewer', default=False, help="whether to show viewer")
    parser.add_argument('-o', '--output-file', default=None,
                        help="Output file! A gzipped json replay file that will be streamed to.")
    args = parser.parse_args()
    args.debug = args.debug == 'true'

    # The faulthandler makes certain errors (segfaults) have nicer stacktraces.
    faulthandler.enable()

    # This is where the interesting things start!

    game_args = {}
    if args.map_file is not None:
        game_args["map_file"] = args.map_file

    replay_file = args.output_file
    if replay_file is not None:
        # overwrite the replay file
        silentremove(replay_file)

    # This is how you initialize a game,
    game = Game(args.action_file, seed=args.seed, debug=args.debug, colored_logs=not args.raw_text,
                round_callback=replay_saver,
                **game_args)

    # ... and the viewer.
    # view_box = (-args.view_box, args.view_box, args.view_box, -args.view_box)
    # viewer = BasicViewer(view_box, game.map_states, colors=not args.raw_text)

    # Here we check if the script is run using the -i flag.
    # If it is not, then we simply play the entire game.
    if not sys.flags.interactive:
        play_all(delay=float(args.delay), keep_history=args.raw_text, real_time=not args.debug, viewer=args.viewer)

    else:
        # print out help message!
        print("Run step() to step through the game.")
        print("You also have access to the variables: game, viewer")
