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
"""Mock node data to support Compute Rolling Upgrade's Mock BSS
implementation.  Provides a means to set up the underlying node data
that is used by the mock HMS, mock WLM and mock BOSS modules.  This is
a minimal implementation to support specifically what is needed for
Compute Rolling Upgrade.  Extend it as needed to support new features.

"""
from importlib import import_module
from ....app import APP


def discover_nodes():
    """ Load configuration based on environment

    """
    node_lists = {
        "unit-test": "discover_unit_test",
        "preview": "discover_preview",
    }
    node_list_name = APP.config['BSS_NODE_LIST']
    node_list_module = import_module(".controllers.mocking.bss.node_list",
                                     package="crus")
    discover = getattr(node_list_module, node_lists[node_list_name])
    node_list = discover()
    return node_list


class Node:
    """ Class to hold node information for use by BOSS, HSM and WLM mocks.
    """
    def __init__(self, xname, nid):
        """ Constructor

        """
        self.xname = xname
        self.nid = nid
        self.fail_in_boot = False
        self.boot_failed = False

    def get_data(self):
        """Retrieve the BSS host data for this node.

        """
        state = "Ready" if not self.boot_failed else "Halt"
        flag = "OK" if not self.boot_failed else "Alert"
        data = {
            "ID": self.xname,
            "NID": self.nid,
            "State": state,
            "Flag": flag,
            "Type": "Node",       # don't use so it is fake and static
            "Enabled": True,      # don't use so it is fake and static
            "Role": "Compute",    # don't use so it is fake and static
            "NetType": "Sling",   # don't use so it is fake and static
            "Arch": "X86",        # don't use so it is fake and static
            "FQDN": "",           # don't use so it is fake and static
            "MAC": [              # don't use so it is fake and static
                "a4:bf:01:2c:f8:19",
                "a4:bf:01:2c:f8:1a"
            ]
        }
        return data

    def fail_boot(self):
        """Set the 'fail_in_boot' flag so that calls to boot() will return
        False indicating a failed boot.

        """
        self.fail_in_boot = True

    def pass_boot(self):
        """Clear the 'fail_in_boot' flag so that calls to boot() will return
        True indicating a successful boot.

        """
        self.fail_in_boot = False

    def boot(self):
        """"Boot" the node, indicating whether the boot succeeded or failed.

        """
        self.boot_failed = self.fail_in_boot
        return not self.boot_failed


class BSSNodeTable:
    """Singleton class to hold the list of known nodes (by XNAME) and
    mappings between NID and XNAME for use by other mocks that need to
    know about nodes.

    """
    _instance = None

    @classmethod
    def create(cls):
        """ Singleton table creator.
        """
        if cls._instance is None:
            cls._instance = cls()

    @classmethod
    def fail_boot(cls, xname):
        """Get a NID for a node based on its XNAME

        """
        cls._instance.nodes[xname].fail_boot()

    @classmethod
    def pass_boot(cls, xname):
        """Get a NID for a node based on its XNAME

        """
        cls._instance.nodes[xname].pass_boot()

    @classmethod
    def boot(cls, xname):
        """Get a NID for a node based on its XNAME

        """
        return cls._instance.nodes[xname].boot()

    @classmethod
    def get_all(cls):
        """Get a NID for a node based on its XNAME

        """
        ret = []
        for xname in cls._instance.nodes:
            ret.append(cls._instance.nodes[xname].get_data())
        return ret

    @classmethod
    def node_count(cls):
        """Return the number of nodes in the node table.

        """
        return len(cls._instance.nodes)

    @staticmethod
    def _discover_nodes():
        """Run run node discovery and build a list of Node objects from it.

        """
        return {xname: Node(xname, nid) for xname, nid in discover_nodes()}

    def __init__(self):
        """Constructor - nodecount specifies the number of nodes to create.
        Defaults to 2048.

        """
        self.nodes = self._discover_nodes()
