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
from crus.controllers.mocking.shared import requests
from crus.app import APP, HEADERS
BSS_HOSTS_URI = APP.config['BSS_HOSTS_URI']
HTTPS_VERIFY = APP.config['HTTPS_VERIFY']


def test_get_hosts():
    """Test getting all of the host information in BSS hosts.

    """
    response = requests.get(BSS_HOSTS_URI, headers=HEADERS,
                            verify=HTTPS_VERIFY)
    assert response.status_code == requests.codes['ok']
    result_data = response.json()
    for node in result_data:
        assert 'ID' in node
        assert 'NID' in node
        assert 'State' in node
        assert 'Flag' in node
