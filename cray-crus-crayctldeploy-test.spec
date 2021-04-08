# Copyright 2020 Hewlett Packard Enterprise Development LP

Name: cray-crus-crayctldeploy-test
License: MIT
Summary: Cray post-install tests for Compute Rolling Upgrade Service (CRUS)
Group: System/Management
Version: %(cat .rpm_version_cray-crus-crayctldeploy-test)
Release: %(echo ${BUILD_METADATA})
Source: %{name}-%{version}.tar.bz2
Vendor: Cray Inc.
Requires: bos-crayctldeploy-test >= 0.1.3
Requires: cray-cmstools-crayctldeploy-test >= 0.1.1
Requires: python3-requests

# Test defines. These may make sense to put in a central location
%define tests /opt/cray/tests
%define smslong %{tests}/sms-long
%define testlib %{tests}/lib

# CMS test defines
%define smslongcms %{smslong}/cms
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
# Install long run tests
install -m 755 -d %{buildroot}%{smslongcms}/
install ct-tests/crus_integration_api_test.sh %{buildroot}%{smslongcms}
install ct-tests/crus_integration_cli_test.sh %{buildroot}%{smslongcms}

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
install -m 644 ct-tests/lib/crus_integration_test/bos.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/crus.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/hsm.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/slurm.py %{buildroot}%{crusinttestlib}
install -m 644 ct-tests/lib/crus_integration_test/utils.py %{buildroot}%{crusinttestlib}

%clean
rm -f  %{buildroot}%{smslongcms}/crus_integration_api_test.sh
rm -f  %{buildroot}%{smslongcms}/crus_integration_cli_test.sh
rm -f %{buildroot}%{cmscommon}/crus.py
rm -f %{buildroot}%{cmslib}/crus_integration_test.py
rm -f %{buildroot}%{crusinttestlib}/__init__.py
rm -f %{buildroot}%{crusinttestlib}/argparse.py
rm -f %{buildroot}%{crusinttestlib}/bos.py
rm -f %{buildroot}%{crusinttestlib}/crus.py
rm -f %{buildroot}%{crusinttestlib}/hsm.py
rm -f %{buildroot}%{crusinttestlib}/slurm.py
rm -f %{buildroot}%{crusinttestlib}/utils.py
rmdir %{buildroot}%{crusinttestlib}

%files
%defattr(755, root, root)
%dir %{crusinttestlib}
%attr(755, root, root) %{smslongcms}/crus_integration_api_test.sh
%attr(755, root, root) %{smslongcms}/crus_integration_cli_test.sh
%attr(644, root, root) %{cmscommon}/crus.py
%attr(755, root, root) %{cmslib}/crus_integration_test.py
%attr(644, root, root) %{crusinttestlib}/__init__.py
%attr(644, root, root) %{crusinttestlib}/argparse.py
%attr(644, root, root) %{crusinttestlib}/bos.py
%attr(644, root, root) %{crusinttestlib}/crus.py
%attr(644, root, root) %{crusinttestlib}/hsm.py
%attr(644, root, root) %{crusinttestlib}/slurm.py
%attr(644, root, root) %{crusinttestlib}/utils.py

%changelog
