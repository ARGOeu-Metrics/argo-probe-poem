# sitelib
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
BuildRequires: python3-devel
Requires: python36-requests, python36-pyOpenSSL

%description
This package includes probes that check ARGO POEM component.
Currently it contains two probes:
 - poem-cert-probe
 - poem-metricapi-probe

%prep
%setup -q

%build
%{py3_build}

%install
%{py3_install "--record=INSTALLED_FILES" }

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root,-)
%{python3_sitelib}/argo_probe_poem
%{dir}


%changelog
* Thu Jun 9 2021 Katarina Zailac <kzailac@gmail.com> - 0.1.0-1%{?dist}
- AO-650 Harmonize argo-mon probes
