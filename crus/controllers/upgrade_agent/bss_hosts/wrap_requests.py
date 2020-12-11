"""Control import of 'requests' based on config (mock or real)

Copyright 2018, Cray Inc. All rights reserved.
"""
from ....app import APP
if APP.config['MOCK_BSS_HOSTS']:
    from ...mocking.shared import requests  # pylint: disable=unused-import
else:  # pragma no unit test
    import requests  # pylint: disable=unused-import
