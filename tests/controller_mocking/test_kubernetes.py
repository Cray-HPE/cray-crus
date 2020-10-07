"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

Copyright 2019 Cray Inc. All rights Reserved.

"""
from crus.controllers.mocking.kubernetes import client, config, ApiException
from crus.controllers.mocking.kubernetes.client import (
    inject_api_exception,
    inject_job_conditions
)

# Test Job Body to use anywhere we want it
JOB_BODY = {
    'metadata': {
        'name': 'my-fake-job',
        'labels': {
            'run': 'my-fake-job',
        },
    },
    'spec': {
        'restartPolicy': 'Never',
        'backoffLimit': 4,
        'containers': [
            {
                'name': 'fake_job',
                'image': 'sms.local:5000/erl/fake-job:latest',
            },
        ],
    },
}


def test_load_incluster_config():
    """Run the mock load incluster config

    """
    config.load_incluster_config()


def run_job_test():
    """Test mock creation, listing and deletion of of a namespaced job

    """
    k8s = client.BatchV1Api()
    k8s.create_namespaced_job('default', JOB_BODY)
    selector = "metadata.name==my-fake-job"
    result = k8s.list_namespaced_job('default', field_selector=selector)
    found = 0
    searched = 0
    for job in result.items:
        searched += 1
        if job.metadata.name == 'my-fake-job':
            found += 1
    assert found == 1
    assert searched == 1
    k8s.delete_namespaced_job('my-fake-job', 'default')
    result = k8s.list_namespaced_job('default', field_selector=selector)
    found = 0
    searched = 0
    for job in result.items:  # pragma should never happen
        searched += 1
        if job.metadata.name == 'my-fake-job':
            found += 1
    assert found == 0
    assert searched == 0


def test_namespaced_job():
    """Test mock creation, listing and deletion of of a namespaced job

    """
    run_job_test()


def test_inject_exception():
    """Test injecting an exception into all of the job operations.

    """
    inject_api_exception(
        [
            "create_namespaced_job",
            "list_namespaced_job",
            "delete_namespaced_job",
        ]
    )
    k8s = client.BatchV1Api()
    try:
        k8s.create_namespaced_job('default', JOB_BODY)
        assert False  # pragma unit test failure
    except ApiException:
        pass
    try:
        k8s.delete_namespaced_job('my-fake-job', 'default')
        assert False  # pragma unit test failure
    except ApiException:
        pass
    try:
        k8s.list_namespaced_job('default')
        assert False  # pragma unit test failure
    except ApiException:
        pass
    inject_api_exception(None)
    run_job_test()


def test_inject_conditions():
    """Test injecting job conditions into created jobs.

    """
    condition_list = [
        {'type': 'Complete', 'status': False},
        {'type': 'Complete', 'status': False},
        {'type': 'Complete', 'status': False},
        {'type': 'Complete', 'status': False},
        {'type': 'Failed', 'status': True},
        None
    ]
    inject_job_conditions(condition_list)
    k8s = client.BatchV1Api()
    k8s.create_namespaced_job('default', JOB_BODY)
    selector = "metadata.name==my-fake-job"
    for condition in condition_list[0:-1]:
        result = k8s.list_namespaced_job('default', field_selector=selector)
        job = result.items[0]
        assert job.status.conditions[-1].type == condition['type']
        assert job.status.conditions[-1].status == condition['status']
    # A few more times to show it sticks
    result = k8s.list_namespaced_job('default', field_selector=selector)
    job = result.items[0]
    assert job.status.conditions[-1].type == condition_list[-2]['type']
    assert job.status.conditions[-1].status == condition_list[-2]['status']

    result = k8s.list_namespaced_job('default', field_selector=selector)
    job = result.items[0]
    assert job.status.conditions[-1].type == condition_list[-2]['type']
    assert job.status.conditions[-1].status == condition_list[-2]['status']

    result = k8s.list_namespaced_job('default', field_selector=selector)
    job = result.items[0]
    assert job.status.conditions[-1].type == condition_list[-2]['type']
    assert job.status.conditions[-1].status == condition_list[-2]['status']

    # Clean up
    inject_job_conditions(None)


def test_read_nonexistent_job_status():  # pylint: disable=invalid-name
    """Try to read the status of a job that does not exist.

    """
    k8s = client.BatchV1Api()
    try:
        k8s.read_namespaced_job_status("non-existent-job", "default")
        assert False  # pragma unit test failure
    except ApiException:
        pass
