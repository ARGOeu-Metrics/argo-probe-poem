# sitelib
%define dir /usr/libexec/argo/probes/poem

Name:          argo-probe-poem
Summary:       Multi-tenant aware probes checking ARGO POEM.
Version:       0.2.1
Release:       1%{?dist}
License:       ASL 2.0
Source0:       %{name}-%{version}.tar.gz
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root
Group:         Network/Monitoring
BuildArch:     noarch
BuildRequires: python3-devel
Requires:      python3-requests, python3-pyOpenSSL


%description
This package includes probes that check ARGO POEM component.
Currently it contains three probes:
 - poem-cert-probe
 - poem-metricapi-probe
 - poem-probecandidate-probe

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
* Thu Apr 4 2024 Katarina Zailac <kzailac@srce.hr> - 0.2.1-1%{?dist}
- AO-926 Create Rocky 9 rpm for argo-probe-poem
* Thu Jul 6 2023 Katarina Zailac <kzailac@srce.hr> - 0.2.0-1%{?dist}
- ARGO-4319 Create probe that checks if there are pending probe candidates
- ARGO-4125 Configure POEM probe test execution
- ARGO-4120  Various poem-sensor fixes
- ARGO-4118 Bump poem sensor to Python3 and use TLSv1.2
- ARGO-3988 Switch argo-probe-poem to Py3
* Thu Jun 9 2021 Katarina Zailac <kzailac@gmail.com> - 0.1.0-1%{?dist}
- AO-650 Harmonize argo-mon probes
