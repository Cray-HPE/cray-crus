"""
Tests the BootSession object

Copyright 2019, Cray Inc. All rights reserved.
"""
import uuid
import pytest
from crus.controllers.mocking.kubernetes.client import (
    inject_api_exception,
    inject_job_conditions
)
from crus.controllers.upgrade_agent.boot_service.boot_session import (
    BootSession,
    BootSessionProgress
)
from crus.controllers.upgrade_agent.errors import ComputeUpgradeError
from crus.app import APP

BOA_JOBS_NAMESPACE = APP.config['BOA_JOBS_NAMESPACE']


def test_successful_boot_session():
    """Tests a successful boot session

    """
    upgrade_id = str(uuid.uuid4())
    boot_session = BootSession(upgrade_id)
    boot_session.boot(str(uuid.uuid4()))  # initiate boot

    assert boot_session.success() is None
    assert boot_session.booting() is True

    # Simulate successful job completion
    assert boot_session.booting() is False
    assert boot_session.success() is True


def test_failed_boot_session():
    """Tests a successful boot session

    """
    inject_job_conditions(
        [
            {'type': 'Complete', 'status': 'False'},
            {'type': 'Complete', 'status': 'False'},
            {'type': 'Failed', 'status': 'True'},
        ]
    )

    upgrade_id = str(uuid.uuid4())
    boot_session = BootSession(upgrade_id)
    boot_session.boot(str(uuid.uuid4()))  # initiate boot

    assert boot_session.success() is None
    assert boot_session.booting() is True

    # Simulate successful job completion
    assert boot_session.booting() is False
    assert boot_session.success() is False
    inject_job_conditions(None)


def test_failed_boot_session_status():
    """Tests a successful boot session

    """
    upgrade_id = str(uuid.uuid4())
    boot_session = BootSession(upgrade_id)
    boot_session.boot(str(uuid.uuid4()))  # initiate boot

    inject_api_exception(["read_namespaced_job_status"])
    try:
        boot_session.success()
        assert False  # pragma unit test failure
    except ComputeUpgradeError as exc:
        assert "failed retrieving job" in str(exc)
    inject_api_exception(None)


def test_uninitiated_session_error():
    """Tests a boot session where status is checked before the boot
    operation is initiated

    """
    upgrade_id = str(uuid.uuid4())
    boot_session = BootSession(upgrade_id)

    with pytest.raises(ComputeUpgradeError) as exception:
        assert boot_session.booting() is False
    assert str(exception.value) == "Boot session has not been initiated. " \
                                   "A session.boot() is required before " \
                                   "being able to check status"


def test_missing_upgrade_id():
    """Tests invalid BootSessionProgress instantiation

    """
    with pytest.raises(AttributeError) as exception:
        BootSessionProgress()

    assert str(exception.value) == "'upgrade_id' must be specified in " + \
                                   "constructor of BootSessionProgress objects"
