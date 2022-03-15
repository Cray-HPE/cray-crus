#
# MIT License
#
# (C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP
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
""" Wrapper for requests which log the request and the results

"""
import logging
from .errors import ComputeUpgradeError

LOGGER = logging.getLogger(__name__)


def do_request(request_function, url, **kwargs):
    """ Wrapper which logs the request being made, makes the request, then
    logs the results (and returns them). Exceptions are caught, logged, and
    re-raised as a ComputeUpgradeError

    """
    if "json" in kwargs:
        LOGGER.debug("Making %s request to %s, json=%s", request_function.__name__, url, kwargs["json"])
    else:
        LOGGER.debug("Making %s request to %s", request_function.__name__, url)
    LOGGER.debug("%s", kwargs)
    try:
        resp = request_function(url, **kwargs)
    except Exception as request_exception:
        message = "%s request to %s resulted in %s: %s" % (request_function.__name__, url,
                                                           type(request_exception).__name__,
                                                           request_exception)
        LOGGER.exception(message)
        raise ComputeUpgradeError(message) from request_exception
    LOGGER.debug("%s request to %s got response with status code %d", request_function.__name__, url, resp.status_code)
    LOGGER.debug("response body: %s", resp.text)
    return resp
