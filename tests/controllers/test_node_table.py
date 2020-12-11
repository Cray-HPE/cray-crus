"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

Copyright 2019 Cray Inc. All rights Reserved.

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
