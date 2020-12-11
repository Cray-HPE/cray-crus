"""
Initialization for the Compute Node Uprade module

Copyright 2019, Cray Inc. All rights reserved.
"""
from .upgrade_agent.upgrade_agent import watch_sessions
from .upgrade_agent.errors import ComputeUpgradeError
