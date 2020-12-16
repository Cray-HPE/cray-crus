"""BSS Hosts data to support Compute Rolling Upgrade.  Provide node
state and other information about nodes.

Copyright 2019, Cray Inc. All rights reserved.

"""
from ....app import APP, HEADERS
from ..errors import ComputeUpgradeError
from .wrap_requests import requests

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
        response = requests.get(BSS_HOSTS_URI, headers=HEADERS, verify=HTTPS_VERIFY)
        if response.status_code != requests.codes['ok']:  # pragma no unit test
            # Cannot be reached by unit tests without simulating a
            # network or service failure.
            raise ComputeUpgradeError(
                "error getting host data from BSS - %s[%d]" %
                (response.text, response.status_code)
            )
        result_data = response.json()
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
