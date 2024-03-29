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
"""Direct tests for the Node Group support in the Compute Upgrade Agent

"""
from crus.controllers.upgrade_agent.node_group import NodeGroup
from crus.controllers.upgrade_agent.errors import ComputeUpgradeError
from crus.controllers.upgrade_agent.node_table import NodeTable


def test_create_same_node_group_twice():  # pylint: disable=invalid-name
    """Test that creating the same named node group twice in a row fails
    with an appropriate exception.

    """
    ng_name = "test-failed"
    ng_data = {
        'label': ng_name,
        'description': "Node group for failed nodes in test upgrade",
        'members': {'ids': []}
    }
    ngroup = NodeGroup(ng_data['label'], ng_data)

    try:
        second_ng = NodeGroup(ng_data['label'], ng_data)
        second_ng.delete()  # pragma unit test failure
        assert False  # pragma unit test failure
    except ComputeUpgradeError:
        pass

    # clean up
    ngroup.delete()


def test_create_node_group_with_tags():  # pylint: disable=invalid-name
    """Test that creating a node group with tags works.

    """
    ng_name = "test-failed"
    ng_data = {
        'label': ng_name,
        'description': "Node group for failed nodes in test upgrade",
        'tags': ['tag_1', 'tag_2', 'tag_3'],
        'members': {'ids': []}
    }
    ngroup = NodeGroup(ng_data['label'], ng_data)

    # Look for the tags...
    check_ng = NodeGroup(ng_data['label'])
    params = check_ng.get_params()
    assert 'label' in params
    assert params['label'] == ng_data['label']
    assert 'description' in params
    assert params['description'] == ng_data['description']
    assert 'tags' in params
    assert params['tags'] == ng_data['tags']
    assert 'members' in params
    assert 'ids' in params['members']
    assert params['members']['ids'] == []

    # clean up
    ngroup.delete()


def test_node_group_remove_missing_member():  # pylint: disable=invalid-name
    """Test that adding the same member to a node group twice in a row
    fails with an appropriate exception.

    """
    ng_name = "test-failed"
    ng_data = {
        'label': ng_name,
        'description': "Node group for failed nodes in test upgrade",
        'tags': ['tag_1', 'tag_2', 'tag_3'],
        'members': {'ids': []}
    }
    ngroup = NodeGroup(ng_data['label'], ng_data)

    xname = NodeTable.get_xname(1)
    try:
        ngroup.remove_member(xname)
        ngroup.delete()  # pragma unit test failure
        assert False  # pragma unit test failure
    except ComputeUpgradeError:
        pass

    # clean up
    ngroup.delete()


def test_delete_nonexistent_node_group():  # pylint: disable=invalid-name
    """Test that deleting a node group that does not exist failes
    appropriately.  Do this by creating a node group and then deleting
    it twice.

    """
    # Create the group
    ng_name = "test-non-existent"
    ng_data = {
        'label': ng_name,
        'description': "Node group for testing double delete",
        'tags': None,
        'members': {'ids': []}
    }
    ngroup = NodeGroup(ng_data['label'], ng_data)

    # Delete it once, which should work...
    ngroup.delete()

    # Try to delete it again which should fail
    try:
        ngroup.delete()
        assert False  # pragma unit test failure
    except ComputeUpgradeError:
        pass


def test_get_nonexistent_node_group():  # pylint: disable=invalid-name
    """Test that looking up a node group that does not exist fails
    appropriately.

    """
    # Create the group
    ng_name = "test-non-existent"
    # Try to delete it again which should fail
    try:
        NodeGroup(ng_name)
        assert False  # pragma unit test failure
    except ComputeUpgradeError:
        pass
