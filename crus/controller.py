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

"""Application driver that launches the controller (CRUA) part of the
CRUS service.

"""
import sys
from getopt import getopt, GetoptError
from crus import (
    API_VERSION,
    VERSION,
    watch_sessions,
    ComputeUpgradeError
)

USAGE_STATIC = """
Usage: driver
       driver --help|-h
       driver --version

Where:

    --help|-h

        Prints this message on stadard error and exits.

    --version

        Prints version information on standard output and exits.
"""


def usage(err=None, retval=1):
    """Print the usage message and an optional error message and, unless
    retval is explicitly set, return 1 to indicate failure.  If retval
    is set, return retval.

    """
    output = USAGE_STATIC
    if err:
        output = "%s\n%s" % (err, USAGE_STATIC)
    print(output, file=sys.stderr, flush=True)
    return retval


def version():
    """Print the version information and return 0

    """
    print("Compute Upgrade Agent version is: %s\n"
          "Compute Upgrade Agent API Version is: %s" % (VERSION, API_VERSION))
    return 0


def driver(argv):
    """Parse and validate arguments and execute the requested compute
    upgrade session or demo.

    """
    shortopts = "h"
    longopts = [
        "help",
        "version"
    ]
    try:
        opts, args = getopt(argv, shortopts, longopts)
    except GetoptError as exc:
        return usage(str(exc))
    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            return usage(retval=0)
        if opt[0] == "--version":
            return version()

    # There should be no arguments...
    if args != []:
        return usage("Compute Upgrade takes no non-option arguments")

    try:  # pragma no unit test (this code never returns, can't test here)
        # Start the controller loop
        watch_sessions()
    except ComputeUpgradeError as exc:  # pragma no unit test
        print(
            "An error occurred while processing upgrades - %s" % str(exc),
            file=sys.stderr, flush=True
        )
        return 1

    # All good, return success.
    return 0  # pragma no unit test (can't really reach this code)


if __name__ == '__main__':  # pragma no cover
    sys.exit(driver(sys.argv[1:]))
