#
# MIT License
#
# (C) Copyright 2019, 2021-2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
"""Mock shell support for Compute Rolling Upgrade, patterned on the
'shell' python library (https://pypi.org/project/shell).  This is a
minimal implementation to support specifically what is needed for
Compute Rolling Upgrade.  Extend it as needed to support new features.

"""
import sys


class CommandRegistry:
    """Static class for internal use that holds a mapping from commands
    (argv[0] values) to their handlers.

    """
    registered_commands = {}

    @staticmethod
    def register(cmd_name, handler):
        """Register a command with a handler for future use with shell()
        calls.

        """
        CommandRegistry.registered_commands[cmd_name] = handler

    @staticmethod
    def find(cmd_name):
        """Look up a candidate command in registered_commands and return it's
        handler.  If the command is not present, return None.

        """
        if cmd_name not in CommandRegistry.registered_commands:
            return None
        return CommandRegistry.registered_commands[cmd_name]


class Command:
    """Command handler base class, registers itself with the
    CommandRegistry to permit use of the shell() call below.  Provides
    an abstract run() method overridden by derived handlers which is
    called by shell().

    """
    def __init__(self, cmd_name):
        """Constructor

        """
        CommandRegistry.register(cmd_name, self)

    def run(self, argv):  # pragma abstract method
        """Abstract run method.  Override this in your command.

        """
        raise NotImplementedError


class CommandOutput:
    """Fake 'file' class to replace stdout or stderr, enough to handle
    'write' calls (supports print or x.write()).

    """
    def __init__(self):
        """Constructor

        """
        self.debug = ""
        self.lines = []
        self.cur_line = ""

    def __iter__(self):
        """Iterator

        """
        return self

    def __next__(self):
        """Iterator support, return the next line from self.lines

        """
        if not self.lines:
            if not self.cur_line:
                raise StopIteration
            ret = self.cur_line
            self.cur_line = ""
            return ret
        return self.lines.pop(0)

    def write(self, string):
        """Write method, captures the output in an iterable place.

        """
        self.cur_line += string
        lines = self.cur_line.split('\n')
        self.lines.extend(lines[:-1])
        self.cur_line = lines[-1]

    def flush(self):
        """Flush method, do nothing, everything is already flushed.

        """
        return


class StdioRedirect:
    """Context manager for handling stdout and stderr redirection for
    commands.  Redirects to the specified 'out' and 'err' objects on
    context entry, restores previous stdout and stderr on context
    exit.

    """
    def __init__(self, out, err):
        """ Constructor
        """
        self.saved_out = sys.stdout
        self.saved_err = sys.stderr
        self.out = out
        self.err = err

    def __enter__(self):
        """Enter function for starting the with block. Redirects stdout and
        stderr as specified in the constructor.

        """
        sys.stdout = self.out
        sys.stderr = self.err

    # pylint: disable=unused-argument
    def __exit__(self, exctype, excvalue, traceback):
        """Exit function for terminating the with block.  Restores stdout and
        stderr to what they were.

        """
        sys.stdout = self.saved_out
        sys.stderr = self.saved_err
        return False


class Shell:
    """ Mock Shell class modeled on the shell python library

    """
    def __init__(self, argv):
        """Constructor

        """
        self.argv = argv
        self.handler = CommandRegistry.find(argv[0])
        self.out = []
        self.err = []

    def run_cmd(self):
        """Run the command attached to this Shell object redirecting stdout
        and stderr in to fake files so we can easily report their
        output form the output() method.

        """
        # Toss any previous output and errors that might be present so
        # we only get the output from this run.
        self.out = CommandOutput()
        self.err = CommandOutput()
        # Switch stdout and stdderr so we capture what is produced on each.
        with StdioRedirect(self.out, self.err):
            if self.handler is None:
                print("%s: command not found" % self.argv[0], file=sys.stderr)
                return
            self.handler.run(self.argv)

    def output(self):
        """ Report the output produced by the command.
        """
        for out in self.out:
            yield out

    def errors(self):
        """ Report the output produced by the command.
        """
        for err in self.err:
            yield err


def shell(argv):
    """Mock shell() function patterned on the shell() function from the
    'shell' library.  This implements only the 'list' form of a
    command because that is all that I use in the caller.

    """
    assert isinstance(argv, list)
    ret = Shell(argv)
    ret.run_cmd()
    return ret
