import os, argparse
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('code_file', help='The filename of the bot you want to create an action for.')

    args = parser.parse_args()

    output = "actions.jsonl"

    with open(args.code_file, "r") as f:
        code = f.read()

    action = {
        "type": "new_robot",
        "round": 1,
        "code": code,
        "robot_type": 0,
        "creator": "arvid",
        "uid": "this_is_a_unique_id"
    }

    with open(output, "w") as f:
        f.writelines([json.dumps(action)])
