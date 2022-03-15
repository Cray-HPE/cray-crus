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
"""
Python Tests for the Shasta Compute Rolling Upgrade Service (CRUS)

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
