Name: rpmconf
Summary: Tool to handle rpmnew and rpmsave files
Group:   Applications/System
License: GPLv3
Version: 0.2.1
Release: 1%{?dist}
URL:     http://wiki.github.com/xsuchy/rpmconf
Source0: http://cloud.github.com/downloads/xsuchy/rpmconf/%{name}-%{version}.tar.gz
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch: noarch
Requires: perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))
BuildRequires: docbook-utils
BuildRequires: docbook-dtd31-sgml

%description
This tool seach for .rpmnew, .rpmsave and .rpmorig files and ask you what to do
with them:
Keep current version, place back old version, watch the diff or merge.

%prep
%setup -q

%build
docbook2man rpmconf.sgml

%install
rm -rf $RPM_BUILD_ROOT
install -D -m 755 rpmconf $RPM_BUILD_ROOT%{_sbindir}/rpmconf
install -D -m 644 rpmconf.8 $RPM_BUILD_ROOT%{_mandir}/man8/rpmconf.8

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_sbindir}/rpmconf
%{_mandir}/man8/rpmconf.8*
%doc LICENSE

%changelog
* Thu Jan  7 2010 Miroslav Suchy <msuchy@redhat.com> 0.2.1-1
- implement merging of files using vimdiff, gvimdiff, meld,
  and kdiff3
- added command line option --version
- added command line option --debug
- fix build requires on Mandriva

* Mon Aug 31 2009 Miroslav Suchy <msuchy@redhat.com> 0.1.8-1
- fix copy and past typo

* Fri Aug 28 2009 Miroslav Suchy <msuchy@redhat.com> 0.1.7-1
- add support for handling .rpmorig
- 513794 - localisation problem
- add support for suspending script

* Fri Jul 17 2009 Miroslav Suchy <msuchy@redhat.com> 0.1.6-1
- addressed fedora package review notes (#7)

* Thu Jul 16 2009 Miroslav Suchy <msuchy@redhat.com> 0.1.5-1
- addressed fedora package review notes

* Thu Jul 16 2009 Miroslav Suchy <msuchy@redhat.com> 0.1.3-1
- initial version

