import os, argparse

from malthusia import CodeContainer


def dir_filify(folder_name, dirfile_name):
    # Try to read contents of folder_name
    try:
        files = os.listdir(folder_name)
    except:
        if (folder_name.endswith('.py')):
            print(
                'It appears you have selected a python file, not a folder. Please enter the folder containing your bot.py')
        else:
            print('It appears you have not selected a valid folder')
        return

    # ensure there is 'bot.py' in folder_name
    if 'bot.py' not in files:
        print('It appears there is no \'bot.py\' in this folder')
        return

    files = [os.path.abspath(os.path.join(folder_name, f)) for f in os.listdir(folder_name) if
             f[-3:] == '.py' and os.path.isfile(os.path.join(folder_name, f))]

    code = {}
    for location in files:
        with open(location) as f:
            code[os.path.basename(location)] = f.read()

    dirfile = CodeContainer.directory_dict_to_dirfile(code)

    with open(dirfile_name, "w") as f:
        f.write(dirfile)

    print('Success! Upload {} through the online portal'.format(dirfile_name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('bot_name', help='The name of the bot you wish to flatten.')
    parser.add_argument('-o', '--output-file', default=None,
                        help="Output file! A txt file representing the directory code.")

    args = parser.parse_args()

    dirfile = args.output_file
    if dirfile is None:
        dirfile = args.bot_name.rstrip("/").split("/")[-1] + ".txt"

    dir_filify(args.bot_name, dirfile)
