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
"""Node data to support Compute Rolling Upgrade.  Provides mappings
between different naming methods (XNAME, NID, NID Name) for nodes.

"""
import re
from ..bss_hosts import BSSHostTable


class NodeTable:
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
    def get_nid(cls, xname):
        """Get a NID for a node based on its XNAME

        """
        cls.create()
        return cls._instance.nids_by_xname[xname]

    @classmethod
    def get_nidname(cls, xname):
        """Get a NID based name for a node based on its XNAME

        """
        cls.create()
        nid = cls._instance.nids_by_xname[xname]
        return "nid%6.6d" % nid

    @classmethod
    def get_xname(cls, nid):
        """Get an XNAME for a node based on its NID

        """
        cls.create()
        return cls._instance.xnames_by_nid[nid]

    @classmethod
    def get_all_xnames(cls):
        """ Get the list of all recognized XNAMEs in the NodeTable.

        """
        cls.create()
        # Comprehension used here to avoid returning the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        return [xname for xname in cls._instance.nodes]

    @staticmethod
    def nidname_to_nid(nidname):
        """Translate a nidname of the form 'nidNNNNNN' into the integer NID
        that it represents.

        """
        pat = r"^nid(?P<nid>[0-9]+)$"
        match = re.match(pat, nidname)
        return int(match.group('nid'), 10)

    @staticmethod
    def _learn_nodes():
        """Learn the node list from the BSS

        """
        host_table = BSSHostTable()
        xnames = host_table.get_all_xnames()
        nodes = {xname: host_table.get_nid(xname) for xname in xnames
                 if host_table.get_role(xname) == "Compute"}
        return nodes

    def __init__(self):
        """Constructor

        """
        self.nodes = self._learn_nodes()
        self.nids_by_xname = {}
        self.xnames_by_nid = {}
        for xname in self.nodes:
            nid = self.nodes[xname]
            self.nids_by_xname[xname] = nid
            self.xnames_by_nid[nid] = xname
