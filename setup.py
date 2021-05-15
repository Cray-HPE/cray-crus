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

from setuptools import setup, find_packages

with open('crus/version.py') as vers_file:
    exec(vers_file.read())  # Get VERSION and API_VERSION from version.py

setup(
    name='crus',
    version=VERSION,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        "marshmallow",
        "shell",
        "apispec >= 0.39.0, < 1",
        "Flask",
        "Flask-RESTful",
        "flask-restful-swagger-2",
        "flask-swagger-ui",
        "flask-marshmallow",
        "etcd3",
        "httpproblem",
        "PyYAML",
        "urllib3",
        "etcd3_model",
        "kubernetes"
    ]
)
