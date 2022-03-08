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
Python Tests for the Shasta Compute Rolling Upgrade Service (CRUS)

"""
from crus.views import errors


def test_missing_input():
    """Test raising and printing the MissingInput exception used for
    error reorting in the CRUS views.

    """
    try:
        raise errors.MissingInput()
    except errors.RequestError as exc:
        assert str(exc) == exc.title


def test_validation():
    """Test raising and printing the DataValidationFailure exception used
    for error reorting in the CRUS views.

    """
    try:
        raise errors.DataValidationFailure()
    except errors.RequestError as exc:
        assert str(exc) == exc.title


def test_not_found():
    """Test raising and printing the ResourceNotFound exception used
    for error reorting in the CRUS views.

    """
    try:
        raise errors.ResourceNotFound()
    except errors.RequestError as exc:
        assert str(exc) == exc.title


def test_method_not_allowed():
    """Test raising and printing the MethodNotAllowed exception used
    for error reorting in the CRUS views.

    """
    try:
        raise errors.MethodNotAllowed()
    except errors.RequestError as exc:
        assert str(exc) == exc.title
