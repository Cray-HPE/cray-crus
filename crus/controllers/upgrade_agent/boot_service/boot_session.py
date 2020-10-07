"""Boot Session abstraction for use with the BOS API

Copyright 2019, Cray Inc. All rights reserved.
"""
import time
from etcd3_model import Etcd3Model, Etcd3Attr
from ....app import ETCD, APP, HEADERS
from .wrap_requests import requests
from .wrap_kubernetes import K8S_BATCH_CLIENT, kubernetes
from ..errors import ComputeUpgradeError

BOOT_SESSION_URI = APP.config['BOOT_SESSION_URI']
HTTPS_VERIFY = APP.config['HTTPS_VERIFY']
BOA_JOBS_NAMESPACE = APP.config['BOA_JOBS_NAMESPACE']


def no_upgrade_id():  # pragma should never happen
    """Default for upgrade_id, raises an exception because instantiating a
    BootSessionProgress without an Upgrade ID is not permitted.

    """
    reason = "'upgrade_id' must be specified in constructor of "\
        "BootSessionProgress objects"
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
        self.progress = BootSessionProgress.get(upgrade_id)
        if self.progress is None:
            self.progress = BootSessionProgress(upgrade_id=upgrade_id)
            self.progress.put()

    # pylint: disable=unused-argument
    def boot(self, template_id):
        """Ask BOS to boot using the template ID this session was created
        with.

        """
        session_request = {"operation": "reboot",
                           "templateUuid": template_id}
        response = requests.post(BOOT_SESSION_URI,
                                 headers=HEADERS,
                                 verify=HTTPS_VERIFY,
                                 json=session_request)

        if response.status_code != requests.codes['created']:  # pragma no unit test
            # Cannot be reached by unit tests without simulating a
            # network or service failure.
            raise ComputeUpgradeError(
                "error getting host data from BOS - %s[%d]" %
                (response.text, response.status_code)
            )
        result_data = response.json()
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
            raise ComputeUpgradeError(
                "Boot session has not been initiated. "
                "A session.boot() is required before being "
                "able to check status"
            )
        name = self.progress.job_id
        namespace = BOA_JOBS_NAMESPACE
        try:
            api_response = K8S_BATCH_CLIENT.read_namespaced_job_status(
                name,
                namespace
            )
        except kubernetes.client.rest.ApiException as exception:
            raise ComputeUpgradeError(
                "failed retrieving job '%s': %s" % (name, exception.reason))

        print("Setting booting to 'True'")
        self.progress.booting = True
        status = api_response.status
        if status.conditions:
            condition = status.conditions[-1]
            if condition.type == 'Complete':
                if condition.status == 'True':
                    print("Completed, setting booting to 'False'")
                    self.progress.success = (status.succeeded == 1)
                    self.progress.booting = False
            elif condition.type == 'Failed':
                if condition.status == 'True':
                    print("Failed, setting booting to 'False'")
                    self.progress.success = False
                    self.progress.booting = False
        self.progress.put()
        print("booting: returning %s" % str(self.progress.booting))
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
        self.progress.remove()
