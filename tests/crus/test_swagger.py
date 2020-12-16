"""
Python Tests for the Shasta Compute Rolling Upgrade Service (CRUS)

Copyright 2019, Cray Inc. All rights reserved.
"""
import json
import pytest
from prance import ResolvingParser
from crus import APP
from crus.app import HEADERS


@pytest.fixture
def client():
    """
    Python Test Fixture for the TMS tests...
    """
    ret = APP.test_client()
    yield ret


# GET tests on '/api/swagger.json' for Success
#
# pylint: disable=redefined-outer-name
def test_get_swagger(client):
    """
    Verify that GET from '/docs/swagger.json' works
    """
    # To GET to swagger route...
    retval = client.get("/docs/swagger.json",
                        headers=HEADERS)
    # Verify that the specification is openapi conformant
    parser = ResolvingParser(spec_string=retval.data.decode('utf-8'),
                             backend='openapi-spec-validator')
    result = parser.specification

    # Make sure some expected paths are in the resulting specification
    result = json.loads(retval.data)
    assert 'paths' in result
    assert '/session' in result['paths']
    assert '/session/{upgrade_id}' in result['paths']
    assert 'servers' in result
    server_0 = result['servers'][0]
    assert 'url' in server_0
    assert server_0['url'] == '/apis/crus'
