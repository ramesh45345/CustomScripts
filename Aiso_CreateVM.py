#!/usr/bin/env python3
"""Provision script for ISO VM. Intended to be run inside VM."""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
# Custom includes
import CFunc
import zch

# Get arguments
parser = argparse.ArgumentParser(description='Provision VM for ISO building.')
parser.add_argument("-c", "--clean", help='Remove chroot folders.', action="store_true")
parser.add_argument("-w", "--workfolder", help='Location of chroot folder (default: %(default)s)', default=os.path.expanduser("~root"))
parser.add_argument("-d", "--cslocation", help='Location of scripts folder (default: %(default)s)', default=sys.path[0])
args = parser.parse_args()

# Global variables
workfolder = os.path.abspath(args.workfolder)
fedora_chroot_location = os.path.join(workfolder, "chroot_fedora")
arch_chroot_location = os.path.join(workfolder, "chroot_arch")
ubuntu_chroot_location = os.path.join(workfolder, "chroot_ubuntu")
cslocation = os.path.join(os.path.abspath(args.cslocation), '')
ubuntu_version = "jammy"
fedora_version = "35"

# Check variables
if not os.path.isdir(cslocation):
    print("ERROR: {0} does not exist. Exiting.".format(args.cslocation))
    sys.exit()
if not os.path.isdir(args.workfolder):
    print("ERROR: {0} does not exist. Exiting.".format(args.workfolder))
    sys.exit()
print("Chroot root folder: {0}".format(workfolder))
print("CS Location: {0}".format(cslocation))


### Functions ###
def ctr_create(ctrimage: str, path: str, cmd: str):
    """Run a chroot create command using a container runtime."""
    full_cmd = ["podman", "run", "--rm", "--privileged", "--pull=always", "-it", "--volume={0}:/chrootfld".format(path), "--name=chrootsetup", ctrimage, "bash", "-c", cmd]
    print("Running {0}".format(full_cmd))
    subprocess.run(full_cmd, check=True)
def create_chroot_arch(path: str, packages: str = "base"):
    """Create an arch chroot."""
    print("Creating arch at {0}".format(path))
    os.makedirs(path, exist_ok=False)
    ctr_create("docker.io/library/archlinux:latest", path, "sed -i 's/^#ParallelDownloads/ParallelDownloads/g' /etc/pacman.conf && pacman -Sy --noconfirm --needed arch-install-scripts && pacstrap -c /chrootfld {0}".format(packages))
def create_chroot_fedora(path: str, packages: str = "systemd passwd dnf fedora-release vim-minimal"):
    """Create a fedora chroot."""
    print("Creating fedora at {0}".format(path))
    os.makedirs(path, exist_ok=False)
    ctr_create("registry.fedoraproject.org/fedora", path, "dnf -y --releasever={0} --installroot=/chrootfld --disablerepo='*' --enablerepo=fedora --enablerepo=updates install {1}".format(fedora_version, packages))
def create_chroot_ubuntu(path: str, packages: str = "systemd-container"):
    """Create an ubuntu chroot."""
    print("Creating ubuntu at {0}".format(path))
    os.makedirs(path, exist_ok=False)
    ctr_create("docker.io/library/ubuntu:rolling", path, "apt-get update && apt-get install -y debootstrap && debootstrap --include={1} --components=main,universe,restricted,multiverse --arch amd64 {0} /chrootfld".format(ubuntu_version, packages))


### Begin Code ###
# Host packges
CFunc.dnfinstall("podman pacman arch-install-scripts systemd-container debootstrap zstd")

# Clean
if args.clean is True:
    if os.path.isdir(fedora_chroot_location):
        shutil.rmtree(fedora_chroot_location)
    if os.path.isdir(arch_chroot_location):
        shutil.rmtree(arch_chroot_location)
    if os.path.isdir(ubuntu_chroot_location):
        shutil.rmtree(ubuntu_chroot_location)

# Fedora Chroot
# Create chroot if it doesn't exist
if not os.path.isdir(fedora_chroot_location) and shutil.which("dnf"):
    os.makedirs(fedora_chroot_location)
    subprocess.run('dnf -y --installroot={0} --releasever $(rpm -q --qf "%{{version}}" -f /etc/fedora-release) install @minimal-environment'.format(fedora_chroot_location), shell=True, check=True)
    zch.ChrootCommand(fedora_chroot_location, "sh -c 'dnf install -y nano livecd-tools spin-kickstarts pykickstart anaconda util-linux'")
if os.path.isdir(fedora_chroot_location):
    # Update packages
    zch.ChrootCommand(fedora_chroot_location, "sh -c 'dnf upgrade -y'")
    # Rsync Host CustomScripts
    subprocess.run("rsync -axHAX --info=progress2 {0} {1}/opt/CustomScripts/".format(cslocation, fedora_chroot_location), shell=True, check=True)


# Arch Chroot
# Create chroot if it doesn't exist
if not os.path.isdir(arch_chroot_location):
    create_chroot_arch(arch_chroot_location, "base python archiso")
if os.path.isdir(arch_chroot_location):
    # Update packages
    zch.ChrootCommand(arch_chroot_location, "sh -c 'pacman -Syu --needed --noconfirm'")
    # Rsync Host CustomScripts
    subprocess.run("rsync -axHAX --info=progress2 {0} {1}/opt/CustomScripts/".format(cslocation, arch_chroot_location), shell=True, check=True)


# Ubuntu Chroot
# Create chroot if it doesn't exist
if not os.path.isdir(ubuntu_chroot_location) and shutil.which("debootstrap"):
    os.makedirs(ubuntu_chroot_location)
    subprocess.run("debootstrap {0} {1} http://archive.ubuntu.com/ubuntu/".format(ubuntu_version, ubuntu_chroot_location), shell=True, check=True)
    zch.ChrootCommand(ubuntu_chroot_location, "sh -c 'apt install -y debootstrap binutils squashfs-tools grub-pc-bin grub-efi-amd64-bin mtools dosfstools unzip'")
    zch.ChrootCommand(ubuntu_chroot_location, "sh -c 'apt-get install -y --no-install-recommends software-properties-common'")
    zch.ChrootCommand(ubuntu_chroot_location, "sh -c 'add-apt-repository -y main && add-apt-repository -y restricted && add-apt-repository -y universe && add-apt-repository -y multiverse'")
if os.path.isdir(ubuntu_chroot_location):
    # Update packages
    zch.ChrootCommand(ubuntu_chroot_location, "sh -c 'apt update; apt upgrade -y; apt dist-upgrade -y'")
    # Rsync Host CustomScripts
    subprocess.run("rsync -axHAX --info=progress2 {0} {1}/opt/CustomScripts/".format(cslocation, ubuntu_chroot_location), shell=True, check=True)
