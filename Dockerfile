# Cray Compute Rolling Upgrade Service Dockerfile
# Copyright 2019-2021 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

# Create 'base' image target
ARG BASE_IMAGE=arti.dev.cray.com/baseos-docker-master-local/sles15sp3:sles15sp3
FROM $BASE_IMAGE as base
ARG SLURM_REPO=http://car.dev.cray.com/artifactory/wlm-slurm/RM/sle15_sp2_cn/x86_64/release/wlm-slurm-1.0/
RUN zypper --non-interactive install --recommends bash curl rpm && \
    curl -XGET "https://arti.dev.cray.com:443/artifactory/dst-misc-stable-local/SigningKeys/HPE-SHASTA-RPM-PROD.asc" --output HPE-SHASTA-RPM-PROD.asc && \
    rpm --import HPE-SHASTA-RPM-PROD.asc && \
    zypper ar --gpgcheck-allow-unsigned $SLURM_REPO wlm_slurm && \
    zypper refresh && \
    zypper --non-interactive install --recommends python3 python3-devel python3-pip slurm && \
    pip3 install --no-cache-dir -U pip

# Apply security patches
COPY cms_meta_tools/utils/zypper-patch.sh /
RUN /zypper-patch.sh && rm /zypper-patch.sh

WORKDIR /app
RUN mkdir -p /app/crus
COPY setup.py requirements.txt constraints.txt /app/crus/
COPY crus /app/crus/crus
RUN cd /app/crus && pip3 install -r requirements.txt . && pip3 list --format freeze
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
RUN groupadd -g 65534 nobody && useradd -u 65534 -g nobody nobody && chown -R nobody:nobody /app
USER 65534:65534
COPY config/gunicorn.py /app/
ENTRYPOINT ["/app/entrypoints/api_server.sh"]
