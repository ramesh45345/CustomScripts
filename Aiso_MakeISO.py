#!/usr/bin/env python3
"""Create ISOs within VM."""

# Python includes.
import argparse
import functools
import os
import subprocess
import sys
# Custom includes
import PCreateChrootVM

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Get arguments
parser = argparse.ArgumentParser(description='Provision VM for ISO building.')
parser.add_argument("-c", "--clean", help='Remove iso folders.', action="store_true")
parser.add_argument("-s", "--stage", help='Setup Stage (1: Host System, 2: VM, default: %(default)s)', type=int, default=1)
parser.add_argument("-w", "--chrootfolder", help='Location of chroot folder (default: %(default)s)', default=os.path.expanduser("~root"))
parser.add_argument("-p", "--outfolder", help='Location to store ISOs (default: %(default)s)', default=os.getcwd())
parser.add_argument("-t", "--distrotype", help='Specify ISO  (choices: %(choices)s) (default: %(default)s)', type=str, default="all", choices=["all", "fedora", "arch", "ubuntu"])
args = parser.parse_args()

# Global variables
workfolder = os.path.abspath(args.chrootfolder)
fedora_chroot_location = os.path.join(workfolder, "chroot_fedora")
arch_chroot_location = os.path.join(workfolder, "chroot_arch")
ubuntu_chroot_location = os.path.join(workfolder, "chroot_ubuntu")
vm_name = "ISOVM"
ssh_ip = f"{vm_name}.local"
ssh_user = "root"

if __name__ == '__main__':
    print(f"Running {__file__}")
    if args.stage == 1:
        print("Running Stage 1, only for host.")
        # Start the VM if it is not started.
        PCreateChrootVM.vm_start(vm_name)
        PCreateChrootVM.ssh_wait(ip=ssh_ip, user=ssh_user)
        # Sync CustomScripts on host to VM.
        subprocess.run(f"rsync -axHAX --info=progress2 {sys.path[0]}/ {ssh_user}@{ssh_ip}:/opt/CustomScripts/", shell=True, check=True)
        # Execute Stage 2
        stagetwocmd = f"ssh {ssh_ip} -l {ssh_user} /opt/CustomScripts/Aiso_MakeISO.py -s 2 -t {args.distrotype}"
        if args.clean:
            stagetwocmd += " -c"
        subprocess.run(stagetwocmd, shell=True, check=True)

        # Retrieve ISO paths
        fedora_iso_path = subprocess.run(f"ssh {ssh_ip} -l {ssh_user} find {fedora_chroot_location}/root/fedlive/ -maxdepth 1 -type f -name '*.iso'", shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        arch_iso_path = subprocess.run(f"ssh {ssh_ip} -l {ssh_user} find {arch_chroot_location}/root/ -maxdepth 1 -type f -name '*.iso'", shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        ubuntu_iso_path = subprocess.run(f"ssh {ssh_ip} -l {ssh_user} find {ubuntu_chroot_location}/root/ubulive/ -maxdepth 1 -type f -name '*.iso'", shell=True, check=False, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
        print(f"Found {fedora_iso_path}, {arch_iso_path}, and {ubuntu_iso_path} .")

        # Retrieve ISOs using scp
        if fedora_iso_path:
            subprocess.run(f"scp -C {ssh_user}@{ssh_ip}:{fedora_iso_path} {args.outfolder}", shell=True, check=True)
            # Cleanup
            subprocess.run(f"ssh {ssh_ip} -l {ssh_user} rm -rf {fedora_chroot_location}/root/fedlive/", shell=True, check=False)
        if arch_iso_path:
            subprocess.run(f"scp -C {ssh_user}@{ssh_ip}:{arch_iso_path} {args.outfolder}", shell=True, check=True)
            # Cleanup
            subprocess.run(f"ssh {ssh_ip} -l {ssh_user} rm -rf {arch_iso_path}", shell=True, check=False)
            subprocess.run(f"ssh {ssh_ip} -l {ssh_user} rm -rf /var/tmp/archiso_wf", shell=True, check=False)
        if ubuntu_iso_path:
            subprocess.run(f"scp -C {ssh_user}@{ssh_ip}:{ubuntu_iso_path} {args.outfolder}", shell=True, check=True)
            # Cleanup
            subprocess.run(f"ssh {ssh_ip} -l {ssh_user} rm -rf {ubuntu_chroot_location}/root/ubulive/", shell=True, check=False)

        # Shutdown the VM.
        PCreateChrootVM.vm_shutdown(vm_name)
    if args.stage == 2:
        print("Running Stage 2, only for VM.")
        # Custom includes
        import zch
        # Update chroots
        chroot_update_cmd = f"/opt/CustomScripts/Aiso_CreateVM.py -d {sys.path[0]}"
        if args.clean:
            chroot_update_cmd += " -c"
        subprocess.run(chroot_update_cmd, shell=True, check=True)
        if args.distrotype == "all" or args.distrotype == "fedora":
            # Fedora ISO
            zch.ChrootCommand(fedora_chroot_location, "sh -c '/opt/CustomScripts/Afediso.py -n'")
        if args.distrotype == "all" or args.distrotype == "arch":
            # Arch ISO
            zch.ChrootCommand(arch_chroot_location, "sh -c '/opt/CustomScripts/Aarchiso.py -n'")
        if args.distrotype == "all" or args.distrotype == "ubuntu":
            # Ubuntu ISO
            zch.ChrootCommand(ubuntu_chroot_location, "sh -c '/opt/CustomScripts/Aubuiso.py -n'")
