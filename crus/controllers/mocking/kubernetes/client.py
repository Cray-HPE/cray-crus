"""
Mock kubernetes client sub-module

Copyright 2019, Cray Inc. All rights reserved.
"""
import copy
from kubernetes.client.rest import ApiException
from kubernetes.client import rest

INJECT_API_EXCEPTION = []
INJECTED_JOB_CONDITIONS = None
INJECTED_JOBS = []


def inject_job_conditions(job_conditions):
    """For test case injection, set up a list of conditions that all
        created jobs will cycle through.  By default the conditions
        are
            [
                {'type': 'Complete', 'status': 'False'},
                {'type': 'Complete', 'status': 'False'},
                {'type': 'Complete', 'status': 'True'},
                None
            ]

        Specifying a non-None 'job_conditions' argument containing a list of
        condition dictionaries, where the 'type' values are in the set

            ["Complete", "Failed"]

        and the 'status' values are in the set

            ['True', 'False', 'Unkown']

        causes all jobs created to absorb the specified sequence of
        conditions.  Each condition shows up in the job's condition
        list as a sequence of events.  Terminating with a None value
        causes the last condition before the None to be the last event
        seen.  If you leave off the None, the last condition will
        repeat forever.

        Specifying None for job_conditions resets job creation to the
        default behavior.

    """
    global INJECTED_JOB_CONDITIONS  # pylint: disable=global-statement
    assert job_conditions is None or isinstance(job_conditions, list)
    if job_conditions is not None:
        # Protect the caller's data, comprehension used here to avoid
        # capturing the list reference
        #
        # pylint: disable=unnecessary-comprehension
        INJECTED_JOB_CONDITIONS = [condition
                                   for condition in job_conditions]
    else:
        INJECTED_JOB_CONDITIONS = None


def inject_api_exception(method_names=None):
    """For test case injection, set up a list of methods that will raise
    ApiException when called.  Setting the list to None clears the
    exception injection.

    """
    global INJECT_API_EXCEPTION  # pylint: disable=global-statement
    assert method_names is None or isinstance(method_names, list)
    INJECT_API_EXCEPTION = method_names if method_names is not None else []


def _inject_exception(name):
    """Check whether an API exception was injected for the specified
    method name, and raise the exception if it was.

    """
    if name in INJECT_API_EXCEPTION:
        raise rest.ApiException(
            "API exception injected by test for method '%s'" % name
        )


class Item:
    """Arbitrary object where dictionary keys are turned into structure
    fields for easier dereferencing like the kubernetes module does it..

    """
    def __init__(self, data):
        """Constructor - drive the top level creation of the object.

        """
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        """ Recursive wrapper, drive the handling of nested elements.

        """
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        return Item(value) if isinstance(value, dict) else value


class ListResult:
    """Request result to mock the result gotten for list... in kubernetes
    library.

    """
    def __init__(self, items):
        """Constructor
        """
        self.items = items


class BatchV1Api:
    """batch_v1_api contains operations on jobs.

    """
    @staticmethod
    def __get_job_condition(body):
        """Get the next condition for a job.  The last condition found sticks
        and always returns the same.

        """
        condition = body['test_conditions'].pop(0)
        if not body['test_conditions']:
            body['test_conditions'].append(condition)
        return condition

    @staticmethod
    def __set_success(body):
        """Determine success from the conditions we have seen.  If there is a
        'completed' type condition at the end of the condition list
        and it has a status of 'True' then we set 'succeeded' in the
        body status to 1, otherwise, we do not change it.

        """
        if body['status']['conditions']:
            condition = body['status']['conditions'][-1]
            if condition['type'] == 'Complete':
                if condition['status'] == 'True':
                    body['status']['succeeded'] = 1

    # pylint: disable=unused-argument
    def __init__(self, apiClient=None):
        """Constructor

        """
        self.jobs = {}

    # pylint: disable=unused-argument
    def create_namespaced_job(self, namespace, body, **kwargs):
        """Mock create job function.  Adds the body to the Job
        dictionary based on the name in the 'metadata' field.

        """
        _inject_exception("create_namespaced_job")
        assert 'metadata' in body
        assert 'name' in body['metadata']
        name = body['metadata']['name']

        # Handle injectd job condition sequences if specified, or take
        # the defaults
        if INJECTED_JOB_CONDITIONS is not None:
            job_conditions = [copy.deepcopy(condition)
                              for condition in INJECTED_JOB_CONDITIONS]
        else:
            job_conditions = [
                {'type': 'Complete', 'status': 'False'},
                {'type': 'Complete', 'status': 'False'},
                {'type': 'Complete', 'status': 'True'},
                None,
            ]
        body['test_conditions'] = job_conditions
        body['status'] = {
            'conditions': [],
            'succeeded': 0
        }
        self.jobs[name] = body

    def list_namespaced_job(self, namespace, **kwargs):
        """Lists the jobs in the specified namespace.

        """
        _inject_exception("list_namespaced_job")
        field = None
        if 'field_selector' in kwargs:
            field_selector = kwargs['field_selector']
            # The only field selector we use is 'metadata.name==<name>'
            # and we always use that, so we are going to parse to that...
            field, value = field_selector.split("==")
            assert field == "metadata.name"
        items = []
        for job_name in self.jobs:
            if field and self.jobs[job_name]['metadata']['name'] == value:
                body = self.jobs[job_name]
                condition = self.__get_job_condition(body)
                if condition:
                    body['status']['conditions'].append(condition)
                self.__set_success(body)
                items.append(Item(body))
        return ListResult(items)

    # pylint: disable=unused-argument
    def delete_namespaced_job(self, name, namespace, **kwargs):
        """Mock delete job function.  Removes the named job.

        """
        _inject_exception("delete_namespaced_job")
        assert name in self.jobs
        del self.jobs[name]

    def read_namespaced_job_status(self, name, namespace):
        """Mock retrieve job status

        """
        _inject_exception("read_namespaced_job_status")
        if name not in self.jobs:
            msg = "job '%s' not found in namespace '%s'" % (name, namespace)
            raise ApiException(status=0, reason=msg)
        job_space = self.jobs[name]['metadata']['namespace']
        if job_space != namespace:  # pragma no unit test
            msg = "job '%s' not found in namespace '%s'" % (name, namespace)
            raise ApiException(status=0, reason=msg)
        jobs = self.list_namespaced_job(
            namespace,
            field_selector="metadata.name==%s" % name
        )
        return jobs.items[0]


class ApiClient:
    """Mock interface of ApiClient.  Nothing needs to be here, but it is
    needed when setting up the BatchV1Api client.

    """
