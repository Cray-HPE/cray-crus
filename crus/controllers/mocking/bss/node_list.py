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
"""Node lists for setting up the BSS hosts data.  Each node list is
expressed as a 'discover' function that returns the list associated
with that configured type.  They are loaded by discover_nodes() in
'bss_nodes' which selects the right function based on the application
configuration setting BSS_NODE_LIST.

"""


def discover_unit_test():
    """Build a 2048 node system for unit testing purposes.

    """
    nodecount = 2048
    rack = 0
    nodes = 0
    node_list = []
    while nodes < nodecount:
        for cabinet in range(0, 4):
            for slot in range(0, 4):
                for node in range(0, 8):
                    xname = "x%dc%ds%db0n%d" % (rack, cabinet, slot, node)
                    node_list.append((xname, nodes + 1))
                    nodes += 1
        rack += 1
    return node_list


def discover_preview():
    """Build a 4 node system based on the preview system configuration for
    mocking a preview system.

    """
    node_list = [
        ("x0c0s28b0n0", 1),
        ("x0c0s26b0n0", 2),
        ("x0c0s24b0n0", 3),
        ("x0c0s21b0n0", 4)
    ]
    return node_list
