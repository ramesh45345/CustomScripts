#!/usr/bin/env python3
"""Create ISOs within VM."""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
# Custom includes
import CFunc

# Get arguments
parser = argparse.ArgumentParser(description='Provision VM for ISO building.')
parser.add_argument("-c", "--clean", help='Remove iso folders.', action="store_true")
parser.add_argument("-s", "--stage", help='Setup Stage (1: Host System, 2: VM, default: %(default)s)', type=int, default=1)
parser.add_argument("-w", "--chrootfolder", help='Location of chroot folder (default: %(default)s)', default=os.path.expanduser("~root"))
parser.add_argument("-p", "--outfolder", help='Location to store ISOs (default: %(default)s)', default=os.getcwd())
args = parser.parse_args()

# Global variables
workfolder = os.path.abspath(args.chrootfolder)
fedora_chroot_location = os.path.join(workfolder, "chroot_fedora")
arch_chroot_location = os.path.join(workfolder, "chroot_arch")
ubuntu_chroot_location = os.path.join(workfolder, "chroot_ubuntu")
ssh_ip = "ISOVM.local"
ssh_user = "root"

if __name__ == '__main__':
    print("Running {0}".format(__file__))
    if args.stage == 1:
        # Run Stage 2

        # Retrieve ISO paths
        print("ssh {0} -l {1} find {2}/root/fedlive/ -type f -name \*.iso".format(ssh_ip, ssh_user, fedora_chroot_location))
        fedora_iso_path = subprocess.run("ssh {0} -l {1} find {2}/root/fedlive/ -type f -name '*.iso'".format(ssh_ip, ssh_user, fedora_chroot_location), shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        arch_iso_path = subprocess.run("ssh {0} -l {1} find {2}/root/ -type f -name '*.iso'".format(ssh_ip, ssh_user, arch_chroot_location), shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        ubuntu_iso_path = subprocess.run("ssh {0} -l {1} find {2}/root/ubulive/ -type f -name '*.iso'".format(ssh_ip, ssh_user, ubuntu_chroot_location), shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        print(fedora_iso_path, arch_iso_path, ubuntu_iso_path)

        # Retrieve ISOs using scp
        # Cleanup

    if args.stage == 2:
        import zch
        # Update chroots
        subprocess.run("/opt/CustomScripts/Aiso_CreateVM.py -d {0}".format(sys.path[0]), shell=True, check=True)
        # Fedora ISO
        zch.ChrootCommand(fedora_chroot_location, "sh -c '/opt/CustomScripts/Afediso.py -n'")
        # Arch ISO
        zch.ChrootCommand(arch_chroot_location, "sh -c '/opt/CustomScripts/Aarchiso.py -n'")
        # Ubuntu ISO
        zch.ChrootCommand(ubuntu_chroot_location, "sh -c '/opt/CustomScripts/Aubuiso.py -n'")
