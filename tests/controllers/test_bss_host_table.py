"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

Copyright 2019 Cray Inc. All rights Reserved.

"""
import re
from crus.controllers.upgrade_agent.bss_hosts import BSSHostTable
from crus.controllers.mocking.bss import BSSNodeTable

# some useful regular expressions...
XNAME_PATTERN = r"^x[0-9]+c[0-9]+s[0-9]+b[0-9]+n[0-9]+$"
NIDNAME_PATTERN = r"^nid[0-9][0-9][0-9][0-9][0-9][0-9]$"


def test_bss_hosts():
    """Test getting all of the XNAMEs known to the NodeTable

    """
    host_table = BSSHostTable()
    xnames = host_table.get_all_xnames()
    assert isinstance(xnames, list)
    assert len(xnames) == BSSNodeTable.node_count()
    for xname in xnames:
        assert re.match(XNAME_PATTERN, xname)
        assert isinstance(host_table.get_nid(xname), int)
        assert isinstance(host_table.get_role(xname), str)
        assert isinstance(host_table.get_state(xname), str)
        assert isinstance(host_table.get_flag(xname), str)
        assert isinstance(host_table.get_enabled(xname), bool)
