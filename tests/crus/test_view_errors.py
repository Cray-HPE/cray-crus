"""
Python Tests for the Shasta Compute Rolling Upgrade Service (CRUS)

Copyright 2019, Cray Inc. All rights reserved.
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
