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
"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

"""
import re
from crus.controllers.upgrade_agent.node_table import NodeTable
from crus.controllers.mocking.bss import BSSNodeTable

# some useful regular expressions...
XNAME_PATTERN = r"^x[0-9]+c[0-9]+s[0-9]+b[0-9]+n[0-9]+$"
NIDNAME_PATTERN = r"^nid[0-9][0-9][0-9][0-9][0-9][0-9]$"


def test_get_all_xnames():
    """Test getting all of the XNAMEs known to the NodeTable

    """
    xnames = NodeTable.get_all_xnames()
    assert isinstance(xnames, list)
    assert len(xnames) == BSSNodeTable.node_count()
    for xname in xnames:
        assert re.match(XNAME_PATTERN, xname)


def test_get_nid():
    """Test getting a NID for each node based on its XNAME and verify that
    all the name translations work for that nid.

    """
    xnames = NodeTable.get_all_xnames()
    for xname in xnames:
        nid = NodeTable.get_nid(xname)
        assert isinstance(nid, int)
        assert NodeTable.get_xname(nid) == xname
        nidname = NodeTable.get_nidname(xname)
        assert NodeTable.nidname_to_nid(nidname) == nid
