"""
Tests for the Compute Upgrade Service

Copyright 2019 Cray Inc. All rights Reserved.
"""
import crus


def test_import():
    """ Verify that CRUS imported as expected
    """
    help(crus)
    assert crus.VERSION
    assert crus.API_VERSION
