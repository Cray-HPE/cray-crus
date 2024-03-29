#
# MIT License
#
# (C) Copyright 2019-2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# Cray Compute Rolling Upgrade Service Dockerfile

# Create 'base' image target
ARG BASE_IMAGE=arti.hpc.amslabs.hpecorp.net/baseos-docker-master-local/sles15sp4:sles15sp4
FROM $BASE_IMAGE as base
ARG SLURM_REPO=https://arti.hpc.amslabs.hpecorp.net/artifactory/wlm-slurm-rpm-stable-local/release/wlm-slurm-1.2/sle15_sp4_cn/
RUN zypper --non-interactive ar --gpgcheck-allow-unsigned $SLURM_REPO wlm_slurm && \
    zypper --non-interactive refresh && \
    zypper --non-interactive install --recommends bash curl rpm && \
    curl -XGET "https://arti.hpc.amslabs.hpecorp.net:443/artifactory/dst-misc-stable-local/SigningKeys/HPE-SHASTA-RPM-PROD.asc" --output HPE-SHASTA-RPM-PROD.asc && \
    rpm --import HPE-SHASTA-RPM-PROD.asc && \
    zypper --non-interactive install --recommends python3 python3-devel python3-pip slurm && \
    pip3 install --no-cache-dir -U pip

# The current sles15sp4 base image starts with a lock on coreutils, but this prevents a necessary
# security patch from being applied. Thus, adding this command to remove the lock if it is 
# present.
RUN zypper --non-interactive removelock coreutils || true

# Apply security patches
COPY zypper-refresh-patch-clean.sh /
RUN /zypper-refresh-patch-clean.sh && rm /zypper-refresh-patch-clean.sh

WORKDIR /app
RUN mkdir -p /app/crus
COPY setup.py requirements.txt constraints.txt /app/crus/
COPY crus /app/crus/crus
RUN --mount=type=secret,id=netrc,target=/root/.netrc cd /app/crus && pip3 install -r requirements.txt . && pip3 list --format freeze
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

# Add 'nobody' group with specified group ID, if it does not already exist
RUN grep -E "^nobody:[^:]*:65534:" /etc/group || groupadd -g 65534 nobody

# Add 'nobody' user with specified user ID and group, if it does not already exist
RUN grep -E "^nobody:[^:]*:65534:" /etc/passwd|| useradd -u 65534 -g nobody nobody

# In case the 'nobody' user already existed, make sure it belongs to 'nobody' group
RUN usermod -g nobody nobody

RUN chown -R nobody:nobody /app

USER 65534:65534
COPY config/gunicorn.py /app/
ENTRYPOINT ["/app/entrypoints/api_server.sh"]
