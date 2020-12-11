"""Tests for the Compute Upgrade Agent testing the Compute Upgrade
Agent driver command.

Copyright 2019 Cray Inc. All rights Reserved.

"""
from crus.controller import driver


def test_help_option():
    """Test that the '--help' and '-h' options are recognized and result
    in a successful result code (0).

    """
    retval = driver(["--help"])
    assert retval == 0
    retval = driver(["-h"])
    assert retval == 0


def test_version_option():
    """Test that the '--version' option is recognized and results in a
    successful result code (0).

    """
    retval = driver(["--version"])
    assert retval == 0


def test_args_after_good_options():
    """Test that trying to run specifying excess arguments fails with an
    unsuccessful result code (!= 0).

    """
    retval = driver(["excess_arg"])
    assert retval != 0


def test_unknown_option():
    """Test that running an unknown option fails and returns an
    unsuccessful result code (!= 0).

    """
    retval = driver(["--no-such-option"])
    assert retval != 0
    retval = driver(["-z"])
    assert retval != 0
