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
"""BSS Hosts data to support Compute Rolling Upgrade.  Provide node
state and other information about nodes.

"""
import logging
from ....app import APP, HEADERS
from ..errors import ComputeUpgradeError
from ..requests_logger import do_request
from .wrap_requests import requests

LOGGER = logging.getLogger(__name__)
BSS_HOSTS_URI = APP.config['BSS_HOSTS_URI']
HTTPS_VERIFY = APP.config['HTTPS_VERIFY']


class BSSHostTable:
    """A Host Table containing the information from the BSS hosts API
    in an easy to use form.

    """
    def __init__(self):
        """Constructor - obtains new host information from BSS when run

        """
        self.hosts = {}
        self.refresh()

    def refresh(self):
        """ Load the current state of hosts from BSS

        """
        response = do_request(requests.get, BSS_HOSTS_URI, headers=HEADERS, verify=HTTPS_VERIFY)
        if response.status_code != requests.codes['ok']:  # pragma no unit test
            # Cannot be reached by unit tests without simulating a
            # network or service failure.
            message = "error getting host data from BSS - %s[%d]" % \
                (response.text, response.status_code)
            LOGGER.error("BSSHostTable.refresh(): %s", message)
            raise ComputeUpgradeError(message)
        try:
            result_data = response.json()
        except Exception:
            message = "error getting host data from BSS - error decoding JSON in response"
            LOGGER.exception("BSSHostTable.refresh(): %s", message)
            raise ComputeUpgradeError(message)
        self.hosts = {host['ID']: host for host in result_data}

    def get_all_xnames(self):
        """ Get all of the XNAMEs for hosts in the BSS hosts list.

        """
        # Comprehension used here to avoid returning the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        return [xname for xname in self.hosts]

    def get_nid(self, xname):
        """Retrieve the NID from a host.

        """
        return self.hosts[xname]['NID']

    def get_role(self, xname):
        """Retrieve the Role setting from a host.

        """
        return self.hosts[xname]['Role']

    def get_state(self, xname):
        """Retrieve the State setting from a host.

        """
        return self.hosts[xname]['State']

    def get_flag(self, xname):
        """Retrieve the Flag setting from a host.

        """
        return self.hosts[xname]['Flag']

    def get_enabled(self, xname):
        """Retrieve the Enabled setting from a host.

        """
        return self.hosts[xname]['Enabled']
