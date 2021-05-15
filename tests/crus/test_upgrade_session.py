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

"""
Python Tests for the Shasta Compute Rolling Upgrade Service (CRUS)

"""
import json
import uuid
from http import HTTPStatus as HS
import pytest
from crus import APP, API_VERSION
from crus.app import HEADERS
from crus.controllers.upgrade_agent.node_group import NodeGroup


@pytest.fixture
def client():
    """
    Python Test Fixture for the TMS tests...
    """
    ret = APP.test_client()
    yield ret


def verify_session(session, original=None):
    """ Check that an update session has the required contents.
    """
    assert 'upgrade_id' in session
    assert 'api_version' in session
    assert session['api_version'] == API_VERSION
    assert 'kind' in session
    assert session['kind'] == "ComputeUpgradeSession"
    supplied_keys = [
        'starting_label',
        'upgrading_label',
        'failed_label',
        'workload_manager_type',
        'upgrade_template_id',
        'upgrade_step_size',
    ]
    for key in supplied_keys:
        assert key in session
    if original:
        for key in supplied_keys:
            assert session[key] == original[key]


# pylint: disable=redefined-outer-name
def test_basic_operations_succes(client):
    """
    Verify that I can add, get, list and delete a session.
    """

    # Set up the data to send with the POST request
    data = {
        'starting_label': "nodes-to-upgrade",
        'upgrading_label': "nodes-that-are-upgrading",
        'failed_label': "nodes-that-failed-to-upgrade",
        'workload_manager_type': "slurm",
        'upgrade_step_size': 15,
        'upgrade_template_id': str(uuid.uuid4())
    }
    # create the node groups (don't put anything in them)
    for key in ('starting_label', 'upgrading_label', 'failed_label'):
        label = data[key]
        params = {
            'label': label,
            'description': 'some description',
            'members': {'ids': []},
        }
        NodeGroup(label, params=params)
    # Issue the POST request
    retval = client.post("/session",
                         data=json.dumps(data),
                         headers=HEADERS)
    # Make sure that the JSON sent back from the POST request as
    # confirmation of the POST has the session we requested in it.
    result = json.loads(retval.data)
    verify_session(result, data)

    # Grab the session ID from the POST results so I can try a GET on
    # the session data directly.
    upgrade_id = result['upgrade_id']

    # Issue a GET to /session and see what I get back
    retval = client.get("/session", headers=HEADERS)
    # Make sure that the JSON list sent back from the GET request has
    # only the session I created in it.
    result = json.loads(retval.data)
    assert isinstance(result, list)
    assert len(result) == 1
    verify_session(result[0], data)
    assert result[0]['upgrade_id'] == upgrade_id

    # Issue a GET to /session/<session ID>/ and see what I get back
    retval = client.get("/session/{}".format(upgrade_id),
                        headers=HEADERS)
    # Make sure that the JSON sent back from the GET request matches
    # what I created
    result = json.loads(retval.data)
    verify_session(result, data)
    assert result['upgrade_id'] == upgrade_id

    # Should be allowed to delete a running session.  We should have
    # some checking here to show that it actually goes through the
    # process of deletion.
    retval = client.delete("/session/{}".format(upgrade_id),
                           headers=HEADERS)
    result = json.loads(retval.data)
    verify_session(result, data)
    assert result['upgrade_id'] == upgrade_id


# pylint: disable=redefined-outer-name
def test_missing_data(client):
    """
    Verify that all of the required fields are really required.
    """

    # Set up the data to send with the POST request
    data = {
        'starting_label': "nodes-to-upgrade",
        'upgrading_label': "nodes-that-are-upgrading",
        'failed_label': "nodes-that-failed-to-upgrade",
        'workload_manager_type': "slurm",
        'upgrade_step_size': 15,
        'upgrade_template_id': str(uuid.uuid4())
    }
    for key in data:
        test_data = {test_key: data[test_key] for test_key in data
                     if test_key != key}
        # Issue the POST request
        retval = client.post("/session",
                             data=json.dumps(test_data),
                             headers=HEADERS)
        assert retval.status_code == HS.UNPROCESSABLE_ENTITY
        result = json.loads(retval.data)
        assert 'status' in result
        assert result['status'] == retval.status_code
        assert 'title' in result
        assert "Unprocessable Entity" in result['title']
        assert 'detail' in result
        assert "failed validation" in result['detail']


# pylint: disable=redefined-outer-name
def test_nonexistent_session(client):
    """
    Verify that all of the required fields are really required.
    """

    # Issue a GET request on a non-existent Upgrade ID
    retval = client.get("/session/no-such-session",
                        headers=HEADERS)
    assert retval.status_code == HS.NOT_FOUND
    result = json.loads(retval.data)
    assert 'status' in result
    assert result['status'] == retval.status_code
    assert 'title' in result
    assert "Not Found" in result['title']
    assert 'detail' in result
    assert "does not exist" in result['detail']
