# Copyright 2019, 2021 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

"""Tests for the Compute Upgrade Agent testing the Compute Upgrade
Agent driver command.

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
