"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

Copyright 2019 Cray Inc. All rights Reserved.

"""
from crus.controllers.upgrade_agent.node_table import NodeTable
from crus.app import APP, HEADERS
from crus.controllers.mocking.shared import requests

BASE_URI = APP.config['NODE_GROUP_URI']
NODE_GROUPS_URI = BASE_URI
NODE_GROUP_URI = "%s/%%s" % BASE_URI
NODE_GROUP_MEMBERS_URI = "%s/%%s/members" % BASE_URI
NODE_GROUP_MEMBER_URI = "%s/%%s/members/%%s" % BASE_URI
HTTPS_VERIFY = APP.config['HTTPS_VERIFY']


def test_node_group():
    """Test creation of a node group with no members in it, then delete it.

    """
    # Create the group
    label = "test_group"
    create_uri = NODE_GROUPS_URI
    data = {
        'label': label,
        'description': "My test group",
        'tags': ['a tag'],
        'members': {'ids': []}
    }
    result = requests.post(create_uri, json=data,
                           headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['created']

    # Verify the initial contents
    get_uri = NODE_GROUP_URI % label
    result = requests.get(get_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['ok']
    result_data = result.json()
    assert 'label' in result_data
    assert result_data['label'] == data['label']
    assert 'description' in result_data
    assert result_data['description'] == data['description']
    assert 'members' in result_data
    assert result_data['members'] == data['members']

    # Add some XNAMEs to the group
    some_xnames = NodeTable.get_all_xnames()[:50]
    for xname in some_xnames:
        member_data = {
            'id': xname
        }
        add_member_uri = NODE_GROUP_MEMBERS_URI % label
        result = requests.post(add_member_uri, json=member_data,
                               headers=HEADERS, verify=HTTPS_VERIFY)
        assert result.status_code == requests.codes['created']

    # Verify that the members got added...
    result = requests.get(get_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['ok']
    result_data = result.json()
    assert 'label' in result_data
    assert result_data['label'] == data['label']
    assert 'description' in result_data
    assert result_data['description'] == data['description']
    assert 'members' in result_data
    assert 'ids' in result_data['members']
    member_xnames = result_data['members']['ids']
    for xname in member_xnames:
        assert xname in some_xnames
    for xname in some_xnames:
        assert xname in member_xnames

    # Delete all the members that we added...
    for xname in some_xnames:
        delete_member_uri = NODE_GROUP_MEMBER_URI % (label, xname)
        result = requests.delete(delete_member_uri, headers=HEADERS,
                                 verify=HTTPS_VERIFY)
        assert result.status_code == requests.codes['ok']

    # Verify that the members got deleted (we should be back where we were
    # right after creation)
    result = requests.get(get_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['ok']
    result_data = result.json()
    assert 'label' in result_data
    assert result_data['label'] == data['label']
    assert 'description' in result_data
    assert result_data['description'] == data['description']
    assert 'members' in result_data
    assert result_data['members'] == data['members']

    # Delete the group
    delete_uri = NODE_GROUP_URI % label
    result = requests.delete(delete_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['ok']

    # Make sure it is gone
    result = requests.get(get_uri, json=data,
                          headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['not_found']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Not Found"
    assert 'detail' in result_data
    assert 'status' in result_data
    assert result_data['status'] == result.status_code


# pylint: disable=invalid-name
def test_fail_create_node_group_no_input():
    """Test that creating a node group with no input data fails as
    expected.

    """
    # Create the group
    result = requests.post(NODE_GROUPS_URI, headers=HEADERS,
                           verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['server_error']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Internal Server Error"
    assert 'detail' in result_data
    assert result_data['detail'] == \
        "error decoding JSON unexpected end of JSON input"
    assert 'status' in result_data
    assert result_data['status'] == result.status_code


# pylint: disable=invalid-name
def test_fail_create_node_group_no_label():
    """Test that creating a node group with no label in the input data
    fails as expected.

    """
    # Create the group
    data = {
        'description': "My test group",
        'members': {'ids': []}
    }
    result = requests.post(NODE_GROUPS_URI, json=data,
                           headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['bad']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Bad Request"
    assert 'detail' in result_data
    assert 'status' in result_data
    assert result_data['status'] == result.status_code


# pylint: disable=invalid-name
def test_fail_create_duplicate_group():
    """Test that trying to create the same group twice in a row fails.

    """
    # Create the group
    label = "test_group"
    data = {
        'label': label,
        'description': "My test group",
        'members': {'ids': []}
    }
    result = requests.post(NODE_GROUPS_URI, json=data,
                           headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['created']

    # Verify the initial contents
    get_uri = NODE_GROUP_URI % label
    result = requests.get(get_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['ok']
    result_data = result.json()
    assert 'label' in result_data
    assert result_data['label'] == data['label']
    assert 'description' in result_data
    assert result_data['description'] == data['description']
    assert 'members' in result_data
    assert result_data['members'] == data['members']

    # Now try to create it again
    result = requests.post(NODE_GROUPS_URI, json=data,
                           headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['conflict']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Conflict"
    assert 'detail' in result_data
    assert result_data['detail'] == \
        "operation would conflict with an existing group that "\
        "has the same label."
    assert 'status' in result_data
    assert result_data['status'] == result.status_code

    # Delete the group
    delete_uri = NODE_GROUP_URI % label
    result = requests.delete(delete_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['ok']

    # Make sure it is gone
    result = requests.get(get_uri, json=data,
                          headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['not_found']


# pylint: disable=invalid-name
def test_fail_delete_group_unknown():
    """Test that trying to delete an unknown group fails as expected.

    """
    delete_uri = NODE_GROUP_URI % "not_there"
    result = requests.delete(delete_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['not_found']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Not Found"
    assert 'detail' in result_data
    assert 'status' in result_data
    assert result_data['status'] == result.status_code


# pylint: disable=invalid-name
def test_fail_create_member_no_data():
    """Test that trying to create a new member in a node group without
    supplying any data fails as expected.

    """
    add_member_uri = NODE_GROUP_MEMBERS_URI % "fake"
    result = requests.post(add_member_uri, headers=HEADERS,
                           verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['server_error']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Internal Server Error"
    assert 'detail' in result_data
    assert result_data['detail'] == \
        "error decoding JSON unexpected end of JSON input"
    assert 'status' in result_data
    assert result_data['status'] == result.status_code


# pylint: disable=invalid-name
def test_fail_create_member_no_id():
    """Test that trying to create a new member in a node group without
    supplying any data fails as expected.

    """
    data = {
        'filler': 1
    }
    add_member_uri = NODE_GROUP_MEMBERS_URI % "fake"
    result = requests.post(add_member_uri, json=data,
                           headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['bad']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Bad Request"
    assert 'detail' in result_data
    assert result_data['detail'] == \
        "invalid xname ID"
    assert 'status' in result_data
    assert result_data['status'] == result.status_code


def test_fail_delete_unknown_member():
    """Test that trying to delete a node group member that does not exist
    fails as expected.

    """
    # Create the group
    label = "test_group"
    create_uri = NODE_GROUPS_URI
    data = {
        'label': label,
        'description': "My test group",
        'members': {'ids': []}
    }
    result = requests.post(create_uri, json=data,
                           headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['created']

    # Verify the initial contents
    get_uri = NODE_GROUP_URI % label
    result = requests.get(get_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['ok']
    result_data = result.json()
    assert 'label' in result_data
    assert result_data['label'] == data['label']
    assert 'description' in result_data
    assert result_data['description'] == data['description']
    assert 'members' in result_data
    assert result_data['members'] == data['members']

    # Delete an invalid group member
    delete_member_uri = NODE_GROUP_MEMBER_URI % (label, "not_there")
    result = requests.delete(delete_member_uri, headers=HEADERS,
                             verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['not_found']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Not Found"
    assert 'detail' in result_data
    assert result_data['detail'] == "group has no such member."
    assert 'status' in result_data
    assert result_data['status'] == result.status_code

    # Delete the group
    delete_uri = NODE_GROUP_URI % label
    result = requests.delete(delete_uri, headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['ok']

    # Make sure it is gone
    result = requests.get(get_uri, json=data,
                          headers=HEADERS, verify=HTTPS_VERIFY)
    assert result.status_code == requests.codes['not_found']
    result_data = result.json()
    assert 'title' in result_data
    assert result_data['title'] == "Not Found"
    assert 'detail' in result_data
    assert 'status' in result_data
    assert result_data['status'] == result.status_code
