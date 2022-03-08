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
"""Tests of the Mock System used for stand-alone development and unit
testing of the Compute Rolling Upgrade Agent.

"""
import json
from crus.controllers.mocking.shared import requests

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}


class MyTestPath(requests.Path):
    """Path handler class to test various kinds of paths.  Each method
    returns the same collection of data, indicating the method name,
    the URI used, the input data and a dictionary of path based
    arguments.

    """
    def __init__(self, uri):
        """Constructor

        """
        super().__init__(uri)
        self.uri = uri

    def get(self, path_args, kwargs):
        """Get method

        """
        input_data = None
        if 'json' in kwargs:
            input_data = kwargs['json']
        data = {
            'request': "get",
            'uri': self.uri,
            'input_data': input_data,
            'path_args': path_args
        }
        return requests.codes['ok'], json.dumps(data)

    def post(self, path_args, kwargs):
        """Post method

        """
        input_data = None
        if 'json' in kwargs:
            input_data = kwargs['json']
        data = {
            'request': "post",
            'uri': self.uri,
            'input_data': input_data,
            'path_args': path_args
        }
        return requests.codes['ok'], json.dumps(data)

    def delete(self, path_args, kwargs):
        """Delete method

        """
        input_data = None
        if 'json' in kwargs:
            input_data = kwargs['json']
        data = {
            'request': "delete",
            'uri': self.uri,
            'input_data': input_data,
            'path_args': path_args
        }
        return requests.codes['ok'], json.dumps(data)

    def put(self, path_args, kwargs):
        """Put method

        """
        input_data = None
        if 'json' in kwargs:
            input_data = kwargs['json']
        data = {
            'request': "put",
            'uri': self.uri,
            'input_data': input_data,
            'path_args': path_args
        }
        return requests.codes['ok'], json.dumps(data)

    def patch(self, path_args, kwargs):
        """Patch method

        """
        input_data = None
        if 'json' in kwargs:
            input_data = kwargs['json']
        data = {
            'request': "patch",
            'uri': self.uri,
            'input_data': input_data,
            'path_args': path_args
        }
        return requests.codes['ok'], json.dumps(data)


def run_test_case(uri, expected_uri, path_args):
    """The basic test case that is repeated for all paths defined in this
    overall test suite.

    """
    data = {
        "one": 1,
        "two": 2,
        "three": 3
    }
    response = requests.get(uri, headers=HEADERS, json=data, verify=False)
    assert response.status_code == requests.codes['ok']
    result_data = response.json()
    assert result_data['request'] == "get"
    assert result_data['uri'] == expected_uri
    assert result_data['input_data'] == data
    assert result_data['path_args'] == path_args

    response = requests.post(uri, headers=HEADERS, json=data, verify=False)
    assert response.status_code == requests.codes['ok']
    result_data = response.json()
    assert result_data['request'] == "post"
    assert result_data['uri'] == expected_uri
    assert result_data['input_data'] == data
    assert result_data['path_args'] == path_args

    response = requests.delete(uri, headers=HEADERS, json=data, verify=False)
    assert response.status_code == requests.codes['ok']
    result_data = response.json()
    assert result_data['request'] == "delete"
    assert result_data['uri'] == expected_uri
    assert result_data['input_data'] == data
    assert result_data['path_args'] == path_args

    response = requests.put(uri, headers=HEADERS, json=data, verify=False)
    assert response.status_code == requests.codes['ok']
    result_data = response.json()
    assert result_data['request'] == "put"
    assert result_data['uri'] == expected_uri
    assert result_data['input_data'] == data
    assert result_data['path_args'] == path_args

    response = requests.patch(uri, headers=HEADERS, json=data, verify=False)
    assert response.status_code == requests.codes['ok']
    result_data = response.json()
    assert result_data['request'] == "patch"
    assert result_data['uri'] == expected_uri
    assert result_data['input_data'] == data
    assert result_data['path_args'] == path_args


def test_simple_path():
    """Test that a basic Path object with all methods presented can be
    constructed and used.

    """
    path_uri = "http://test_path/api/simple_path"
    test_uri = path_uri
    # Register a MyTestPath handler set with 'path_uri'
    MyTestPath(path_uri)
    path_args = {}
    # Run the test case with the test URI as seen above
    run_test_case(test_uri, path_uri, path_args)

    # Run the test case with a trailing slash
    run_test_case(test_uri + '/', path_uri, path_args)


def test_one_path_arg():
    """Test requests on a path with one path based argument at the end of
    the path.

    """
    path_uri = "http://test_path/api/test_path/<path_arg>"
    test_uri = "http://test_path/api/test_path/path_arg_value"
    # Register a MyTestPath handler set with 'path_uri'
    MyTestPath(path_uri)
    path_args = {
        'path_arg': "path_arg_value"
    }
    # Run the test case with the test URI as seen above
    run_test_case(test_uri, path_uri, path_args)

    # Run the test case with a trailing slash
    run_test_case(test_uri + '/', path_uri, path_args)


def test_one_interior_path_arg():
    """Test requests on a path with one path based argument in the middle
    of the path.

    """
    path_uri = \
        "http://test_path/api/test_path/<path_arg>/stuff"
    test_uri = \
        "http://test_path/api/test_path/path1_value/stuff"
    # Register a MyTestPath handler set with 'path_uri'
    MyTestPath(path_uri)
    path_args = {
        'path_arg': "path1_value"
    }
    # Run the test case with the test URI as seen above
    run_test_case(test_uri, path_uri, path_args)

    # Run the test case with a trailing slash
    run_test_case(test_uri + '/', path_uri, path_args)


def test_two_path_args():
    """Test requests on a path with two path based arguments separated
    by fixed content at the end of the path.

    """
    path_uri = "http://test_path/api/test_path/<path_arg_1>/and/<path_arg_2>"
    test_uri = "http://test_path/api/test_path/path1_value/and/path2_value"
    # Register a MyTestPath handler set with 'path_uri'
    MyTestPath(path_uri)
    path_args = {
        'path_arg_1': "path1_value",
        'path_arg_2': "path2_value"
    }
    # Run the test case with the test URI as seen above
    run_test_case(test_uri, path_uri, path_args)

    # Run the test case with a trailing slash
    run_test_case(test_uri + '/', path_uri, path_args)


def test_two_interior_path_args():
    """Test requests on a path with two path based arguments separated
    by fixed content in the middle of the path.

    """
    path_uri = \
        "http://test_path/api/test_path/<path_arg_1>/and/<path_arg_2>/stuff"
    test_uri = \
        "http://test_path/api/test_path/path1_value/and/path2_value/stuff"
    # Register a MyTestPath handler set with 'path_uri'
    MyTestPath(path_uri)
    path_args = {
        'path_arg_1': "path1_value",
        'path_arg_2': "path2_value"
    }
    # Run the test case with the test URI as seen above
    run_test_case(test_uri, path_uri, path_args)

    # Run the test case with a trailing slash
    run_test_case(test_uri + '/', path_uri, path_args)


def test_bad_uri():
    """Test methods on an unknown URI

    """
    uri = "http://not.there.com/some/path/that/does/not/exist"
    response = requests.get(uri, headers=HEADERS, json={}, verify=False)
    assert response.status_code == requests.codes['not_found']
    assert uri in response.text

    response = requests.post(uri, headers=HEADERS, json={}, verify=False)
    assert response.status_code == requests.codes['not_found']
    assert uri in response.text

    response = requests.delete(uri, headers=HEADERS, json={}, verify=False)
    assert response.status_code == requests.codes['not_found']
    assert uri in response.text

    response = requests.put(uri, headers=HEADERS, json={}, verify=False)
    assert response.status_code == requests.codes['not_found']
    assert uri in response.text

    response = requests.patch(uri, headers=HEADERS, json={}, verify=False)
    assert response.status_code == requests.codes['not_found']
    assert uri in response.text
