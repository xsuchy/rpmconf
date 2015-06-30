Name:           rpmconf
Summary:        Tool to handle rpmnew and rpmsave files
License:        GPLv3
Version:        1.0.11
Release:        1%{?dist}
URL:            http://wiki.github.com/xsuchy/rpmconf
# source is created by:
# git clone https://github.com/xsuchy/rpmconf.git
# cd rpmconf; tito build --tgz
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  docbook-utils
BuildRequires:  docbook-dtd31-sgml
BuildRequires:  python3-sphinx
BuildRequires:  python3-devel
Requires:       %{name}-base
Requires:       python3-rpmconf
Requires:       rpm-python3
BuildRequires:  rpm-python3
#check
BuildRequires:  python3-pylint
BuildRequires:  python3-six
# mergetools
Suggests: diffuse 
Suggests: kdiff3
Suggests: meld
Suggests: vim-X11
Suggests: vim-enhanced

%description
This tool search for .rpmnew, .rpmsave and .rpmorig files and ask you what to do
with them:
Keep current version, place back old version, watch the diff or merge.

%package -n python3-rpmconf
Summary:        Python interface for %{name}
BuildArch:      noarch

%description -n python3-rpmconf
Python interface for %{name}. Mostly useful for developers only.

%package -n python3-rpmconf-doc
Summary:        Documentation of python interface for %{name}
BuildArch:      noarch

%description -n python3-rpmconf-doc
Documentation generated from code of python3-rpmconf.

%package base
Summary: Filesystem for %{name}
BuildArch: noarch

%description base
Directory hierarchy for installation scripts, which are handled by rpmconf.

%prep
%setup -q

%build
%{__python3} setup.py build
docbook2man rpmconf.sgml
make -C docs html man

%install
%{__python3} setup.py install --skip-build \
    --install-scripts %{_sbindir} \
    --root %{buildroot}
install -D -m 644 rpmconf.8 %{buildroot}%{_mandir}/man8/rpmconf.8
install -D -m 644 docs/build/man/rpmconf.3 %{buildroot}%{_mandir}/man3/rpmconf.3
mkdir -p %{buildroot}%{_datadir}/rpmconf/

%check
python3-pylint --reports=n %{buildroot}%{_sbindir}/rpmconf
python3-pylint --reports=n %{buildroot}%{python3_sitelib}/rpmconf/rpmconf.py

%files
%license LICENSE
%{_sbindir}/rpmconf
%{_mandir}/man8/rpmconf.8*

%files -n python3-rpmconf
%license LICENSE
%{python3_sitelib}/rpmconf/
%{python3_sitelib}/rpmconf-*.egg-info
%{_mandir}/man3/rpmconf.3*

%files -n python3-rpmconf-doc
%license LICENSE
%doc docs/build/html/

%files base
%dir %{_datadir}/rpmconf

%changelog
* Tue Jun 30 2015 Miroslav Suchý <msuchy@redhat.com> 1.0.11-1
- disable pylint warning

* Tue Jun 30 2015 Miroslav Suchý <miroslav@suchy.cz> 1.0.10-1
- 1236722 - other method for stdin flush and handle Ctrl+C correctly

* Mon Jun 01 2015 Miroslav Suchý <msuchy@redhat.com> 1.0.9-1
- pylint: let the logger expand params
- use soft deps

* Mon Jun 01 2015 Miroslav Suchý <msuchy@redhat.com> 1.0.8-1
- 1226591 - do not flush stdin, when it is not TTY
- BR python3-six
- minor fixes
- use RPM Python API to get package name of file

* Mon Jan 12 2015 Miroslav Suchý <miroslav@suchy.cz> 1.0.7-1
- correctly reference tar.gz
- add / before usr/bin
- remove superfluous changelog line

* Fri Jan 09 2015 Miroslav Suchý <miroslav@suchy.cz> 1.0.6-1
- let tito bump up version in docs/source/conf.py

* Thu Jan 08 2015 Miroslav Suchý <miroslav@suchy.cz> 1.0.5-1
- add -doc subpackage
- mark LICENSE as %%license
- Split to python class and CLI
- use rpm python api to get version

* Sun Nov 23 2014 Miroslav Suchý <msuchy@redhat.com> 1.0.4-1
- add BR rpm-python3

* Sun Nov 23 2014 Miroslav Suchý <miroslav@suchy.cz> 1.0.3-1
- Allow specification of a custom merge type via an environment variable,
  $MERGE
- do not remove files on those merge tools, which does not return correct exit
  code
- make pylint run mandatory
- skip /var/lib/mock when --clean
- use rpm bindings to find configfiles
- use filecmp instead of subprocessed diff

* Tue Nov 04 2014 Miroslav Suchý <msuchy@redhat.com> 1.0.2-1
- require rpm-python3

* Wed Oct 29 2014 Miroslav Suchý <msuchy@redhat.com> 1.0.1-1
- migrate to python3
- handle symlinks correctly

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

