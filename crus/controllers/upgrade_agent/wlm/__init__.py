"""
Initialization for the Compute Node Uprade WLM sub-Module

Copyright 2019, Cray Inc. All rights reserved.
"""
from .wlm import get_wlm_handler
from .wrap_shell import shell
from .slurm import SlurmHandler  # just so we register Slurm
