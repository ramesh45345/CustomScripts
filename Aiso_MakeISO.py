#!/usr/bin/env python3
"""Create ISOs within VM."""

# Python includes.
import argparse
import os
import subprocess
import sys
# Custom includes
import PCreateChrootVM

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
vm_name = "ISOVM"
ssh_ip = "{0}.local".format(vm_name)
ssh_user = "root"

if __name__ == '__main__':
    print("Running {0}".format(__file__))
    if args.stage == 1:
        print("Running Stage 1, only for host.")
        # Start the VM if it is not started.
        PCreateChrootVM.vm_start(vm_name)
        PCreateChrootVM.ssh_wait(ip=ssh_ip, user=ssh_user)
        # Execute Stage 2
        subprocess.run("ssh {0} -l {1} /opt/CustomScripts/Aiso_MakeISO.py -s 2".format(ssh_ip, ssh_user), shell=True, check=True)

        # Retrieve ISO paths
        fedora_iso_path = subprocess.run("ssh {0} -l {1} find {2}/root/fedlive/ -maxdepth 1 -type f -name '*.iso'".format(ssh_ip, ssh_user, fedora_chroot_location), shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        arch_iso_path = subprocess.run("ssh {0} -l {1} find {2}/root/ -maxdepth 1 -type f -name '*.iso'".format(ssh_ip, ssh_user, arch_chroot_location), shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        ubuntu_iso_path = subprocess.run("ssh {0} -l {1} find {2}/root/ubulive/ -maxdepth 1 -type f -name '*.iso'".format(ssh_ip, ssh_user, ubuntu_chroot_location), shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        print("Found {0}, {1}, and {2} .".format(fedora_iso_path, arch_iso_path, ubuntu_iso_path))

        # Retrieve ISOs using scp
        subprocess.run("scp -C {0}@{1}:{2} {3}".format(ssh_user, ssh_ip, fedora_iso_path, args.outfolder), shell=True, check=False)
        subprocess.run("scp -C {0}@{1}:{2} {3}".format(ssh_user, ssh_ip, arch_iso_path, args.outfolder), shell=True, check=False)
        subprocess.run("scp -C {0}@{1}:{2} {3}".format(ssh_user, ssh_ip, ubuntu_iso_path, args.outfolder), shell=True, check=False)

        # Cleanup
        subprocess.run("ssh {0} -l {1} rm -rf {2}/root/fedlive/ {3} {4}/root/ubulive/".format(ssh_ip, ssh_user, fedora_chroot_location, arch_iso_path, ubuntu_chroot_location), shell=True, check=False)
        # Shutdown the VM.
        PCreateChrootVM.vm_shutdown(vm_name)
    if args.stage == 2:
        print("Running Stage 2, only for VM.")
        # Custom includes
        import zch
        # Update chroots
        subprocess.run("/opt/CustomScripts/Aiso_CreateVM.py -d {0}".format(sys.path[0]), shell=True, check=True)
        # Fedora ISO
        zch.ChrootCommand(fedora_chroot_location, "sh -c '/opt/CustomScripts/Afediso.py -n'")
        # Arch ISO
        zch.ChrootCommand(arch_chroot_location, "sh -c '/opt/CustomScripts/Aarchiso.py -n'")
        # Ubuntu ISO
        zch.ChrootCommand(ubuntu_chroot_location, "sh -c '/opt/CustomScripts/Aubuiso.py -n'")
