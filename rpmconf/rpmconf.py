#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: noai:ts=4:sw=4:expandtab
# pylint: disable=missing-docstring,too-many-arguments,too-many-branches
#
# Copyright (C) 2014 Miroslav Suchy <msuchy@redhat.com>
# Copyright (C) 2015 Igor Gnatenko <i.gnatenko.brain@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Red Hat trademarks are not licensed under GPLv3. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.

import difflib
import filecmp
import logging
import os
import pydoc
import rpm
import shutil
import signal
import select
import subprocess
import sys
import termios
import time
import tty

__version__ = "1.0.90"
#uncomment when rpm 4.13 is available
#rpm.setInterruptSafety(False)

class RpmConf(object):
    """

    :param packages: Check only configuration files of given packages.
    :type packages: list
    :param clean: Find and delete orphaned .rpmnew and .rpmsave files.
    :type clean: bool
    :param debug: Dry run. Just show which files will be deleted.
    :type debug: bool
    :param selinux: Display SELinux context of old and new file.
    :type selinux: bool
    :param diff: Non-interactive diff mode. Useful to audit configs.
    :type diff: bool
    :param frontend: Define which frontend should be used for merging.
    :type frontend: str
    :ivar packages: :class:`list` of :class:`rpm.mi`
    :ivar clean: :class:`bool`
    :ivar diff: :class:`bool`
    :ivar frontend: :class:`str`
    :ivar selinux: :class:`bool`
    :ivar debug: :class:`bool`
    :ivar logger: :class:`logging.Logger`

    """
    def __init__(self, packages=None, clean=False, debug=False, selinux=False,
                 diff=False, frontend=None):
        trans = rpm.TransactionSet()
        if not packages:
            self.packages = [trans.dbMatch()] # pylint: disable=no-member
        else:
            self.packages = []
            for pkg in packages:
                tmp = trans.dbMatch("name", pkg) # pylint: disable=no-member
                self.packages.append(tmp)
        self.clean = clean
        self.diff = diff
        self.frontend = frontend
        self.selinux = selinux
        self.debug = debug
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("rpmconf")

    def run(self):
        """Main function to proceed"""
        for pkg in self.packages:
            for pkg_hdr in pkg:
                self._handle_package(pkg_hdr)
        if self.clean:
            self._clean_orphan()

    @staticmethod
    def flush_input(question):
        """Flush stdin and then as the question.

        :param question: String to ask
        :type question: str
        :return: User string
        :rtype: str

        """
        if os.isatty(sys.stdin.fileno()):
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno(), termios.TCSANOW)
                while select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    sys.stdin.read(1)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSANOW, old_settings)
        # BZ 1237075 workaround
        signal.signal(signal.SIGINT, signal.default_int_handler)
        return input(question)

    @staticmethod
    def get_list_of_config(package):
        """Get all files marked as config in package

        :param package: RPM Header of package
        :type package: rpm.hdr
        :return: Strings list of files marked as config in package
        :rtype: list

        """
        files = rpm.fi(package) # pylint: disable=no-member
        result = []
        for rpm_file in files:
            if rpm_file[4] & rpm.RPMFILE_CONFIG: # pylint: disable=no-member
                result.append(rpm_file[0])
        return result

    def show_diff(self, file1, file2):
        """Show differences between two files.

        :param file1: Path to first file
        :type file1: str
        :param file2: Path to second file
        :type file2: str

        """
        err_msg_template = "Warning: file {} is broken symlink. I'm using /dev/null instead.\n"
        err_msg = ""
        if os.path.islink(file1):
            err_msg += "Info: '{0}' is symlink to '{1}'.\n".format(file1, os.readlink(file1))
            if self.is_broken_symlink(file1):
                fromdate = time.ctime(os.stat(file1).st_mtime)
            else:
                fromdate = None
                err_msg += err_msg_template.format(file1)
                file1 = "/dev/null"
        if os.path.islink(file2):
            err_msg += "Info: '{0}' is symlink to '{1}'.\n".format(file2, os.readlink(file2))
            if self.is_broken_symlink(file2):
                todate = time.ctime(os.stat(file2).st_mtime)
            else:
                todate = None
                err_msg += err_msg_template.format(file2)
                file2 = "/dev/null"
        try:
            fromlines = open(file1, "U").readlines()
            tolines = open(file2, "U").readlines()
            diff = difflib.unified_diff(fromlines, tolines,
                                        file1, file2,
                                        fromdate, todate)
        except UnicodeDecodeError:
            # binary files
            diff_out = subprocess.Popen(["/usr/bin/diff", "-u", file1, file2],
                                        stdout=subprocess.PIPE,
                                        universal_newlines=True)
            diff = diff_out.communicate()[0]
        pydoc.pager(err_msg + "".join(diff))

    @staticmethod
    def is_broken_symlink(file1):
        """ Returns true if file is broken symlink. False otherwise. """
        #pylint: disable=no-member
        return os.path.islink(file1) and os.path.exists(file1)

    def _show_cond_diff(self, file_ex, file1, file2):
        if os.path.lexists(file_ex):
            self.show_diff(file1, file2)

    @staticmethod
    def _copy(src, dst):
        """Copy src to dst.

        :param src: Source file
        :type src: str
        :param dst: Destination file
        :type dst: str

        """
        if os.path.islink(src):
            linkto = os.readlink(src)
            try:
                os.symlink(linkto, dst)
            except FileExistsError:
                os.unlink(dst)
                os.symlink(linkto, dst)
        else:
            shutil.copy2(src, dst)

    def _remove(self, conf_file):
        """Remove file

        :param conf_file: File to be deleted
        :type conf_file: str

        """
        if self.debug:
            print("rm {}".format(conf_file))
        else:
            os.unlink(conf_file)

    def _overwrite(self, src, dst):
        if self.debug:
            print("cp --no-dereference {0} {1}".format(src, dst))
        else:
            self._copy(src, dst)
            self._remove(src)

    def _ls_conf_file(self, conf_file, other_file):
        print("Configuration file '{}'".format(conf_file))
        if self.selinux:
            print(subprocess.check_output(['/usr/bin/ls', '-ltrd', '--lcontext',
                                           conf_file, other_file],
                                          universal_newlines=True))
        else:
            print(subprocess.check_output(['/usr/bin/ls', '-ltrd',
                                           conf_file, other_file],
                                          universal_newlines=True))

    def _merge_conf_files(self, conf_file, other_file):
        # vimdiff, gvimdiff, meld return 0 even if file was not saved
        # we may handle it some way. check last modification? ask user?
        try:
            if self.frontend == "vimdiff" or \
                    self.frontend == "gvimdiff" or \
                    self.frontend == "meld":
                subprocess.check_call(
                    ["/usr/bin/{}".format(self.frontend),
                     conf_file, other_file])
            elif self.frontend == "diffuse":
                try:
                    subprocess.check_call(
                        ["/usr/bin/diffuse", conf_file, other_file])
                except subprocess.CalledProcessError:
                    print("Files not merged.")
            elif self.frontend == "kdiff3":
                try:
                    subprocess.check_call(
                        ["/usr/bin/kdiff3", conf_file, other_file,
                         "-o", conf_file])
                    self._remove(other_file)
                    self._remove("{}.orig".format(conf_file))
                except subprocess.CalledProcessError:
                    print("Files not merged.")
            elif (self.frontend == "env" or self.frontend is None) and \
                    os.environ.get('MERGE') is not None:
                merge_tool = os.environ.get('MERGE')
                print(repr(merge_tool))
                subprocess.check_call([merge_tool, conf_file, other_file])
            else:
                self.logger.error("You did not selected any frontend for merge.\n" +
                                  "      Define it with environment variable 'MERGE' or flag -f.")
                sys.exit(2)
        except FileNotFoundError as err:
            sys.stderr.write("{0}\n".format(err.strerror))
            sys.exit(4)

    def _handle_package(self, package):
        for conf_file in self.get_list_of_config(package):
            if self.diff:
                conf_rpmnew = "{0}.rpmnew".format(conf_file)
                conf_rpmsave = "{0}.rpmsave".format(conf_file)
                conf_rpmorig = "{0}.rpmorig".format(conf_file)
                self._show_cond_diff(conf_rpmnew, conf_file, conf_rpmnew)
                self._show_cond_diff(conf_rpmsave, conf_rpmsave, conf_file)
                self._show_cond_diff(conf_rpmorig, conf_rpmorig, conf_file)
            else:
                tmp = "{}.{}"
                if os.access(tmp.format(conf_file, "rpmnew"), os.F_OK):
                    self._handle_rpmnew(conf_file,
                                        tmp.format(conf_file, "rpmnew"))
                if os.access(tmp.format(conf_file, "rpmsave"), os.F_OK):
                    self._handle_rpmsave(conf_file,
                                         tmp.format(conf_file, "rpmsave"))
                if os.access(tmp.format(conf_file, "rpmorig"), os.F_OK):
                    self._handle_rpmsave(conf_file,
                                         tmp.format(conf_file, "rpmorig"))

    def _handle_rpmnew(self, conf_file, other_file):
        if not (self.is_broken_symlink(conf_file) or self.is_broken_symlink(other_file)) \
            and filecmp.cmp(conf_file, other_file):
            self._remove(other_file)
            return

        prompt = """ ==> Package distributor has shipped an updated version.
   What would you like to do about it ?  Your options are:
    Y or I  : install the package maintainer's version
    N or O  : keep your currently-installed version
      D     : show the differences between the versions
      M     : merge configuration files
      Z     : background this process to examine the situation
      S     : skip this file
 The default action is to keep your current version.
*** aliases (Y/I/N/O/D/M/Z/S) [default=N] ? """

        option = ""
        while (option not in ["Y", "I", "N", "O", "S"]):
            if not os.access(other_file, os.F_OK):
                print("File {} was removed by 3rd party. Skipping.".format(other_file))
                return
            self._ls_conf_file(conf_file, other_file)
            print(prompt)
            try:
                option = self.flush_input("Your choice: ").upper()
            except EOFError:
                option = "S"
            except KeyboardInterrupt:
                sys.exit(1)
            if not os.access(other_file, os.F_OK):
                print("File {} was removed by 3rd party. Skipping.".format(other_file))
                return
            if not option:
                option = "N"
            if option == "D":
                self.show_diff(conf_file, other_file)
            if option == "Z":
                print("Run command 'fg' to continue")
                os.kill(os.getpid(), signal.SIGSTOP)
            if option == "M":
                self._merge_conf_files(conf_file, other_file)
        if option in ["N", "O"]:
            self._remove(other_file)
        if option in ["Y", "I"]:
            self._overwrite(other_file, conf_file)

    def _handle_rpmsave(self, conf_file, other_file):
        if not (self.is_broken_symlink(conf_file) or self.is_broken_symlink(other_file)) \
            and filecmp.cmp(conf_file, other_file):
            self._remove(other_file)
            return

        prompt = """ ==> Package distributor has shipped an updated version.
 ==> Maintainer forced upgrade. Your old version has been backed up.
   What would you like to do about it?  Your options are:
    Y or I  : install (keep) the package maintainer's version
    N or O  : return back to your original file
      D     : show the differences between the versions
      M     : merge configuration files
      Z     : background this process to examine the situation
      S     : skip this file
 The default action is to keep package maintainer's version.
*** aliases (Y/I/N/O/M/D/Z/S) [default=Y] ? """

        option = ""
        while (option not in ["Y", "I", "N", "O", "S"]):
            if not os.access(other_file, os.F_OK):
                print("File {} was removed by 3rd party. Skipping.".format(other_file))
                return
            self._ls_conf_file(conf_file, other_file)
            print(prompt)
            try:
                option = self.flush_input("Your choice: ").upper()
            except EOFError:
                option = "S"
            except KeyboardInterrupt:
                sys.exit(1)
            if not os.access(other_file, os.F_OK):
                print("File {} was removed by 3rd party. Skipping.".format(other_file))
                return
            if not option:
                option = "Y"
            if option == "D":
                self.show_diff(other_file, conf_file)
            if option == "Z":
                print("Run command 'fg' to continue")
                os.kill(os.getpid(), signal.SIGSTOP)
            if option == "M":
                self._merge_conf_files(conf_file, other_file)
        if option in ["Y", "I"]:
            self._remove(other_file)
        if option in ["N", "O"]:
            self._overwrite(other_file, conf_file)

    @staticmethod
    def _clean_orphan_file(rpmnew_rpmsave):
        # rpmnew_rpmsave is lowercase name of rpmnew/rpmsave file
        (rpmnew_rpmsave_orig, _) = os.path.splitext(rpmnew_rpmsave)
        package_merge = file_delete = None
        trans = rpm.TransactionSet()
        # pylint: disable=no-member
        tmp_db = trans.dbMatch("basenames", rpmnew_rpmsave_orig)
        if tmp_db.count() == 0:
            file_delete = rpmnew_rpmsave
        else:
            package_merge = tmp_db.__next__().Name
        return ([package_merge, rpmnew_rpmsave_orig, rpmnew_rpmsave],
                file_delete)

    def _clean_orphan(self):
        files_merge = []
        files_delete = []
        for topdir in ["/etc", "/var", "/usr"]:
            self.logger.info("Seaching through: %s", topdir)
            for root, dirs, files in os.walk(topdir, followlinks=True):
                if root == "/var/lib":
                    # skip /var/lib/mock
                    dirs[:] = [d for d in dirs if d != "mock"]
                for name in files:
                    l_name = os.path.join(root, name)
                    if os.path.splitext(l_name)[1] in [".rpmnew", ".rpmsave"]:
                        (file_merge, file_delete) = self._clean_orphan_file(
                            l_name)
                        if file_merge[0]:
                            files_merge.append(file_merge)
                        if file_delete:
                            files_delete.append(file_delete)
        if files_merge:
            print(
                "These files need merging - you may want to run 'rpmconf -a':")
            for (package_merge, _, rpmnew_rpmsave) in files_merge:
                print("{0}: {1}".format(package_merge.ljust(20),
                                        rpmnew_rpmsave))
            print("Skipping files above.\n")
        if files_delete:
            print("Orphaned .rpmnew and .rpmsave files:")
            for file_delete in files_delete:
                print(file_delete)
            answer = None
            while answer not in ["Y", "N", ""]:
                answer = self.flush_input("Delete these files (Y/n): ").upper()
            if answer in ["Y", ""]:
                for file_delete in files_delete:
                    self._remove(file_delete)
        else:
            print("No orphaned .rpmnew and .rpmsave files found.")
