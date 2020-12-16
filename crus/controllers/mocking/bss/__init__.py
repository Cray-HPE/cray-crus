"""
Initialization for the Boot Orchestration Mock module

Copyright 2019, Cray Inc. All rights reserved.
"""
from .bss_api import start_service
from .bss_nodes import BSSNodeTable

start_service()
BSSNodeTable.create()
