#!/usr/bin/env python3
"""Enter chroot"""

# Python includes.
import argparse
import os
import shutil
import subprocess
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

### Functions ###
def ChrootMountPaths(RootPath: str):
    """Mount all binds for chroot"""
    subprocess.run("mount --rbind /dev {0}/dev".format(RootPath), shell=True, check=True)
    subprocess.run("mount --make-rslave {0}/dev".format(RootPath), shell=True, check=True)
    subprocess.run("mount -t proc /proc {0}/proc".format(RootPath), shell=True, check=True)
    subprocess.run("mount --rbind /sys {0}/sys".format(RootPath), shell=True, check=True)
    subprocess.run("mount --make-rslave {0}/sys".format(RootPath), shell=True, check=True)
    subprocess.run("mount --rbind /tmp {0}/tmp".format(RootPath), shell=True, check=True)
    if os.path.islink(os.path.join(RootPath, "etc", "resolv.conf")):
        os.unlink(os.path.join(RootPath, "etc", "resolv.conf"))
    shutil.copy(os.path.join(os.sep, "etc", "resolv.conf"), os.path.join(RootPath, "etc", "resolv.conf"))
def ChrootUnmountPaths(RootPath: str):
    """Unmount all binds for chroot"""
    subprocess.run("umount -l {0}/dev".format(RootPath), shell=True, check=False, stdout=subprocess.DEVNULL)
    subprocess.run("umount -l {0}/proc".format(RootPath), shell=True, check=False, stdout=subprocess.DEVNULL)
    subprocess.run("umount -l {0}/sys".format(RootPath), shell=True, check=False, stdout=subprocess.DEVNULL)
    subprocess.run("umount -l {0}/tmp".format(RootPath), shell=True, check=False, stdout=subprocess.DEVNULL)
def ChrootRunCommand(RootPath: str, command: str, run_quoted_with_bash: bool = False):
    """Run a command without performing a mount or unmount. If the run_quoted_with_bash is set to True, assumes that /bin/bash exists, and the command is run with that interpreter."""
    if run_quoted_with_bash is True:
        subprocess.run("chroot {0} /bin/bash -c '{1}'".format(RootPath, command), shell=True, check=False)
    else:
        subprocess.run("PATH=$PATH:/sbin:/bin:/usr/sbin:/usr/local/bin chroot {0} {1}".format(RootPath, command), shell=True, check=False)
def ChrootRunCommandArray(RootPath: str, command: list, interpreter: str = None, error_on_fail: bool = True):
    """Run a command without performing a mount or unmount. Expects a command list."""
    if interpreter:
        subprocess.run(["chroot", RootPath, interpreter, "-c"] + command, shell=False, check=error_on_fail)
    else:
        subprocess.run(["chroot", RootPath] + command, shell=False, check=error_on_fail)
def ChrootCommand(RootPath: str, command: str):
    """Run a command in the chroot, mounting before and unmounting after."""
    try:
        ChrootMountPaths(RootPath)
        ChrootRunCommand(RootPath, command)
    finally:
        ChrootUnmountPaths(RootPath)


# Exit if not root.
CFunc.is_root(True)

if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Enter a chroot.')
    parser.add_argument("chrootpath", help='Path to enter the chroot')
    parser.add_argument("-c", "--chrootcommand", default="/bin/bash", help='Command to run in the chroot')
    args = parser.parse_args()

    # Get absolute path of the given path.
    abschrootpath = os.path.realpath(args.chrootpath)
    ChrootCommand(abschrootpath, args.chrootcommand)
