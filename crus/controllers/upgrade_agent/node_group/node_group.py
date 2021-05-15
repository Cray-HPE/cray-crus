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

"""Class for managing Node Groups

"""
from ....app import APP, HEADERS
from .wrap_requests import requests
from ..errors import ComputeUpgradeError

BASE_URI = APP.config['NODE_GROUP_URI']
NODE_GROUPS_URI = BASE_URI
NODE_GROUP_URI = "%s/%%s" % BASE_URI
NODE_GROUP_MEMBERS_URI = "%s/%%s/members" % BASE_URI
NODE_GROUP_MEMBER_URI = "%s/%%s/members/%%s" % BASE_URI
HTTPS_VERIFY = APP.config['HTTPS_VERIFY']


class NodeGroup:
    """A representation of a NodeGroup that allows for creation,
    interrogation, modification, and deletion of the underlying Node
    Group.

    """
    def __init__(self, label, params=None):
        """Constructor -- if 'params' is specified, it contains the initial
        parameters for creating a node group.  In that case, the
        constructor will create the underlying node group.  Otherwise,
        the constructor will retrieve the named node group from HSM.

        """
        if params is not None:
            create_uri = NODE_GROUPS_URI
            # Make sure the name matches (and is present) in the
            # params
            params['label'] = label
            response = requests.post(create_uri, json=params, headers=HEADERS,
                                     verify=HTTPS_VERIFY, timeout=120.0)
            if response.status_code != requests.codes['created']:
                response_data = response.json()
                raise ComputeUpgradeError(
                    "failed to create Node Group named '%s' - %s[%d]" %
                    (label, response.text, response.status_code))
        else:
            get_uri = NODE_GROUP_URI % label
            response = requests.get(get_uri, headers=HEADERS,
                                    verify=HTTPS_VERIFY, timeout=120.0)
            response_data = response.json()
            if response.status_code != requests.codes['ok']:
                raise ComputeUpgradeError(
                    "failed to obtain Node Group named '%s' - %s[%d]" %
                    (label, response.text, response.status_code))
            params = response_data

        # Remember the settings for the boot set, whether we created
        # it or retrieved it.
        self.label = params['label']
        self.description = params['description']
        if 'tags' in params:
            self.tags = params['tags']
        else:
            self.tags = []
        self.members = params['members']['ids']

    def get_members(self):
        """Retrieve a safe copy of the member list from the node group

        """
        # Comprehension used here to avoid returning the list
        # reference
        #
        # pylint: disable=unnecessary-comprehension
        return [xname for xname in self.members]

    def add_member(self, xname):
        """Add a new member to the Node Group

        """
        member_data = {
            'id': xname
        }
        add_member_path = NODE_GROUP_MEMBERS_URI % self.label
        response = requests.post(add_member_path, json=member_data,
                                 headers=HEADERS, verify=HTTPS_VERIFY,
                                 timeout=120.0)
        if response.status_code != requests.codes['created']:
            raise ComputeUpgradeError(  # pragma should never happen
                "failed to add member %s to Node Group named '%s' - %s[%d]" %
                (xname, self.label, response.text, response.status_code))

    def remove_member(self, xname):
        """Remove a member from the Node Group

        """
        delete_member_path = NODE_GROUP_MEMBER_URI % (self.label, xname)
        response = requests.delete(delete_member_path, headers=HEADERS,
                                   verify=HTTPS_VERIFY, timeout=120.0)
        if response.status_code != requests.codes['ok']:
            raise ComputeUpgradeError(
                "failed to remove member %s from Node Group named '%s' "
                "- %s[%d]" %
                (xname, self.label, response.text, response.status_code))

    def get_params(self):
        """Retrieve the Node Group parameters.

        """
        params = {
            'label': self.label,
            'description': self.description,
            'members': {'ids': self.members},
        }
        if self.tags:
            params['tags'] = self.tags
        return params

    def delete(self):
        """Delete the underlying Node Group.

        """
        delete_uri = NODE_GROUP_URI % self.label
        response = requests.delete(delete_uri, headers=HEADERS,
                                   verify=HTTPS_VERIFY, timeout=120.0)
        if response.status_code != requests.codes['ok']:
            raise ComputeUpgradeError(
                "failed to delete node group named '%s' - %s[%d]" %
                (self.label, response.text, response.status_code))
