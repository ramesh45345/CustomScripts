#!/usr/bin/env python3
"""Provision script for ISO VM. Intended to be run inside VM."""

# Python includes.
import argparse
import os
import shutil
import subprocess
# Custom includes
import CFunc
import zch

# Global variables
chroot_locations = os.path.join(os.sep, "root")
fedora_chroot_location = os.path.join(chroot_locations, "chroot_fedora")
arch_chroot_location = os.path.join(chroot_locations, "chroot_arch")
ubuntu_chroot_location = os.path.join(chroot_locations, "chroot_ubuntu")

# Get arguments
parser = argparse.ArgumentParser(description='Provision VM for ISO building.')
parser.add_argument("-c", "--clean", help='Remove chroot folders.', action="store_true")
parser.add_argument("-w", "--workfolder", help='Location of chroot folder.')
args = parser.parse_args()

# Host packges
CFunc.dnfinstall("pacman arch-install-scripts systemd-container debootstrap")

# Fedora Chroot
# Create chroot if it doesn't exist
if not os.path.isdir(fedora_chroot_location) and shutil.which("dnf"):
    os.makedirs(fedora_chroot_location)
    subprocess.run('dnf -y --installroot={0} --releasever $(rpm -q --qf "%{{version}}" -f /etc/fedora-release) install @minimal-environment'.format(fedora_chroot_location), shell=True, check=True)
    subprocess.run("systemd-nspawn -D {0} sh -c 'dnf install -y nano livecd-tools spin-kickstarts pykickstart anaconda util-linux'".format(fedora_chroot_location), shell=True, check=True)
if os.path.isdir(fedora_chroot_location):
    # Update packages
    subprocess.run("systemd-nspawn -D {0} sh -c 'dnf upgrade -y'".format(fedora_chroot_location), shell=True, check=True)
    # Rsync Host CustomScripts
    subprocess.run("rsync -axHAX --info=progress2 /opt/CustomScripts/ {0}/opt/CustomScripts/".format(fedora_chroot_location), shell=True, check=True)


# Arch Chroot
# Create chroot if it doesn't exist
if not os.path.isdir(arch_chroot_location) and shutil.which("pacstrap"):
    subprocess.run("pacman-key --init; pacman-key --populate archlinux", shell=True, check=True)
    os.makedirs(arch_chroot_location)
    subprocess.run('pacstrap {0} base python archiso'.format(arch_chroot_location), shell=True, check=True)
if os.path.isdir(arch_chroot_location):
    # Update packages
    subprocess.run("systemd-nspawn -D {0} sh -c 'pacman -Syu --needed --noconfirm'".format(arch_chroot_location), shell=True, check=True)
    # Rsync Host CustomScripts
    subprocess.run("rsync -axHAX --info=progress2 /opt/CustomScripts/ {0}/opt/CustomScripts/".format(arch_chroot_location), shell=True, check=True)


# Ubuntu Chroot
# Create chroot if it doesn't exist
if not os.path.isdir(ubuntu_chroot_location) and shutil.which("debootstrap"):
    os.makedirs(ubuntu_chroot_location)
    subprocess.run("debootstrap hirsute {0} http://archive.ubuntu.com/ubuntu/".format(ubuntu_chroot_location), shell=True, check=True)
    subprocess.run("systemd-nspawn -D {0} sh -c 'apt install -y debootstrap binutils squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools dosfstools unzip'".format(arch_chroot_location), shell=True, check=True)
if os.path.isdir(ubuntu_chroot_location):
    # Update packages
    subprocess.run("systemd-nspawn -D {0} sh -c 'apt update; apt upgrade -y; apt dist-upgrade -y'".format(arch_chroot_location), shell=True, check=True)
    # Rsync Host CustomScripts
    subprocess.run("rsync -axHAX --info=progress2 /opt/CustomScripts/ {0}/opt/CustomScripts/".format(arch_chroot_location), shell=True, check=True)
