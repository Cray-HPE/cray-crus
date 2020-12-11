"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

Copyright 2019 Cray Inc. All rights Reserved.

"""
import sys
from crus.controllers.mocking.shared import shell


class MyTestCommand(shell.Command):
    """ Test command handler
    """
    def run(self, argv):
        """ Run method, dumps out the arguments that were passed in.
        """
        sys.stdout.flush()  # just to make sure flush gets called, coverage
        sys.stderr.flush()  # just to make sure flush gets called, coverage
        for arg in argv:
            print("%s" % arg)
        print("that's all", end='')
        return 0


def test_register_command():
    """Test registering a command.  This also sets up the later tests to
    use that command.

    """
    assert MyTestCommand("test_command")


def run_test_case(argv):
    """ Run a test case described by an argv list
    """
    argv = ["test_command"]
    cmd = shell.shell(argv)
    # pylint: disable=unnecessary-comprehension
    out = [line for line in cmd.output()]
    assert out[0:-1] == argv
    assert out[-1] == "that's all"


def test_command():
    """Test running a command with no arguments.

    """
    argv = ["test_command"]
    run_test_case(argv)


def test_command_with_args():
    """Test running a command with arguments.

    """
    argv = ["test_command", "argument 1", "argument 2", "argument 3"]
    run_test_case(argv)


def test_unregistered_command():
    """Test running a command with arguments.

    """
    argv = ["unknown_command"]
    cmd = shell.shell(argv)
    # pylint: disable=unnecessary-comprehension
    out = [line for line in cmd.output()]
    # pylint: disable=unnecessary-comprehension
    errs = [line for line in cmd.errors()]
    assert out == []
    assert errs != []
    assert errs[0] == "%s: command not found" % argv[0]
