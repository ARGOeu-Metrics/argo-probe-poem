# sitelib
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define dir /usr/libexec/argo/probes/poem

Name: argo-probe-poem
Summary: Multi-tenant aware probes checking ARGO POEM.
Version: 0.1.0
Release: 1%{?dist}
License: ASL 2.0
Source0: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Group: Network/Monitoring
BuildArch: noarch
Requires: python-requests, python-argparse, pyOpenSSL

%description
This package includes probes that check ARGO POEM component.
Currently it contains two probes:
 - poem-cert-probe
 - poem-metricapi-probe

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install --skip-build --root %{buildroot} --record=INSTALLED_FILES
install -d -m 755 %{buildroot}/%{dir}
install -d -m 755 %{buildroot}/%{python_sitelib}/argo_probe_poem

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root,-)
%{python_sitelib}/argo_probe_poem
%{dir}


%changelog
* Thu Jun 9 2021 Katarina Zailac <kzailac@gmail.com> - 0.1.0-1%{?dist}
- AO-650 Harmonize argo-mon probes
