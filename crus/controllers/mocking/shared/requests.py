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
"""Mock requests support for Compute Rolling Upgrade, patterned on the
'requests' python library (https://pypi.org/project/requests).  This
is a minimal implementation to support specifically what is needed for
Compute Rolling Upgrade.  Extend it as needed to support new features.

"""
import re
import json
from requests import codes


class PathRegistry:
    """Single instance static class for internal use that holds a mapping
    from registered path URIs to their handlers.

    """
    registered_patterns = {}

    @staticmethod
    def register(uri, handler):
        """Register a URI with a handler for future use with get, post,
        delete, put or patch calls.

        """
        # A uri may contain path arguments of the form '<arg_name>',
        # construct an re pattern to find them if they are there.
        path_arg_pattern = r"[<][^>]+[>]"

        # Get all of the fixed parts (i.e. non-argument parts) of the URI
        fixed_parts = re.split(path_arg_pattern, uri)

        # Get all of the argument names in the path (drop the '<' and '>')
        argnames = [found[1:-1] for found in re.findall(path_arg_pattern, uri)]

        # Merge the argnames and fixed parts in an alternating list so
        # we can compose a regular expression pattern with groups in
        # it that will let the arguments be parsed out.
        merged = [None] * (len(fixed_parts) + len(argnames))
        merged[::2] = fixed_parts
        merged[1::2] = argnames

        # Compose a pattern for parsing URIs to extract args (if any)
        arg = False
        pattern = r"^"
        for item in merged:
            if arg:
                arg_pattern = "(?P<%s>[^/]*)" % item
                pattern += arg_pattern
                arg = False
            else:
                pattern += item
                arg = True
        pattern += "/*$"

        # Register the handler with the pattern
        PathRegistry.registered_patterns[pattern] = handler

    @staticmethod
    def find(uri):
        """Look up a candidate URI by matching it against the URI patterns
        that have been registered.  If the match is found, return both
        the handler and the dictionary of path arguments from the
        match.  If no match is found return None in both places.

        """
        for pattern in PathRegistry.registered_patterns:
            match = re.match(pattern, uri)
            if match:
                return PathRegistry.registered_patterns[pattern], \
                    match.groupdict()
        return None, None


class Path:
    """Base class for path handlers defined in the Mock services.  Derive
    your service API path handlers from this.

    """
    def __init__(self, uri):
        PathRegistry.register(uri, self)

    def get(self, path_args, kwargs):  # pragma abstract method
        """Abstract 'get' method for this Path object, if the Path does not
        have a 'get' method, leave it unimplemented.  If the path does
        have a 'get' method, override it in your derived class.

        """
        raise NotImplementedError

    def post(self, path_args, kwargs):  # pragma abstract method
        """Abstract 'post' method for this Path object, if the Path does not
        have a 'post' method, leave it unimplemented.  If the path
        does have a 'post' method, override it in your derived class.

        """
        raise NotImplementedError

    def delete(self, path_args, kwargs):  # pragma abstract method
        """Abstract 'delete' method for this Path object, if the Path does not
        have a 'delete' method, leave it unimplemented.  If the path
        does have a 'delete' method, override it in your derived
        class.

        """
        raise NotImplementedError

    def put(self, path_args, kwargs):  # pragma abstract method
        """Abstract 'put' method for this Path object, if the Path does not
        have a 'put' method, leave it unimplemented.  If the path does
        have a 'put' method, override it in your derived class.

        """
        raise NotImplementedError

    def patch(self, path_args, kwargs):  # pragma abstract method
        """Abstract 'patch' method for this Path object, if the Path does not
        have a 'patch' method, leave it unimplemented.  If the path
        does have a 'patch' method, override it in your derived class.

        """
        raise NotImplementedError


class Response:
    """ Minimalist mock Response object for return from methods.
    """
    def __init__(self, text=None, status_code=None):
        self.text = text
        self.status_code = status_code

    def json(self):
        """ Translate the response text from JSON to data

        """
        return json.loads(self.text)


def get(uri, **kwargs):
    """Mock 'get' method to support 'get' requests on a given URI path.

    """
    handler, path_args = PathRegistry.find(uri)
    if handler is None:
        return Response(status_code=codes['not_found'],
                        text="URI '%s' unknown" % uri)
    status_code, text = handler.get(path_args, kwargs)
    return Response(status_code=status_code, text=text)


def post(uri, **kwargs):
    """Mock 'post' method to support 'post' requests on a given URI path.

    """
    handler, path_args = PathRegistry.find(uri)
    if handler is None:
        return Response(status_code=codes['not_found'],
                        text="URI '%s' unknown" % uri)
    status_code, text = handler.post(path_args, kwargs)
    return Response(status_code=status_code, text=text)


def delete(uri, **kwargs):
    """Mock 'delete' method to support 'delete' requests on a given URI path.

    """
    handler, path_args = PathRegistry.find(uri)
    if handler is None:
        return Response(status_code=codes['not_found'],
                        text="URI '%s' unknown" % uri)
    status_code, text = handler.delete(path_args, kwargs)
    return Response(status_code=status_code, text=text)


def put(uri, **kwargs):
    """Mock 'put' method to support 'put' requests on a given URI path.

    """
    handler, path_args = PathRegistry.find(uri)
    if handler is None:
        return Response(status_code=codes['not_found'],
                        text="URI '%s' unknown" % uri)
    status_code, text = handler.put(path_args, kwargs)
    return Response(status_code=status_code, text=text)


def patch(uri, **kwargs):
    """Mock 'patch' method to support 'patch' requests on a given URI path.

    """
    handler, path_args = PathRegistry.find(uri)
    if handler is None:
        return Response(status_code=codes['not_found'],
                        text="URI '%s' unknown" % uri)
    status_code, text = handler.patch(path_args, kwargs)
    return Response(status_code=status_code, text=text)
