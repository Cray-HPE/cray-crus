## Cray Compute Rolling Upgrade Service Dockerfile
## Copyright 2019-2021 Hewlett Packard Enterprise Development LP

# Create 'base' image target
ARG BASE_IMAGE=dtr.dev.cray.com:443/baseos/sles15sp1:sles15sp1
FROM $BASE_IMAGE as base
ENV PIP_INDEX_URL=https://arti.dev.cray.com:443/artifactory/api/pypi/pypi-remote/simple
ENV PIP_EXTRA_INDEX_URL=https://arti.dev.cray.com/artifactory/internal-pip-master-local
ARG SLURM_REPO=http://car.dev.cray.com/artifactory/wlm-slurm/RM/sle15_sp1_cn/x86_64/dev/master/
RUN zypper ar --gpgcheck-allow-unsigned $SLURM_REPO wlm_slurm && \
    zypper --non-interactive install --recommends python3 python3-devel python3-pip slurm && \
    pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org && \
    zypper clean -a

WORKDIR /app
RUN mkdir -p /app/crus
COPY setup.py requirements.txt constraints.txt /app/crus/
COPY crus /app/crus/crus
RUN cd /app/crus && pip3 install . && pip install -r requirements.txt
COPY entrypoints /app/entrypoints

# Run unit tests
FROM base as testing
COPY tests /app/crus/tests
COPY noxfile.py /app/crus/
COPY .coveragerc .pylintrc .pycodestyle setup.py /app/crus/
COPY requirements-test.txt requirements-lint.txt requirements-style.txt /app/crus/
ARG FORCE_TESTS=null

# The nox run won't use virtual environments, so we need to have the test, lint
# and style requirements installed in the testing image before we run the tests
RUN pip3.6 install nox && \
    pip3.6 install --upgrade -r /app/crus/requirements-test.txt && \
    pip3.6 install --upgrade -r /app/crus/requirements-lint.txt && \
    pip3.6 install --upgrade -r /app/crus/requirements-style.txt
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
