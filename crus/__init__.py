"""
Initialization for the Compute Node Uprade Service (CRUS)

Copyright 2019, Cray Inc. All rights reserved.
"""
from .version import VERSION, API_VERSION
from .app import APP
from . import models
from . import views
from .controllers.upgrade_agent.upgrade_agent import watch_sessions
from .controllers.upgrade_agent.errors import ComputeUpgradeError
