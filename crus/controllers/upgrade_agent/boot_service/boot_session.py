#
# MIT License
#
# (C) Copyright 2019-2022 Hewlett Packard Enterprise Development LP
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
"""Boot Session abstraction for use with the BOS API

"""
import logging
import time
from etcd3_model import Etcd3Model, Etcd3Attr
from ....app import ETCD, APP, HEADERS
from .wrap_requests import requests
from .wrap_kubernetes import K8S_BATCH_CLIENT, kubernetes
from ..errors import ComputeUpgradeError
from ..requests_logger import do_request

LOGGER = logging.getLogger(__name__)
BOOT_SESSION_URI = APP.config['BOOT_SESSION_URI']
HTTPS_VERIFY = APP.config['HTTPS_VERIFY']
BOA_JOBS_NAMESPACE = APP.config['BOA_JOBS_NAMESPACE']


def no_upgrade_id():  # pragma should never happen
    """Default for upgrade_id, raises an exception because instantiating a
    BootSessionProgress without an Upgrade ID is not permitted.

    """
    reason = "'upgrade_id' must be specified in constructor of "\
        "BootSessionProgress objects"
    LOGGER.error("no_upgrade_id: This should never happen")
    raise AttributeError(reason)


class BootSessionProgress(Etcd3Model):
    """ETCD Model for storing boot session state in ETCD.  Indexed by
    Upgrade Session ID, which must be provided as the 'upgrade_id'
    keyword argument at construction time, either because we are
    loading from ETCD (JSON) or because the caller provided it.  An
    AttributeError will be raised if this is not provided.

    Fields:

        upgrade_id [the Object ID for reference -- must be unique]

           The ID of the Upgrade Session to which the BootSession to
           which this BootSessionProgress belongs.  Used as the Object
           ID.

        template_id

           The UUID that identifies the boot template to be used for
           this boot session.

        session_id

           The UUID (if the session has begun) of the boot session
           that is underway.  None if no boot session is underway.

        boot_start_time

           The local time at which the boot was initially requested
           (as a numeric value suitable for comparison).

        booting

           A threee state boolean indicating whether the session is
           currently booting (True), finished booting (False) or never
           started booting (None).

        success

           A three state boolean indicating whether the boot session
           (overall) succeeded (True), failed (False) or is either not
           completed or not started (None).

    """
    etcd_instance = ETCD
    model_prefix = "%s/%s" % (APP.config['ETCD_PREFIX'],
                              "boot_progress")

    # Make the default for upgrade ID produce an exception so that
    # failing to provide it in at construction is a coding error.
    upgrade_id = Etcd3Attr(is_object_id=True, default=no_upgrade_id)
    template_id = Etcd3Attr(default=None)
    session_id = Etcd3Attr(default=None)
    job_id = Etcd3Attr(default=None)
    boot_start_time = Etcd3Attr(default=None)
    booting = Etcd3Attr(default=None)
    success = Etcd3Attr(default=None)


class BootSession:
    """Abstraction to cover the BOS API and associated operations needed
    to initiate and monitor a boot session.

    """
    def __init__(self, upgrade_id):
        """Constructor - upgrade_id is the Upgrade Session ID of the
        associated boot session, will be used to locate state in ETCD
        among other things.

        """
        self.upgrade_id = upgrade_id
        self.progress = BootSessionProgress.get(upgrade_id)
        if self.progress is None:
            self.progress = BootSessionProgress(upgrade_id=upgrade_id)
            self.progress.put()

    # pylint: disable=unused-argument
    def boot(self, template_id, upgrading_label):
        """Ask BOS to boot using the template ID this session was created
        with, limiting to nodes in the upgrading HSM group.

        """
        LOGGER.info("BootSession(%s).boot(%s, %s): Starting",
                    self.upgrade_id, template_id, upgrading_label)
        session_request = {"operation": "reboot",
                           "templateUuid": template_id,
                           "limit": upgrading_label}
        response = do_request(requests.post, BOOT_SESSION_URI, headers=HEADERS,
                              verify=HTTPS_VERIFY, json=session_request)
        if response.status_code != requests.codes['created']:  # pragma no unit test
            # Cannot be reached by unit tests without simulating a
            # network or service failure.
            message = "error getting host data from BOS - %s[%d]" % (response.text, response.status_code)
            LOGGER.error("BootSession(%s).boot(%s, %s): %s", self.upgrade_id, template_id, upgrading_label, message)
            raise ComputeUpgradeError(message)
        try:
            result_data = response.json()
        except Exception:
            message = "error getting host data from BOS - error decoding JSON in response"
            LOGGER.exception("BootSession(%s).boot(%s, %s): %s",
                             self.upgrade_id, template_id, upgrading_label, message)
            raise ComputeUpgradeError(message)
        self.progress.session_id = result_data['links'][0]['href']
        self.progress.boot_start_time = time.time()
        self.progress.job_id = result_data['links'][0]['jobId']
        self.progress.booting = True
        self.progress.put()

    def booting(self):
        """ Ask whether this session is currently booting.

        Return:
            True - the boot session has been initiated and has not completed
            False - the boot session has been initiated and has completed
            None - the boot session has not been initiated

        """
        if not self.progress.session_id:
            message = "Boot session has not been initiated. " \
                      "A session.boot() is required before being " \
                      "able to check status"
            LOGGER.error("BootSession(%s).booting(): %s", self.upgrade_id, message)
            raise ComputeUpgradeError(message)

        name = self.progress.job_id
        namespace = BOA_JOBS_NAMESPACE
        LOGGER.debug("BootSession(%s).booting(): Checking status of k8s job %s in namespace %s",
                     self.upgrade_id, name, namespace)
        try:
            api_response = K8S_BATCH_CLIENT.read_namespaced_job_status(
                name,
                namespace
            )
        except kubernetes.client.rest.ApiException as exception:
            message = "failed retrieving job '%s': %s" % (name, exception.reason)
            LOGGER.exception("BootSession(%s).booting(): %s", self.upgrade_id, message)
            raise ComputeUpgradeError(message)
        LOGGER.debug("BootSession(%s).booting(): api_response = %s", self.upgrade_id, str(api_response))

        LOGGER.debug("BootSession(%s).booting(): Setting booting to 'True'", self.upgrade_id)
        self.progress.booting = True
        status = api_response.status
        if status.conditions:
            condition = status.conditions[-1]
            if condition.type == 'Complete':
                if condition.status == 'True':
                    LOGGER.debug("BootSession(%s).booting(): Completed, setting booting to 'False'", self.upgrade_id)
                    self.progress.success = (status.succeeded == 1)
                    self.progress.booting = False
            elif condition.type == 'Failed':
                if condition.status == 'True':
                    LOGGER.debug("BootSession(%s).booting(): Failed, setting booting to 'False'", self.upgrade_id)
                    self.progress.success = False
                    self.progress.booting = False
        self.progress.put()
        LOGGER.debug("BootSession(%s).booting(): returning %s", self.upgrade_id, self.progress.booting)
        return self.progress.booting

    def success(self):
        """ Ask whether this session succeeded.

        Return:
            True - the boot session has completed and has succeeded
            False - the boot session has completed and has failed
            None - the boot session has not completed (or has not
                   initiated, the two are indistinguishable here)

        """
        self.booting()
        return self.progress.success

    def cleanup(self):
        """Remove boot session progress from ETCD.

        """
        LOGGER.debug("BootSession(%s).cleanup(): starting", self.upgrade_id)
        self.progress.remove()
        LOGGER.debug("BootSession(%s).cleanup(): done", self.upgrade_id)
