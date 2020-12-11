"""Control import of 'shell' based on config (mock or real)

Copyright 2018, Cray Inc. All rights reserved.
"""
from ....app import APP
if APP.config['MOCK_KUBERNETES_CLIENT']:
    from ...mocking import kubernetes  # pylint: disable=unused-import
else:  # pragma no unit test
    import kubernetes  # pylint: disable=unused-import


kubernetes.config.load_incluster_config()
K8S_BATCH_CLIENT = kubernetes.client.BatchV1Api(kubernetes.client.ApiClient())
