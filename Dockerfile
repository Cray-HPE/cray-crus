## Cray Compute Rolling Upgrade Service Dockerfile
## Copyright 2019, Cray Inc. All rights reserved.

# Create 'base' image target
ARG BASE_IMAGE=dtr.dev.cray.com:443/dst/centos7_epel_dst_repo:v1.0
FROM $BASE_IMAGE as base
ARG SLURM_REPO=http://car.dev.cray.com/artifactory/shasta-premium/RM/centos_7_5_ncn/x86_64/dev/master/
# gcc and python-devel are needed for grpcio installation and pylint installation
RUN yum-config-manager --add-repo $SLURM_REPO && \
    yum install --disableplugin=fastestmirror --nogpgcheck -y slurm yum-utils && \
    yum install --disableplugin=fastestmirror --nogpgcheck -y python36 python36-devel && \
    yum install --disableplugin=fastestmirror --nogpgcheck -y gcc gcc-c++ && \
    yum clean all

# Make python3.6 default
RUN ln -sf /usr/bin/python3.6 /usr/bin/python

WORKDIR /app
RUN python3.6 -m ensurepip
RUN pip3.6 install --upgrade pip
RUN pip3.6 install --upgrade gunicorn
RUN mkdir -p /app/crus
COPY setup.py /app/crus/
COPY crus /app/crus/crus
RUN cd /app/crus && pip3.6 install .
COPY entrypoints /app/entrypoints

# Run unit tests
FROM base as testing
COPY tests /app/crus/tests
COPY noxfile.py /app/crus/
COPY .coveragerc .pylintrc .pycodestyle setup.py /app/crus/
COPY requirements-test.txt requirements-lint.txt requirements-style.txt /app/crus/
ARG FORCE_TESTS=null
RUN pip3.6 install nox
# The nox run won't use virtual environments, so we need to have the test, lint
# and style requirements installed in the testing image before we run the tests
RUN pip3.6 install --upgrade -r /app/crus/requirements-test.txt
RUN pip3.6 install --upgrade -r /app/crus/requirements-lint.txt
RUN pip3.6 install --upgrade -r /app/crus/requirements-style.txt
# Now run the tests. This covers lint, style, unit tests and coverage.  The
# environment variable setting tells my noxfile not to use virtual envs for
# running the sessions inside.
RUN cd /app/crus && NOX_DOCKER_BUILD=yes nox

# Create the actual application layer.  This will run the API server (view),
# to run the Upgrade Controller override the entrypoint using
#
#     /app/entrypoints/controller.sh
FROM base as app
ENTRYPOINT ["/app/entrypoints/api_server.sh"]
