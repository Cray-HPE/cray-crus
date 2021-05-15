#!/bin/bash
# Copyright 2021 Hewlett Packard Enterprise Development LP
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

OPENAPI_FILE="api/openapi.yaml"
GET_API_VERSION="api/get_api_version.py"
API_VERSION_TMPFILE=".api_version"
CONSTRAINTS_TMPFILE="constraints-tmp.txt"

# Need to get the API version from the openapi file
# Create a constraints file without the crus package in it, since we haven't updated
# that line yet
if ! grep -v "^crus==" constraints.txt > ${CONSTRAINTS_TMPFILE} ; then
    echo "Unable to generate ${CONSTRAINTS_TMPFILE}"
    exit 1
fi

pip3 install --no-cache-dir -c ${CONSTRAINTS_TMPFILE} pip setuptools
pip3 install --no-cache-dir -c ${CONSTRAINTS_TMPFILE} PyYAML
if ./${GET_API_VERSION} ${OPENAPI_FILE} > ${API_VERSION_TMPFILE} ; then
    echo "API version string is $(cat ${API_VERSION_TMPFILE})"
else
    echo "Unable to get API version from openapi file"
    exit 1
fi

./install_cms_meta_tools.sh || exit 1
./cms_meta_tools/update_versions/update_versions.sh || exit 1
rm -rf ./cms_meta_tools ${API_VERSION_TMPFILE} ${CONSTRAINTS_TMPFILE}
exit 0
