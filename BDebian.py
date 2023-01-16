#!/usr/bin/env python3
"""Install Debian in a Chroot"""

# If used in docker, first spin up container:
#   docker run -it --privileged --name bdeb -v /:/files ubuntu:rolling
#   apt update; apt install python3 debootstrap qemu-user-static
# Remount the partition in question with suid and dev in the docker container: mount -o remount,defaults,suid,dev <partition>

# Python includes.
import argparse
import os
import sys
import subprocess
import shutil
import stat
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = sys.path[0]

# Get arguments
parser = argparse.ArgumentParser(description='Install Debian/Ubuntu into a folder/chroot.')
parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
parser.add_argument("-c", "--hostname", help='Hostname', default="DebianTest")
parser.add_argument("-u", "--username", help='Username', default="user")
parser.add_argument("-f", "--fullname", help='Full Name', default="User Name")
parser.add_argument("-q", "--password", help='Password', default="asdf")
parser.add_argument("-g", "--grubtype", type=int, help='Grub Install Number', default=1)
parser.add_argument("-i", "--grubpartition", help='Grub Custom Parition (if autodetection isnt working, i.e. /dev/sdb)', default=None)
parser.add_argument("-t", "--type", help='OS Type (debian, ubuntu, etc)', default="debian")
parser.add_argument("-r", "--release", help='Release Distribution', default="unstable")
parser.add_argument("-a", "--architecture", help='Architecture (amd64, i386, armhf, arm64, etc)', default="amd64")
parser.add_argument("-z", "--zch", help='Use zch instead of systemd-nspawn', action="store_true")
parser.add_argument("installpath", help='Path of Installation')

# Save arguments.
args = parser.parse_args()
print("Hostname:", args.hostname)
print("Username:", args.username)
print("Full Name:", args.fullname)
print("Grub Install Number:", args.grubtype)
# Get absolute path of the given path.
absinstallpath = os.path.realpath(args.installpath)
print("Path of Installation:", absinstallpath)
print("OS Type:", args.type)
print("Release Distribution:", args.release)
DEVPART = subprocess.run('sh -c df -m | grep " \+{0}$" | grep -Eo "/dev/[a-z]d[a-z]"'.format(absinstallpath), shell=True, stdout=subprocess.PIPE, universal_newlines=True)
grubautopart = format(DEVPART.stdout.strip())
print("Autodetect grub partition:", grubautopart)
if args.grubpartition is not None and stat.S_ISBLK(os.stat(args.grubpartition).st_mode) is True:
    grubpart = args.grubpartition
else:
    grubpart = grubautopart
print("Grub partition to be used:", grubpart)
print("Architecture to install:", args.architecture)
if args.type == "ubuntu" and "arm" in args.architecture:
    osurl = "http://ports.ubuntu.com/ubuntu-ports/"
elif args.type == "ubuntu":
    osurl = "http://archive.ubuntu.com/ubuntu/"
else:
    osurl = "http://ftp.us.debian.org/debian/"
print("URL to use:", osurl)

# Exit if not root.
CFunc.is_root(True)

# Ensure that certain commands exist.
cmdcheck = ["debootstrap"]
for cmd in cmdcheck:
    if not shutil.which(cmd):
        sys.exit("\nError, ensure command {0} is installed.".format(cmd))
if args.zch is False:
    cmd = "systemd-nspawn"
    if not shutil.which(cmd):
        sys.exit("\nError, ensure command {0} is installed.".format(cmd))

if args.noprompt is False:
    input("Press Enter to continue.")

# Bootstrap the chroot environment.
BOOTSTRAPSCRIPT = ""
if "arm" in args.architecture:
    if args.architecture == "armhf":
        qemu_cmd = "qemu-arm-static"
    if args.architecture == "arm64":
        qemu_cmd = "qemu-aarch64-static"
    # Ensure that certain commands exist.
    cmdcheck = ["update-binfmts", qemu_cmd]
    for cmd in cmdcheck:
        if not shutil.which(cmd):
            sys.exit("\nError, ensure command {0} is installed.".format(cmd))
    # ARM specific init here.
    BOOTSTRAPSCRIPT += """
debootstrap --foreign --no-check-gpg --include=ca-certificates --arch {DEBARCH} {DISTROCHOICE} {INSTALLPATH} {URL}
cp -av /usr/bin/{qemu_cmd} {INSTALLPATH}/usr/bin
update-binfmts --enable
chroot {INSTALLPATH}/ /debootstrap/debootstrap --second-stage --verbose
""".format(DEBARCH=args.architecture, DISTROCHOICE=args.release, INSTALLPATH=absinstallpath, URL=osurl, qemu_cmd=qemu_cmd)
else:
    BOOTSTRAPSCRIPT += """
debootstrap --no-check-gpg --arch {DEBARCH} {DISTROCHOICE} {INSTALLPATH} {URL}
""".format(DEBARCH=args.architecture, DISTROCHOICE=args.release, INSTALLPATH=absinstallpath, URL=osurl)
subprocess.run(BOOTSTRAPSCRIPT, shell=True)

# Create and run setup script.
SETUPSCRIPT = """#!/bin/bash
echo "Running Debian Setup Script"

# Exporting Path for chroot
export PATH=$PATH:/bin:/usr/local/sbin:/usr/sbin:/sbin

# Set hostname
echo "{HOSTNAME}" > /etc/hostname
sed -i 's/\(127.0.0.1\\tlocalhost\)\(.*\)/\\1 {HOSTNAME}/g' "/etc/hosts"

# Update repos
apt update

# Set timezone
echo "America/New_York" > "/etc/timezone"
[ -f /etc/localtime ] && rm -f /etc/localtime
ln -s /usr/share/zoneinfo/America/New_York /etc/localtime
apt install -y tzdata
dpkg-reconfigure -f noninteractive tzdata

# Install locales
apt install -y locales
sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
echo 'LANG="en_US.UTF-8"'>/etc/default/locale
locale-gen --purge en_US en_US.UTF-8
dpkg-reconfigure --frontend=noninteractive locales
update-locale
# Locale fix for gnome-terminal.
localectl set-locale LANG="en_US.UTF-8"
echo "LANG=en_US.UTF-8" > /etc/locale.conf
# Set keymap for Ubuntu
echo "console-setup	console-setup/charmap47	select	UTF-8" | debconf-set-selections

# Install lsb_release
DEBIAN_FRONTEND=noninteractive apt install -y lsb-release nano sudo less apt-transport-https psmisc

# Store distro being used.
DISTRO=$(lsb_release -si)
DEBRELEASE=$(lsb_release -sc)

DEBIAN_FRONTEND=noninteractive apt install -y software-properties-common

# Unlocking root account
apt install -y passwd
passwd -u root
chpasswd <<<"root:{PASSWORD}"
# Setup normal user
if ! grep -i {USERNAME} /etc/passwd; then
    adduser --disabled-password --gecos "" {USERNAME}
    chfn -f "{FULLNAME}" {USERNAME}
fi
chpasswd <<<"{USERNAME}:{PASSWORD}"

# Add user to all reasonable groups
# Get all groups
LISTOFGROUPS="$(cut -d: -f1 /etc/group)"
# Remove some groups
CUTGROUPS=$(sed -e "/^users/d; /^root/d; /^nobody/d; /^nogroup/d" <<< $LISTOFGROUPS)
echo Groups to Add: $CUTGROUPS
for grp in $CUTGROUPS; do
    usermod -aG $grp {USERNAME}
done

# Network software
apt install -y ssh
# Allow root login
sed -i '/^#PermitRootLogin.*/s/^#//g' /etc/ssh/sshd_config
sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config

# Network manager
apt-get install -y network-manager
sed -i 's/managed=.*/managed=true/g' /etc/NetworkManager/NetworkManager.conf
# https://askubuntu.com/questions/882806/ethernet-device-not-managed
if [ -f /etc/NetworkManager/conf.d/10-globally-managed-devices.conf ]; then
    rm /etc/NetworkManager/conf.d/10-globally-managed-devices.conf
fi
touch /etc/NetworkManager/conf.d/10-globally-managed-devices.conf
# Ensure DNS resolution is installed and working
apt-get install -y openresolv
# Create resolv.conf file if it doesn't exist (and its path)
if [ ! -f /run/resolvconf/resolv.conf ]; then
    mkdir -p /run/resolvconf
    touch /run/resolvconf/resolv.conf
    echo "nameserver 1.1.1.1" > /run/resolvconf/resolv.conf
fi
# https://askubuntu.com/questions/137037/networkmanager-not-populating-resolv-conf
# https://www.linuxquestions.org/questions/ubuntu-63/18-04-how-to-force-usage-of-dns-server-assigned-by-dhcp-4175628934/
# ln -sf ../run/systemd/resolve/resolv.conf /etc/resolv.conf
# DEBIAN_FRONTEND=noninteractive dpkg-reconfigure openresolv

""".format(HOSTNAME=args.hostname, USERNAME=args.username, PASSWORD=args.password, FULLNAME=args.fullname)

# Set up repositories for debian/ubuntu.
if args.type == "ubuntu":
    SETUPSCRIPT += """
# Restricted, universe, and multiverse for Ubuntu.
add-apt-repository restricted
add-apt-repository universe
add-apt-repository multiverse
if ! grep -i "{DEBRELEASE}-updates main" /etc/apt/sources.list; then
    add-apt-repository "deb {URL} {DEBRELEASE}-updates main restricted universe multiverse"
fi
if ! grep -i "{DEBRELEASE}-security main" /etc/apt/sources.list; then
    add-apt-repository "deb {URL} {DEBRELEASE}-security main restricted universe multiverse"
fi
if ! grep -i "{DEBRELEASE}-backports main" /etc/apt/sources.list; then
    add-apt-repository "deb {URL} {DEBRELEASE}-backports main restricted universe multiverse"
fi
# Install firmware for armhf architecture.
if [[ "{DEBARCH}" = "armhf" || "{DEBARCH}" = "arm64" ]]; then
    apt install -y linux-firmware
fi
""".format(DEBRELEASE=args.release, URL=osurl, DEBARCH=args.architecture)
else:
    SETUPSCRIPT += """
# Contrib and non-free for normal distro
add-apt-repository main
add-apt-repository contrib
add-apt-repository non-free
if [[ "{DEBRELEASE}" != "sid" && "{DEBRELEASE}" != "unstable" && "{DEBRELEASE}" != "testing" ]] && ! grep -i "{DEBRELEASE}-updates main" /etc/apt/sources.list; then
    add-apt-repository "deb http://ftp.us.debian.org/debian {DEBRELEASE}-updates main contrib non-free"
fi
# Comment out lines containing httpredir.
sed -i '/httpredir/ s/^#*/#/' /etc/apt/sources.list
# Install firmware for armhf architecture.
if [[ "{DEBARCH}" = "armhf" || "{DEBARCH}" = "arm64" ]]; then
    apt install -y firmware-linux
fi
""".format(DEBRELEASE=args.release, DEBARCH=args.architecture)

SETUPSCRIPT += """
# Enable 32-bit support for 64-bit arch.
if [[ "{DEBARCH}" = "amd64" ]]; then
    dpkg --add-architecture i386
fi
apt update
apt dist-upgrade -y

# Install software
DEBIAN_FRONTEND=noninteractive apt install -y tasksel xorg
apt install -f
# Install fs tools.
DEBIAN_FRONTEND=noninteractive apt install -y btrfs-tools f2fs-tools nbd-client
# Fix for nbd-client: https://bugs.launchpad.net/ubuntu/+source/nbd/+bug/1487679
systemctl disable NetworkManager-wait-online

# Delete defaults in sudoers for Debian.
if grep -iq $'^Defaults\tenv_reset' /etc/sudoers; then
    sed -i $'/^Defaults\tenv_reset/ s/^#*/#/' /etc/sudoers
    sed -i $'/^Defaults\tmail_badpass/ s/^#*/#/' /etc/sudoers
    sed -i $'/^Defaults\tsecure_path/ s/^#*/#/' /etc/sudoers
fi
visudo -c

# Fetch scripts
apt install -y git
git clone "https://github.com/ramesh45345/CustomScripts.git" "/opt/CustomScripts"
chmod a+rwx "/opt/CustomScripts"

""".format(DEBARCH=args.architecture)

# Init grub script
GRUBSCRIPT = """#!/bin/bash

# Debian Grub Script

# Exporting Path for chroot
export PATH=$PATH:/bin:/usr/local/sbin:/usr/sbin:/sbin
"""
# Install kernel, grub.
if 2 <= args.grubtype <= 3:

    if args.type == "ubuntu":
        GRUBSCRIPT += """
DEBIAN_FRONTEND=noninteractive apt install -y linux-image-generic linux-headers-generic
DEBIAN_FRONTEND=noninteractive apt install -y gfxboot gfxboot-theme-ubuntu linux-firmware
"""
    else:
        GRUBSCRIPT += """
if [[ "{DEBARCH}" = "amd64" ]]; then
    DEBIAN_FRONTEND=noninteractive apt install -y linux-image-amd64
fi
if [[ "{DEBARCH}" = "i386" || "{DEBARCH}" = "i686" ]]; then
    DEBIAN_FRONTEND=noninteractive apt install -y linux-image-686-pae
fi

apt install -y firmware-linux gfxboot
echo "firmware-ipw2x00 firmware-ipw2x00/license/accepted boolean true" | debconf-set-selections
echo "firmware-ivtv firmware-ivtv/license/accepted boolean true" | debconf-set-selections
DEBIAN_FRONTEND=noninteractive apt install -y ^firmware-*
""".format(DEBARCH=args.architecture)

# Grub install selection statement.
if args.grubtype == 1:
    print("Not installing grub.")
else:
    # Create fstab for other grub scenarios
    subprocess.run("genfstab -U {INSTALLPATH} > {INSTALLPATH}/etc/fstab".format(INSTALLPATH=absinstallpath), shell=True)
    subprocess.run("sed -i '/zram0/d' {INSTALLPATH}/etc/fstab".format(INSTALLPATH=absinstallpath), shell=True)
# Use autodetected or specified grub partition.
if args.grubtype == 2:
    # Add if partition is a block device
    if stat.S_ISBLK(os.stat(grubpart).st_mode) is True:
        GRUBSCRIPT += """
DEBIAN_FRONTEND=noninteractive apt install -y grub-pc
update-grub2
grub-install --target=i386-pc --recheck --debug {0}
""".format(grubpart)
    else:
        print("ERROR Grub Mode 2, partition {0} is not a block device.".format(grubpart))
# Use efi partitioning
elif args.grubtype == 3:
    # Add if /boot/efi is mounted, and partition is a block device.
    if os.path.ismount("{0}/boot/efi".format(absinstallpath)) is True and stat.S_ISBLK(os.stat(grubpart).st_mode) is True:
        GRUBSCRIPT += """
DEBIAN_FRONTEND=noninteractive apt install -y grub-efi-amd64
update-grub2
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id={0} --recheck --debug
""".format(args.type)
    else:
        print("ERROR Grub Mode 3, {0}/boot/efi isn't a mount point or {1} is not a block device.".format(absinstallpath, grubpart))

# Close the setup script.
SETUPSCRIPT_PATH = os.path.join(absinstallpath, "setupscript.sh")
SETUPSCRIPT_VAR = open(SETUPSCRIPT_PATH, mode='w')
SETUPSCRIPT_VAR.write(SETUPSCRIPT)
SETUPSCRIPT_VAR.close()
os.chmod(SETUPSCRIPT_PATH, 0o777)
# Close the grub script.
GRUBSCRIPT_PATH = os.path.join(absinstallpath, "grubscript.sh")
GRUBSCRIPT_VAR = open(GRUBSCRIPT_PATH, mode='w')
GRUBSCRIPT_VAR.write(GRUBSCRIPT)
GRUBSCRIPT_VAR.close()
os.chmod(GRUBSCRIPT_PATH, 0o777)
# Remove resolv.conf before chroot
if os.path.exists("{0}/etc/resolv.conf".format(absinstallpath)):
    os.remove("{0}/etc/resolv.conf".format(absinstallpath))
# Run the setup script.
if args.zch is True:
    subprocess.run("{1}/zch.py {0} -c /setupscript.sh".format(absinstallpath, SCRIPTDIR), shell=True)
else:
    subprocess.run("systemd-nspawn -D {0} /setupscript.sh".format(absinstallpath), shell=True)
# Copy resolv.conf into chroot (needed for chroot)
if os.path.exists("/etc/resolv.conf"):
    shutil.copy2("/etc/resolv.conf", "{0}/etc/resolv.conf".format(absinstallpath))
# Run the grub script.
subprocess.run("{1}/zch.py {0} -c /grubscript.sh".format(absinstallpath, SCRIPTDIR), shell=True)
# Remove after running
os.remove(SETUPSCRIPT_PATH)
os.remove(GRUBSCRIPT_PATH)
print("Script finished successfully.")
