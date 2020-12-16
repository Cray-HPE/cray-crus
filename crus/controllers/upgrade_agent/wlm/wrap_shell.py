"""Control import of 'shell' based on config (mock or real)

Copyright 2018, Cray Inc. All rights reserved.
"""
from ....app import APP
if APP.config['MOCK_WLM']:
    from ...mocking.shared import shell  # pylint: disable=unused-import
else:  # pragma no unit test
    import shell  # pylint: disable=unused-import
