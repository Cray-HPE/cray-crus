"""
Initialization for the Boot Orchestration Mock module

Copyright 2019, Cray Inc. All rights reserved.
"""
from .bos_api import start_service
from .bos_session_table import BootSessionTable
from .bos_template_table import BootTemplateTable

start_service()
