"""
Mock BSS REST API

Copyright 2019, Cray Inc. All rights reserved.
"""
import json
from ..shared import requests
from .bss_nodes import BSSNodeTable
from ....app import APP

BSS_HOSTS_URI = APP.config['BSS_HOSTS_URI']
HTTPS_VERIFY = APP.config['HTTPS_VERIFY']


class BSSHostsPath(requests.Path):  # pylint: disable=abstract-method
    """Path handler class to allow creating of node groups.

    """
    def get(self, path_args, kwargs):  # pylint: disable=unused-argument
        """Get method

        """
        status_code = requests.codes['ok']
        data = BSSNodeTable.get_all()
        return status_code, json.dumps(data)


def start_service():
    """Initiate the mock Node Group service using the paths and handlers we
    have.

    """
    BSSHostsPath(BSS_HOSTS_URI)
