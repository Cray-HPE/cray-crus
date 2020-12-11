"""Node lists for setting up the BSS hosts data.  Each node list is
expressed as a 'discover' function that returns the list associated
with that configured type.  They are loaded by discover_nodes() in
'bss_nodes' which selects the right function based on the application
configuration setting BSS_NODE_LIST.

Copyright 2019, Cray Inc. All rights reserved.
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
