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

"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

"""
import re
from importlib import import_module
from crus.controllers.mocking.bss import BSSNodeTable

# some useful regular expressions...
XNAME_PATTERN = r"^x[0-9]+c[0-9]+s[0-9]+b[0-9]+n[0-9]+$"


def validate_node_data(node):
    """Verify that a node data block is of the right form and has
    reasonable content.

    """
    assert 'ID' in node
    assert re.match(XNAME_PATTERN, node['ID'])
    assert 'Type' in node
    assert node['Type'] == "Node"
    assert 'State' in node
    assert 'Flag' in node
    assert 'Enabled' in node
    assert node['Enabled']
    assert 'Role' in node
    assert node['Role'] == "Compute"
    assert 'NID' in node
    assert isinstance(node['NID'], int)
    assert 'NetType' in node
    assert node['NetType'] == "Sling"
    assert 'Arch' in node
    assert node['Arch'] == "X86"
    assert 'FQDN' in node
    assert 'MAC' in node
    assert isinstance(node['MAC'], list)
    assert node['MAC'] != []


def test_node_list():
    """Test the node list initialization feature to be sure it supports
    all known node list configurations and they produce valid node
    lists.

    """
    node_list_module = import_module(".mocking.bss.node_list",
                                     package="crus.controllers")
    discover_names = [name for name in node_list_module.__dict__
                      if name[:9] == "discover_"]
    for name in discover_names:
        discover = getattr(node_list_module, name)
        node_list = discover()
        assert isinstance(node_list, list)
        for node in node_list:
            assert isinstance(node, tuple)
            assert len(node) == 2
            assert re.match(XNAME_PATTERN, node[0])
            assert isinstance(node[1], int)


def test_get_all():
    """Test getting data for all nodes in the BSS node table

    """
    nodes = BSSNodeTable.get_all()
    assert nodes is not None
    assert len(nodes) == BSSNodeTable.node_count()
    for node in nodes:
        validate_node_data(node)


def test_node_boot_fail_and_pass():
    """Test setting nodes to fail in boot and trying to boot them then
    setting them to pass in boot and trying to boot them.

    """
    nodes = BSSNodeTable.get_all()
    xnames = [node['ID'] for node in nodes]
    for xname in xnames:
        BSSNodeTable.fail_boot(xname)
        assert not BSSNodeTable.boot(xname)
        BSSNodeTable.pass_boot(xname)
        assert BSSNodeTable.boot(xname)
