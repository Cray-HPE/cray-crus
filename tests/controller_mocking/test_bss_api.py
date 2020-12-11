"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

Copyright 2019 Cray Inc. All rights Reserved.

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
