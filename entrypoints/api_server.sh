#! /bin/sh

# Copyright 2019, Cray Inc. All rights reserved.

exec gunicorn --bind=0.0.0.0:8080 --workers=1 crus:APP
