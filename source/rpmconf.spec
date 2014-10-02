Name: rpmconf
Summary: Tool to handle rpmnew and rpmsave files
Group:   Applications/System
License: GPLv3
Version: 0.3.7
Release: 1%{?dist}
URL:     http://wiki.github.com/xsuchy/rpmconf
Source0: http://cloud.github.com/downloads/xsuchy/rpmconf/%{name}-%{version}.tar.gz
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch: noarch
BuildRequires: docbook-utils
BuildRequires: docbook-dtd31-sgml
Requires: %{name}-base

%description
This tool search for .rpmnew, .rpmsave and .rpmorig files and ask you what to do
with them:
Keep current version, place back old version, watch the diff or merge.

%package base
Summary: Filesystem for %{name}
Group: Applications/System
BuildArch: noarch

%description base
Directory hierarchy for installation scripts, which are handled by rpmconf.

%prep
%setup -q

%build
docbook2man rpmconf.sgml

%install
rm -rf $RPM_BUILD_ROOT
install -D -m 755 rpmconf %{buildroot}%{_sbindir}/rpmconf
install -D -m 644 rpmconf.8 %{buildroot}%{_mandir}/man8/rpmconf.8

mkdir %{buildroot}%{_datadir}/rpmconf

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{_sbindir}/rpmconf
%{_mandir}/man8/rpmconf.8*
%doc LICENSE

%files base
%dir %{_datadir}/rpmconf

%changelog
* Thu Oct 02 2014 Miroslav Suchý 0.3.7-1
- when there is no error return 0

* Sun Jan 12 2014 Miroslav Suchý <miroslav@suchy.cz> 0.3.6-1
- add non-interactive --diff mode
- remove some white space in NAME section
- remove garbage from man page
- rpmconf-base should not require rpmconf

* Thu Jul 25 2013 Miroslav Suchý <msuchy@redhat.com> 0.3.5-1
- add ability to configure packages
- replace old macro RPM_BUILD_ROOT
- create subpackage -base which will own /usr/share/rpmconf
- document ability to handle app configuration

* Mon Jul 15 2013 Miroslav Suchý <miroslav@suchy.cz>
- When overwriting the current file with an .rpmnew/.rpmsave file, check that
  the copy worked before removing the source file.
- Skip deleting files if user input could not be read.
- fix few spelling typos

* Fri Jul 08 2011 Miroslav Suchý 0.3.3-1
- Revert "change download location to github magic url"

* Fri Jul 08 2011 Miroslav Suchý 0.3.2-1
- change download location to github magic url

* Fri Jul 08 2011 Miroslav Suchý 0.3.1-1
- bump up version
- add warning about --debug position sensitivity
- scan /usr during --clean
- introduce new option -Z to print SELinux context of old and new file
- do not dereference links
- allow another option : skip the current config file and go to the next one
- show config file dates
- we do not need perl
- --clean - Find and delete orphaned .rpmnew and .rpmsave files.
- fix spelling error

* Mon Feb 22 2010 Miroslav Suchy <msuchy@redhat.com> 0.2.2-1
- 567318 - fix syntax error
- add diffuse as merge frontend

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

