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
Mock BSS REST API

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
