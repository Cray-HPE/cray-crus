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
import uuid
from crus.controllers.mocking.shared import requests
from crus.app import APP, HEADERS
BOOT_SESSION_URI = APP.config['BOOT_SESSION_URI']
HTTPS_VERIFY = APP.config['HTTPS_VERIFY']


def test_create_boot_session():
    """Test creating new boot session

    """
    template_uuid = str(uuid.uuid4())
    session_request = {"operation": "boot",
                       "templateUuid": template_uuid}
    response = requests.post(BOOT_SESSION_URI, headers=HEADERS, verify=HTTPS_VERIFY,
                             json=session_request)
    assert response.status_code == requests.codes['created']
    result_data = response.json()
    assert len(result_data) == 1
    assert 'href' in result_data['links'][0]
    assert 'operation' in result_data['links'][0]
    assert 'templateUuid' in result_data['links'][0]
    assert 'jobId' in result_data['links'][0]
    assert result_data['links'][0]['operation'] == "boot"
    assert result_data['links'][0]['templateUuid'] == template_uuid


def test_invalid_session_request():
    """Test invalid new boot session requests

    """
    template_uuid = str(uuid.uuid4())
    tests_session_request = [{"templateUuid": template_uuid},
                             {"operation": "boot"},
                             ""]
    expected_codes = ['bad', 'bad', 'server_error']
    for i, test_request in enumerate(tests_session_request):
        response = requests.post(BOOT_SESSION_URI, headers=HEADERS, verify=HTTPS_VERIFY,
                                 json=test_request)
        assert response.status_code == requests.codes[expected_codes[i]]
