"""
Initialization for the views sub-module of CRUS

Copyright 2019, Cray Inc. All rights reserved.
"""
from ..app import add_paths, install_swagger
from . import upgrade_session
from . import swagger

# Set swagger paths
add_paths(swagger.PATHS)
add_paths(upgrade_session.PATHS)
install_swagger()
