"""
The 'tms' module configurations.

Copyright 2019, Cray Inc. All rights reserved.
"""
import os


def uri_compose(full_env, api_env, api_default, gw_path):
    """Compose a specific URI prefix either using an enironment variable
    containing the full prefix (full_env), if that environment
    variable is present or using the combination of an API environment
    variable (api_env) and the gateway path (gw_path) if the
    environment variable in full_env is not present.  If neither
    environment variable is present, use a default API URI
    (api_default).

    """
    full_uri = os.environ.get(full_env, None)
    gw_uri = "%s/%s" % (os.environ.get(api_env, api_default), gw_path)
    uri = full_uri if full_uri is not None else gw_uri
    return uri


def bool_from_env(env_name, true="yes", default="yes"):
    """Take a boolean value from an environment variable based on its
    value (by default 'yes' means True).  The 'true' parameter sets
    the value that will evaluate to True (all others will translate to
    False.  The value is case insensitive.  The 'default' parameter
    sets the value to use if the environment variable is not present.

    """
    return os.environ.get(env_name, default).lower() == true.lower()


class DefaultConfig:
    """Default application configuration (used as template for all
    others).  This is used if the CRUS_CONFIGURATION environment
    variable is unset or is set to 'default' when 'crus' is imported.

    """
    DEBUG = bool_from_env('CRUS_DEBUG', default='no')
    TESTING = bool_from_env('CRUS_TESTING', default='no')
    HTTPS_VERIFY = bool_from_env('UPGRADE_HTTPS_VERIFY', default='no')
    ETCD_HOST = os.environ.get('ETCD_HOST', 'localhost')
    ETCD_PORT = os.environ.get('ETCD_PORT', '2379')
    ETCD_PREFIX = os.environ.get('CRUS_ETCD_PREFIX', '/services/crus')
    ETCD_MOCK_CLIENT = bool_from_env('ETCD_MOCK_CLIENT', default='no')
    API_URI = os.environ.get('CRUS_API_URI', 'api-gw-service-nmn.local/apis')
    MOCK_NODE_GROUP = bool_from_env('CRUS_MOCK_NODE_GROUP', default='no')
    NODE_GROUP_URI = uri_compose("CRUS_NODE_GROUP_URI",
                                 "CRUS_API_URI",
                                 "https://api-gw-service-nmn.local/apis",
                                 "smd/hsm/v1/groups")
    MOCK_BOOT = bool_from_env('CRUS_MOCK_BOOT', default='no')
    UPGRADE_DATA_DIR = os.environ.get('UPGRADE_DATA_DIR', "/upgrade_data")
    BOOT_STATUS_DELAY = float(
        os.environ.get('CRUS_BOOT_STATUS_DELAY', "5.0")
    )
    BOOT_URI = uri_compose("CRUS_BOOT_URI",
                           "CRUS_API_URI",
                           "https://api-gw-service-nmn.local/apis",
                           "boot")
    MOCK_WLM = bool_from_env('CRUS_MOCK_WLM', default='no')
    BSS_NODE_LIST = os.environ.get("CRUS_BSS_NODE_LIST", "unit-test")
    MOCK_BSS_HOSTS = bool_from_env('CRUS_MOCK_BSS_HOSTS', default='no')
    BSS_HOSTS_URI = uri_compose("CRUS_BSS_HOSTS_URI",
                                "CRUS_API_URI",
                                "https://api-gw-service-nmn.local/apis",
                                "bss/boot/v1/hosts")
    BOOT_SESSION_URI = uri_compose("BOOT_SESSION_URI",
                                   "CRUS_API_URI",
                                   "https://api-gw-service-nmn.local/apis",
                                   "bos/v1/session")
    MOCK_BOS_SERVICE = bool_from_env('MOCK_BOS_SERVICE', default='no')
    BOA_JOBS_NAMESPACE = os.environ.get('BOA_JOBS_NAMESPACE', 'services')
    MOCK_KUBERNETES_CLIENT = bool_from_env('MOCK_KUBERNETES_CLIENT', default='no')


class DevelopmentConfig(DefaultConfig):
    """Development application configuration. Set the CRUS_CONFIGURATION
    environment variable to "development" before importing 'crus' to
    use this configuration.

    """
    DEBUG = bool_from_env('CRUS_DEBUG', default='no')
    TESTING = bool_from_env('CRUS_TESTING', default='no')
    HTTPS_VERIFY = bool_from_env('UPGRADE_HTTPS_VERIFY', default='no')
    ETCD_HOST = os.environ.get('ETCD_HOST', 'localhost')
    ETCD_PORT = os.environ.get('ETCD_PORT', '2379')
    ETCD_PREFIX = os.environ.get('CRUS_ETCD_PREFIX', '/services/crus')
    ETCD_MOCK_CLIENT = bool_from_env('ETCD_MOCK_CLIENT', default='no')
    API_URI = os.environ.get('CRUS_API_URI', 'api-gw-service-nmn.local/apis')
    MOCK_NODE_GROUP = bool_from_env('CRUS_MOCK_NODE_GROUP', default='no')
    NODE_GROUP_URI = uri_compose("CRUS_NODE_GROUP_URI",
                                 "CRUS_API_URI",
                                 "https://api-gw-service-nmn.local/apis",
                                 "smd/hsm/v1/groups")
    MOCK_BOOT = bool_from_env('CRUS_MOCK_BOOT', default='no')
    UPGRADE_DATA_DIR = os.environ.get('UPGRADE_DATA_DIR', "/upgrade_data")
    BOOT_STATUS_DELAY = float(
        os.environ.get('CRUS_BOOT_STATUS_DELAY', "5.0")
    )
    BOOT_URI = uri_compose("CRUS_BOOT_URI",
                           "CRUS_API_URI",
                           "https://api-gw-service-nmn.local/apis",
                           "boot")
    MOCK_WLM = bool_from_env('CRUS_MOCK_WLM', default='no')
    BSS_NODE_LIST = os.environ.get("CRUS_BSS_NODE_LIST", "unit-test")
    MOCK_BSS_HOSTS = bool_from_env('CRUS_MOCK_BSS_HOSTS', default='no')
    BSS_HOSTS_URI = uri_compose("CRUS_BSS_HOSTS_URI",
                                "CRUS_API_URI",
                                "https://api-gw-service-nmn.local/apis",
                                "bss/boot/v1/hosts")
    BOOT_SESSION_URI = uri_compose("BOOT_SESSION_URI",
                                   "CRUS_API_URI",
                                   "https://api-gw-service-nmn.local/apis",
                                   "bos/v1/session")
    MOCK_BOS_SERVICE = bool_from_env('MOCK_BOS_SERVICE', default='no')
    MOCK_KUBERNETES_CLIENT = bool_from_env('MOCK_KUBERNETES_CLIENT', default='no')


class TestingConfig(DefaultConfig):
    """Testing application configuration.  Set the CRUS_CONFIGURATION
    environment variable to "testing" before importing 'crus' to use
    this configuration.

    """
    DEBUG = bool_from_env('CRUS_DEBUG', default='no')
    TESTING = bool_from_env('CRUS_TESTING', default='yes')
    HTTPS_VERIFY = bool_from_env('UPGRADE_HTTPS_VERIFY', default='no')
    ETCD_HOST = os.environ.get('ETCD_HOST', 'localhost')
    ETCD_PORT = os.environ.get('ETCD_PORT', '2379')
    ETCD_PREFIX = os.environ.get('CRUS_ETCD_PREFIX', '/services/crus')
    ETCD_MOCK_CLIENT = bool_from_env('ETCD_MOCK_CLIENT', default='yes')
    API_URI = os.environ.get('CRUS_API_URI', 'api-gw-service-nmn.local/apis')
    MOCK_NODE_GROUP = bool_from_env('CRUS_MOCK_NODE_GROUP', default='yes')
    NODE_GROUP_URI = uri_compose("CRUS_NODE_GROUP_URI",
                                 "CRUS_API_URI",
                                 "https://api-gw-service-nmn.local/apis",
                                 "smd/hsm/v1/groups")
    MOCK_BOOT = bool_from_env('CRUS_MOCK_BOOT', default='yes')
    UPGRADE_DATA_DIR = os.environ.get('UPGRADE_DATA_DIR', "/upgrade_data")
    BOOT_STATUS_DELAY = float(
        os.environ.get('CRUS_BOOT_STATUS_DELAY', "5.0")
    )
    BOOT_URI = uri_compose("CRUS_BOOT_URI",
                           "CRUS_API_URI",
                           "https://api-gw-service-nmn.local/apis",
                           "boot")
    MOCK_WLM = bool_from_env('CRUS_MOCK_WLM', default='yes')
    BSS_NODE_LIST = os.environ.get("CRUS_BSS_NODE_LIST", "unit-test")
    MOCK_BSS_HOSTS = bool_from_env('CRUS_MOCK_BSS_HOSTS', default='yes')
    BSS_HOSTS_URI = uri_compose("CRUS_BSS_HOSTS_URI",
                                "CRUS_API_URI",
                                "https://api-gw-service-nmn.local/apis",
                                "bss/boot/v1/hosts")
    API_URI = os.environ.get('CRUS_API_URI', 'api-gw-service-nmn.local/apis')
    MOCK_NODE_GROUP = bool_from_env('CRUS_MOCK_NODE_GROUP', default='yes')
    NODE_GROUP_URI = uri_compose("CRUS_NODE_GROUP_URI",
                                 "CRUS_API_URI",
                                 "https://api-gw-service-nmn.local/apis",
                                 "smd/hsm/v1/groups")
    MOCK_BOOT = bool_from_env('CRUS_MOCK_BOOT', default='yes')
    UPGRADE_DATA_DIR = os.environ.get('UPGRADE_DATA_DIR', "/upgrade_data")
    BOOT_STATUS_DELAY = float(
        os.environ.get('CRUS_BOOT_STATUS_DELAY', "5.0")
    )
    BOOT_URI = uri_compose("CRUS_BOOT_URI",
                           "CRUS_API_URI",
                           "https://api-gw-service-nmn.local/apis",
                           "boot")
    MOCK_WLM = bool_from_env('CRUS_MOCK_WLM', default='yes')
    BSS_NODE_LIST = os.environ.get("CRUS_BSS_NODE_LIST", "unit-test")
    MOCK_BSS_HOSTS = bool_from_env('CRUS_MOCK_BSS_HOSTS', default='yes')
    BSS_HOSTS_URI = uri_compose("CRUS_BSS_HOSTS_URI",
                                "CRUS_API_URI",
                                "https://api-gw-service-nmn.local/apis",
                                "bss/boot/v1/hosts")
    BOOT_SESSION_URI = uri_compose("BOOT_SESSION_URI",
                                   "CRUS_API_URI",
                                   "https://api-gw-service-nmn.local/apis",
                                   "bos/v1/session")
    MOCK_BOS_SERVICE = bool_from_env('MOCK_BOS_SERVICE', default='yes')
    MOCK_KUBERNETES_CLIENT = bool_from_env('MOCK_KUBERNETES_CLIENT', default='yes')


class ProductionConfig(DefaultConfig):
    """Production application configuration.  Set the CRUS_CONFIGURATION
    environment variable to "production" before importing 'crus' to
    use this configuration.

    """
    DEBUG = bool_from_env('CRUS_DEBUG', default='no')
    TESTING = bool_from_env('CRUS_TESTING', default='no')
    HTTPS_VERIFY = bool_from_env('UPGRADE_HTTPS_VERIFY', default='no')
    ETCD_HOST = os.environ.get('ETCD_HOST', 'localhost')
    ETCD_PORT = os.environ.get('ETCD_PORT', '2379')
    ETCD_PREFIX = os.environ.get('CRUS_ETCD_PREFIX', '/services/crus')
    ETCD_MOCK_CLIENT = bool_from_env('ETCD_MOCK_CLIENT', default='no')
    API_URI = os.environ.get('CRUS_API_URI', 'api-gw-service-nmn.local/apis')
    MOCK_NODE_GROUP = bool_from_env('CRUS_MOCK_NODE_GROUP', default='no')
    NODE_GROUP_URI = uri_compose("CRUS_NODE_GROUP_URI",
                                 "CRUS_API_URI",
                                 "https://api-gw-service-nmn.local/apis",
                                 "smd/hsm/v1/groups")
    MOCK_BOOT = bool_from_env('CRUS_MOCK_BOOT', default='no')
    UPGRADE_DATA_DIR = os.environ.get('UPGRADE_DATA_DIR', "/upgrade_data")
    BOOT_STATUS_DELAY = float(
        os.environ.get('CRUS_BOOT_STATUS_DELAY', "5.0")
    )
    BOOT_URI = uri_compose("CRUS_BOOT_URI",
                           "CRUS_API_URI",
                           "https://api-gw-service-nmn.local/apis",
                           "boot")
    MOCK_WLM = bool_from_env('CRUS_MOCK_WLM', default='no')
    BSS_NODE_LIST = os.environ.get("CRUS_BSS_NODE_LIST", "unit-test")
    MOCK_BSS_HOSTS = bool_from_env('CRUS_MOCK_BSS_HOSTS', default='no')
    BSS_HOSTS_URI = uri_compose("CRUS_BSS_HOSTS_URI",
                                "CRUS_API_URI",
                                "https://api-gw-service-nmn.local/apis",
                                "bss/boot/v1/hosts")
    BOOT_SESSION_URI = uri_compose("BOOT_SESSION_URI",
                                   "CRUS_API_URI",
                                   "https://api-gw-service-nmn.local/apis",
                                   "bos/v1/session")
    MOCK_BOS_SERVICE = bool_from_env('MOCK_BOS_SERVICE', default='no')
    MOCK_KUBERNETES_CLIENT = bool_from_env('MOCK_KUBERNETES_CLIENT', default='no')
