#! /bin/sh

# Copyright 2019, Cray Inc. All rights reserved.

# for some reason, when the controller starts right up, it has
# problems talking to etcd and slurm (CASMCLOUD-858), but when it
# waits a little bit, it has no problems.  Until this is resolved,
# wait 30 seconds before starting...
sleep 30
python -m crus.controller
