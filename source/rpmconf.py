#!/usr/bin/python3
# vim: noai:ts=4:sw=4:expandtab

# This software is licensed to you under the GNU General Public License,
# version 3 (GPLv3). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv3
# along with this software; if not, see
# http://www.gnu.org/licenses/gpl-3.0.txt.
#
# Red Hat trademarks are not licensed under GPLv3. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.

from termios import tcflush, TCIOFLUSH

import argparse
import difflib
import os
import pydoc
import re
import rpm
import shutil
import signal
import subprocess
import sys
import time

def flush_input(question):
    """ Flush stdin and then ask the question. """
    tcflush(sys.stdin, TCIOFLUSH)
    return input(question)

def copy(src, dst):
    """ Copy src to dst."""
    if os.path.islink(src):
        linkto = os.readlink(src)
        os.symlink(linkto, dst)
    else:
        shutil.copy2(src, dst)

def overwrite(args, src, dst):
    if args.debug:
        print("cp --no-dereference {0} {1}".format(src, dst))
    else:
        copy(src, dst)
        remove(args, src)

def get_list_of_config(package):
    """ return list of config files for give package """
    result = subprocess.check_output(["/usr/bin/rpm", '-qc', package['name']], universal_newlines=True)
    # if package contains no files rpm will print localized "(contains no files)"
    if re.match( r'^(.*)$', result):
        result = []
    else:
        result = result.rstrip().split('\n')
    return result

def differ(file_name1, file_name2):
    """ returns True if files differ """
    fromlines = open(file_name1, 'U').readlines()
    tolines = open(file_name2, 'U').readlines()
    return not(list(difflib.unified_diff(fromlines, tolines)) == [])

def show_diff(file1, file2):
    fromdate = time.ctime(os.stat(file1).st_mtime)
    todate = time.ctime(os.stat(file2).st_mtime)
    fromlines = open(file1, 'U').readlines()
    tolines = open(file2, 'U').readlines()
    diff = difflib.unified_diff(fromlines, tolines, file1, file2, fromdate, todate)
    pydoc.pager(diff)

def show_cond_diff(file_ex, file1, file2):
    if os.path.lexists(file_ex):
        show_diff(file1, file2)

def remove(args, conf_file):
    if args.debug:
        print("rm {}".format(conf_file))
    else:
        os.unlink(conf_file)

def merge_conf_files(args, conf_file, other_file):
    # vimdiff, gvimdiff, meld return 0 even if file was not saved
    # we may handle it some way. check last modification? ask user?
    try:
        if args.frontend == 'vimdiff':
            subprocess.check_call(['/usr/bin/vimdiff', conf_file, other_file])
            remove(args, other_file)
        elif args.frontend == 'gvimdiff':
            subprocess.check_call(['/usr/bin/gvimdiff', conf_file, other_file])
            remove(args, other_file)
        elif args.frontend == 'diffuse':
            try:
                subprocess.check_call(['/usr/bin/diffuse', conf_file, other_file])
                remove(args, other_file)
            except subprocess.CalledProcessError:
                print("Files not merged.")
        elif args.frontend == 'kdiff3':
            try:
                subprocess.check_call(['/usr/bin/kdiff3', conf_file, other_file, '-o', conf_file])
                remove(args, other_file)
                remove(args, conf_file+".orig")
            except subprocess.CalledProcessError:
                print("Files not merged.")
        elif args.frontend == 'meld':
            subprocess.check_call(['/usr/bin/meld', conf_file, other_file])
            remove(args, other_file)
        else:
            sys.stderr.write("Error: you did not selected any frontend for merge.\n")
            sys.exit(2)
    except FileNotFoundError:
        sys.stderr.write("Error: {0} not found.\n")
        sys.exit(4)

def ls_conf_file(args, conf_file, other_file):
    print("Configuration file '{}'".format(conf_file))
    if args.selinux:
        print(subprocess.check_output(['/usr/bin/ls', '-ltrd', '--lcontext', 
            conf_file, other_file],
            universal_newlines=True))
    else:
        print(subprocess.check_output(['/usr/bin/ls', '-ltrd',
            conf_file, other_file], universal_newlines=True))

def handle_rpmnew(args, conf_file, other_file):
    if not differ(conf_file, other_file):
        remove(args, other_file)
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
*** aliases (Y/I/N/O/D/Z/S) [default=N] ? """

    option = ""
    while (option not in ["Y", "I", "N", "O", "M", "S"]):
        ls_conf_file(args, conf_file, other_file)
        print(prompt)
        try:
            option = flush_input("Your choice: ").upper()
        except EOFError:
            option = "S"
        if not option:
            option = "N"

        if option == "D":
            show_diff(conf_file, other_file)
        if option == "Z":
            print("Run command 'fg' to continue")
            os.kill(os.getpid(), signal.SIGSTOP)
    if option in ["N", "O"]:
        remove(args, other_file)
    if option in ["Y", "I"]:
        overwrite(args, other_file, conf_file)
    if option == "M":
        merge_conf_files(args, conf_file, other_file)

def handle_rpmsave(args, conf_file, other_file):
    if not differ(conf_file, other_file):
        remove(args, other_file)
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
*** aliases (Y/I/N/O/D/Z/S) [default=Y] ? """

    option = ""
    while (option not in ["Y", "I", "N", "O", "M", "S"]):
        ls_conf_file(args, conf_file, other_file)
        print(prompt)
        try:
            option = flush_input("Your choice: ").upper()
        except EOFError:
            option = "S"
        if not option:
            option = "Y"

        if option == "D":
            show_diff(other_file, conf_file)
        if option == "Z":
            print("Run command 'fg' to continue")
            os.kill(os.getpid(), signal.SIGSTOP)
    if option in ["Y", "I"]:
        remove(args, other_file)
    if option in ["N", "O"]:
        overwrite(args, other_file, conf_file)
    if option == "M":
        merge_conf_files(args, conf_file, other_file)

def handle_package(args, package):
    """ does the main work for each package
        package is rpmHdr object
    """
    for conf_file in get_list_of_config(package):
        if args.diff:
            conf_rpmnew = "{0}.rpmnew".format(conf_file)
            conf_rpmsave = "{0}.rpmsave".format(conf_file)
            conf_rpmorig = "{0}.rpmorig".format(conf_file)
            show_cond_diff(conf_rpmnew, conf_file, conf_rpmnew)
            show_cond_diff(conf_rpmsave, conf_rpmsave, conf_file)
            show_cond_diff(conf_rpmorig, conf_rpmorig, conf_file)
        else:
            if os.access(conf_file + ".rpmnew", os.F_OK):
                handle_rpmnew(args, conf_file, conf_file + ".rpmnew")
            if os.access(conf_file + ".rpmsave", os.F_OK):
                handle_rpmsave(args, conf_file, conf_file + ".rpmsave")
            if os.access(conf_file + ".rpmorig", os.F_OK):
                handle_rpmsave(args, conf_file, conf_file + ".rpmorig")

def clean_orphan_file(rpmnew_rpmsave):
    # rpmnew_rpmsave is lowercase name of rpmnew/rpmsave file
    (rpmnew_rpmsave_orig, _) = os.path.splitext(rpmnew_rpmsave)
    package_merge = file_delete = None
    try:
        package_merge = subprocess.check_output(["/usr/bin/rpm", '-qf',
            rpmnew_rpmsave_orig, '--qf', '%{name}'],
            universal_newlines=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        file_delete = rpmnew_rpmsave
    return ([package_merge, rpmnew_rpmsave_orig, rpmnew_rpmsave], file_delete)

def clean_orphan(args):
    FILES_MERGE = []
    FILES_DELETE = []
    sys.stdout.write("Searching through: ")
    for topdir in ['/etc', '/var', '/usr']:
        sys.stdout.write(topdir + " ")
        sys.stdout.flush()
        for root, dirs, files in os.walk(topdir, followlinks=True):
            # TODO - skip /var/lib/mock/
            for name in files:
                l_name = os.path.join(root, name)
                if os.path.splitext(l_name)[1] in ['.rpmnew', '.rpmsave']:
                    (file_merge, file_delete) = clean_orphan_file(l_name)
                    if file_merge[0]:
                        FILES_MERGE.append(file_merge)
                    if file_delete:
                        FILES_DELETE.append(file_delete)
    sys.stdout.write("\n")
    if FILES_MERGE:
        print("These files need merging - you may want to run 'rpmconf -a':")
        for (package_merge, _, rpmnew_rpmsave) in FILES_MERGE:
            print("{0}: {1}".format(package_merge.ljust(20), rpmnew_rpmsave))
        print("Skipping files above.\n")
    if FILES_DELETE:
        print("Orphaned .rpmnew and .rpmsave files:")
        for file_delete in FILES_DELETE:
            print(file_delete)
        answer = None
        while answer not in ["Y", "N", ""]:
            answer = flush_input("Delete these files (Y/n): ").upper()
        if answer in ["Y", ""]:
            for file_delete in FILES_DELETE:
                remove(args, file_delete)
    else:
        print("No orphaned .rpmnew and .rpmsave files found.")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--all', dest='all', action='store_true',
        help='Check configuration files of all packages.')
    parser.add_argument('-c', '--clean', dest='clean', action='store_true',
        help='Find and delete orphaned .rpmnew and .rpmsave files.')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
        help='Dry run. Just show which file will be deleted.')
    parser.add_argument('-D', '--diff', dest='diff', action='store_true',
        help='Non-interactive diff mode. Useful to audit configs. Use with -a or -o options.')
    parser.add_argument('-f', '--frontend', dest='frontend', action='store', metavar='EDITOR',
        help='Define which frontend should be used for merging. For list of valid types see man page.')
    parser.add_argument('-o', '--owner', dest='owner', action='append', metavar='PACKAGE',
        help='Check only configuration files of given package.')
    parser.add_argument('-V', '--version', dest='version', action='store_true',
        help='Display rpmconf version.')
    parser.add_argument('-Z', dest='selinux', action='store_true',
        help='Display SELinux context of old and new file.')
    args = parser.parse_args()

    if args.version:
        print(subprocess.check_output(["/usr/bin/rpm", '-q', 'rpmconf']))
        sys.exit(0)
    if not (args.owner or args.all or args.clean):
        print(parser.print_usage())
        sys.exit(1)

    packages = []
    ts = rpm.TransactionSet()
    if args.all:
        packages = [ ts.dbMatch() ]
    elif args.owner:
        for o in args.owner:
            mi = ts.dbMatch('name', o)
            packages.append(mi)

    for mi in packages:
        for package_hdr in mi:
            handle_package(args, package_hdr)

    if args.clean:
        clean_orphan(args)


try:
    main()
except KeyboardInterrupt:
    sys.exit(2)
except PermissionError as e:
    print(e)
    print('You have to run this program as root.')
    sys.exit(3)
