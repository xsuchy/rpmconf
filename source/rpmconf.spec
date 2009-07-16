Name: rpmconf
Summary: Tool to handle rpmnew and rpmsave files
Group:   Applications/System
License: GPLv3
Version: 0.1.0
Release: 1%{?dist}
URL:     http://wiki.github.com/xsuchy/rpmconf
Source0: http://cloud.github.com/downloads/xsuchy/rpmconf/%{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-root-%(%{__id_u} -n)
BuildArch: noarch
Requires: perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))

%description
This tool seach for .rpmnew and .rpmsave files and ask you what to do with them.
Keep current version, place back old version or watch the diff.

%prep
%setup -q

%build
#/usr/bin/docbook2man rpmconf.sgml
#/usr/bin/gzip rpmconf.8

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man8
mkdir -p $RPM_BUILD_ROOT/%{_usr}/sbin
install -m 755 rpmconf $RPM_BUILD_ROOT%{_usr}/sbin
#install -m 644 rpmconf.8.gz $RPM_BUILD_ROOT%{_mandir}/man8/

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%dir %{defaultdir}
%{_usr}/sbin/*
%{_mandir}/man8/*

%changelog
* Thu Jul 16 2009 Miroslav Suchy <msuchy@redhat.com>
- initial version

