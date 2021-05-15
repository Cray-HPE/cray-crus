# Copyright 2020-2021 Hewlett Packard Enterprise Development LP
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

Name: cray-crus-crayctldeploy-test
License: MIT
Summary: Cray post-install tests for Compute Rolling Upgrade Service (CRUS)
Group: System/Management
# The placeholder version string will be replaced at build time by
# the runBuildPrep.sh script
Version: %(cat .version)
Release: %(echo ${BUILD_METADATA})
Source: %{name}-%{version}.tar.bz2
Vendor: Cray Inc.
Requires: bos-crayctldeploy-test >= 0.2.9
Requires: cray-cmstools-crayctldeploy-test >= 1.0.1
Requires: python3-requests

# Test defines. These may make sense to put in a central location
%define tests /opt/cray/tests
%define smslong %{tests}/sms-long
%define testlib %{tests}/lib

# CMS test defines
%define cmslib %{testlib}/cms
%define cmscommon %{cmslib}/common

# CRUS test defines
%define crusinttestlib %{cmslib}/crus_integration_test

%description
This is a collection of post-install tests for Compute Rolling Upgrade Service (CRUS).

%prep
%setup -q

%build

%install
# Install shared test libraries
# The cmscommon directory should already exist, since we have
# cray-cmstools-crayctldeploy-test as a prerequisite, but just in
# case...
install -m 755 -d %{buildroot}%{cmscommon}/
install -m 644 ct-tests/lib/common/crus.py %{buildroot}%{cmscommon}

# Install CRUS integration test modules
install -m 755 -d %{buildroot}%{crusinttestlib}/
install -m 755 ct-tests/lib/crus_integration_test.py %{buildroot}%{cmslib}
install -m 644 ct-tests/lib/crus_integration_test/__init__.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/argparse.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/crus.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/hsm.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/slurm.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/utils.py %{buildroot}%{crusinttestlib}

%clean
rm -f %{buildroot}%{cmscommon}/crus.py
rm -f %{buildroot}%{cmslib}/crus_integration_test.py
rm -f %{buildroot}%{crusinttestlib}/__init__.py
rm -f %{buildroot}%{crusinttestlib}/argparse.py
rm -f %{buildroot}%{crusinttestlib}/crus.py
rm -f %{buildroot}%{crusinttestlib}/hsm.py
rm -f %{buildroot}%{crusinttestlib}/slurm.py
rm -f %{buildroot}%{crusinttestlib}/utils.py
rmdir %{buildroot}%{crusinttestlib}

%files
%defattr(755, root, root)
%dir %{crusinttestlib}
%attr(644, root, root) %{cmscommon}/crus.py
%attr(755, root, root) %{cmslib}/crus_integration_test.py
%attr(644, root, root) %{crusinttestlib}/__init__.py
%attr(644, root, root) %{crusinttestlib}/argparse.py
%attr(644, root, root) %{crusinttestlib}/crus.py
%attr(644, root, root) %{crusinttestlib}/hsm.py
%attr(644, root, root) %{crusinttestlib}/slurm.py
%attr(644, root, root) %{crusinttestlib}/utils.py

%changelog
