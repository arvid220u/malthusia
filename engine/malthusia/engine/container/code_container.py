import re
import os
from .instrument import Instrument

import marshal, pickle
from ..restrictedpython import compile_restricted


class CodeContainer:
    """
    CodeContainer compiles a given directory, and instruments the code. It is then used as the code
    object representing a robot's code, to be run by a RobotRunner.
    """

    def __init__(self, code):
        self.code = code

    @classmethod
    def directory_dict_to_dirfile(cls, dirdict):
        dirfile = ""
        for idx, file in enumerate(dirdict):
            if idx > 0:
                dirfile += "\n"
            num_lines = len(dirdict[file].strip("\n").split("\n"))
            separator = "=============="
            dirfile += f"{file}, {num_lines} lines\n" + separator + "\n"
            dirfile += dirdict[file].strip("\n") + "\n" + separator + "\n"
        return dirfile

    @classmethod
    def dirfile_to_directory_dict(cls, dirfile):
        dirdict = {}
        lines = dirfile.split("\n")
        i = 0
        while i < len(lines):
            name = lines[i].split(" ")[0].rstrip(",")
            nlines = int(lines[i].split(" ")[1])
            filelines = []
            for j in range(i + 2, i + 2 + nlines):
                filelines.append(lines[j])
            file = "\n".join(filelines)
            dirdict[name] = file
            i = i + 2 + nlines + 2
        return dirdict

    @classmethod
    def from_directory_dict(cls, dic):
        code = {}

        for filepath in dic:
            module_name = os.path.basename(filepath).split('.py')[0]
            compiled = compile_restricted(cls.preprocess(dic[filepath]), filepath, 'exec')
            code[module_name] = Instrument.instrument(compiled)

        return cls(code)

    @classmethod
    def from_dirfile(cls, dirfile):
        directory_dict = cls.dirfile_to_directory_dict(dirfile)

        return cls.from_directory_dict(directory_dict)

    @classmethod
    def from_directory(cls, dirname):
        files = [os.path.abspath(os.path.join(dirname, f)) for f in os.listdir(dirname) if
                 f[-3:] == '.py' and os.path.isfile(os.path.join(dirname, f))]

        code = {}
        for location in files:
            with open(location) as f:
                code[location] = f.read()

        return cls.from_directory_dict(code)

    def to_bytes(self):
        packet = {}
        for key in self.code:
            packet[key] = marshal.dumps(self.code[key])

        return pickle.dumps(packet)

    @classmethod
    def from_bytes(cls, codebytes):
        packet = pickle.loads(codebytes)

        for key in packet:
            packet[key] = marshal.loads(packet[key])

        return cls(packet)

    def to_file(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.to_bytes())

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            return cls.from_bytes(cls.preprocess(f.read()))

    @classmethod
    def package_name(cls):
        return cls.__module__.split(".", 1)[0]

    @classmethod
    def preprocess(cls, content):
        """
        Strips package.stubs imports from the code.

        It removes lines containing one of the following imports:
        - from package.stubs import *
        - from package.stubs import a, b, c

        The regular expression that is used also supports non-standard whitespace styles like the following:
        - from package.stubs import a,b,c
        - from  package.stubs  import  a,  b,  c

        Go to https://regex101.com/r/bhAqFE/6 to test the regular expression with custom input.
        """

        pattern = r'^([ \t]*)from([ \t]+)' + cls.package_name() + r'\.stubs([ \t]+)import([ \t]+)(\*|([a-zA-Z_]+([ \t]*),([ \t]*))*[a-zA-Z_]+)([ \t]*)$'

        # Replace all stub imports
        while True:
            match = re.search(pattern, content, re.MULTILINE)

            if match is None:
                break

            # Remove the match from the content
            start = match.start()
            end = match.end()
            content = content[0:start] + content[end:]

        return content

    def __getitem__(self, key):
        return self.code[key]

    def __contains__(self, key):
        return key in self.code
