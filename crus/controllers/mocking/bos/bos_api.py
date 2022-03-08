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
Mock BOS REST API

"""
import json
import uuid
from ..shared import requests
from .bos_session_table import BootSessionTable
from ...upgrade_agent.boot_service.wrap_kubernetes import K8S_BATCH_CLIENT
from ....app import APP

BASE_URI = APP.config['BOOT_SESSION_URI']
BOOT_SESSIONS_URI = BASE_URI
BOOT_SESSION_URI = "%s/<session_id>" % BASE_URI
BOA_JOBS_NAMESPACE = APP.config['BOA_JOBS_NAMESPACE']


class NewBootSessionPath(requests.Path):  # pylint: disable=abstract-method
    """Path handler class to allow creating of boot session.

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
                "instance": "",
                "type": "about:blank",
                "title": "Internal Server Error",
                "detail": "error decoding JSON unexpected end of JSON input",
                "status": status_code,
            }

            return status_code, json.dumps(data)
        if 'operation' not in input_data:
            # No operation provided
            status_code = requests.codes['bad']
            data = {
                "type": "about:blank",
                "title": "Bad Request",
                "detail": "'operation' is required",
                "status": status_code,
                "instance": ""
            }
            return status_code, json.dumps(data)
        if 'templateUuid' not in input_data:
            # No templateUuid provided
            status_code = requests.codes['bad']
            data = {
                "type": "about:blank",
                "title": "Bad Request",
                "detail": "'templateUuid' is required",
                "status": status_code,
                "instance": ""
            }
            return status_code, json.dumps(data)

        session_id = str(uuid.uuid4())
        job_id = "boot-job-%s" % str(uuid.uuid4())
        input_data['jobId'] = job_id
        mock_job = {
            "metadata": {
                "name": job_id,
                "namespace": BOA_JOBS_NAMESPACE
            },
        }
        if APP.config['MOCK_KUBERNETES_CLIENT']:
            K8S_BATCH_CLIENT.create_namespaced_job(BOA_JOBS_NAMESPACE,
                                                   mock_job)
        boot_session = BootSessionTable.create(session_id, input_data)
        if APP.config['MOCK_BSS_HOSTS']:
            # Perform a mock boot of the session's nodes.
            BootSessionTable.boot(session_id)
        return status_code, json.dumps(boot_session)


def start_service():
    """Initiate the mock Boot Session service using the paths and handlers we
    have.

    """
    NewBootSessionPath(BASE_URI)
