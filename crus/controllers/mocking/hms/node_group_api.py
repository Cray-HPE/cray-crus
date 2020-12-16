"""
Mock BOS REST API

Copyright 2019, Cray Inc. All rights reserved.
"""
import json
from ..shared import requests
from .node_group_table import NodeGroupTable
from ....app import APP

BASE_URI = APP.config['NODE_GROUP_URI']
NODE_GROUPS_URI = BASE_URI
NODE_GROUP_URI = "%s/<label>" % BASE_URI
NODE_GROUP_MEMBERS_URI = "%s/<label>/members" % BASE_URI
NODE_GROUP_MEMBER_URI = "%s/<label>/members/<xname>" % BASE_URI


class NodeGroupsPath(requests.Path):  # pylint: disable=abstract-method
    """Path handler class to allow creating of node groups.

    """
    def post(self, path_args, kwargs):  # pylint: disable=unused-argument
        """Post method

        """
        status_code = requests.codes['created']
        input_data = None
        if 'json' in kwargs:
            input_data = kwargs['json']
        if not input_data:
            # No data provided, can't post
            status_code = requests.codes['server_error']
            data = {
                "type": "about:blank",
                "title": "Internal Server Error",
                "detail": "error decoding JSON unexpected end of JSON input",
                "status": status_code
            }
            return status_code, json.dumps(data)
        if 'label' not in input_data:
            # No name provided, can't post
            status_code = requests.codes['bad']
            data = {
                "type": "about:blank",
                "title": "Bad Request",
                "detail": "couldn\'t validate group: group or partition field has invalid characters",
                "status": status_code
            }
            return status_code, json.dumps(data)
        label = input_data['label']
        if NodeGroupTable.get(label) is not None:
            # Name must be unique
            status_code = requests.codes['conflict']
            data = {
                "type": "about:blank",
                "title": "Conflict",
                "detail": "operation would conflict with an existing group that has the same label.",
                "status": status_code
            }
            return status_code, json.dumps(data)
        data = [{"URI": "/hsm/v1/groups/%s" % label}]
        NodeGroupTable.create(label, input_data)
        return status_code, json.dumps(data)


class NodeGroupPath(requests.Path):  # pylint: disable=abstract-method
    """Path handler class to handle retrieving and deleting a node group.

    """
    def get(self, path_args, kwargs):  # pylint: disable=unused-argument
        """Get method

        """
        status_code = requests.codes['ok']
        label = path_args['label']
        data = NodeGroupTable.get(label)
        if not data:
            status_code = requests.codes['not_found']
            data = {
                "type": "about:blank",
                "title": "Not Found",
                "detail": "No such group: %s" % label,
                "status": status_code
            }
        return status_code, json.dumps(data)

    def delete(self, path_args, kwargs):  # pylint: disable=unused-argument
        """Delete method

        """
        status_code = requests.codes['ok']
        label = path_args['label']
        if not NodeGroupTable.delete(label):
            status_code = requests.codes['not_found']
            data = {
                "type": "about:blank",
                "title": "Not Found",
                "detail": "no such group.",
                "status": status_code
            }
            return status_code, json.dumps(data)
        data = {
            'code': 0,
            'message': "deleted 1 entry"
        }
        return status_code, json.dumps(data)


class NodeGroupMembersPath(requests.Path):  # pylint: disable=abstract-method
    """Path handler class to handle adding a new node (member) to a node
    group.

    """
    def post(self, path_args, kwargs):
        """Post method

        """
        status_code = requests.codes['created']
        label = path_args['label']
        input_data = None
        if 'json' in kwargs:
            input_data = kwargs['json']
        if not input_data:
            # No data provided, can't post
            status_code = requests.codes['server_error']
            data = {
                "type": "about:blank",
                "title": "Internal Server Error",
                "detail": "error decoding JSON unexpected end of JSON input",
                "status": status_code
            }
            return status_code, json.dumps(data)
        if 'id' not in input_data:
            # No name provided, can't post
            status_code = requests.codes['bad']
            data = {
                "type": "about:blank",
                "title": "Bad Request",
                "detail": "invalid xname ID",
                "status": status_code
            }
            return status_code, json.dumps(data)
        data = [
            {
                "URI": "/hsm/v1/groups/%s/members/%s" % (label,
                                                         input_data['id'])
            }
        ]
        NodeGroupTable.add_member(label, input_data)
        return status_code, json.dumps(data)


class NodeGroupMemberPath(requests.Path):  # pylint: disable=abstract-method
    """Path handler class to handle deleting a node (member) from a node
    group.

    """
    def delete(self, path_args, kwargs):  # pylint: disable=unused-argument
        """Delete method

        """
        status_code = requests.codes['okay']
        label = path_args['label']
        xname = path_args['xname']
        if not NodeGroupTable.remove_member(label, xname):
            status_code = requests.codes['not_found']
            data = {
                "type": "about:blank",
                "title": "Not Found",
                "detail": "group has no such member.",
                "status": status_code
            }
            return status_code, json.dumps(data)
        data = {'code': 0, 'message': "deleted 1 entry"}
        return status_code, json.dumps(data)


def start_service():
    """Initiate the mock Node Group service using the paths and handlers we
    have.

    """
    NodeGroupsPath(NODE_GROUPS_URI)
    NodeGroupPath(NODE_GROUP_URI)
    NodeGroupMembersPath(NODE_GROUP_MEMBERS_URI)
    NodeGroupMemberPath(NODE_GROUP_MEMBER_URI)
