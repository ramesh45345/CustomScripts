#!/usr/bin/env python3
"""Install Fedora Software"""

# Python includes.
import argparse
import grp
import os
import platform
import pwd
import shutil
import subprocess
import sys

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]

# Get arguments
parser = argparse.ArgumentParser(description='Install Fedora Software.')
parser.add_argument("-d", "--desktop", dest="desktop", type=int, help='Desktop Environment', default="0")

# Save arguments.
args = parser.parse_args()
print("Desktop Environment:", args.desktop)

# Exit if not root.
if os.geteuid() is not 0:
    sys.exit("\nError: Please run this script as root.\n")

# Get non-root user information.
if os.getenv("SUDO_USER") not in ["root", None]:
    USERNAMEVAR = os.getenv("SUDO_USER")
elif os.getenv("USER") not in ["root", None]:
    USERNAMEVAR = os.getenv("USER")
else:
    # https://docs.python.org/3/library/pwd.html
    USERNAMEVAR = pwd.getpwuid(1000)[0]
# https://docs.python.org/3/library/grp.html
USERGROUP = grp.getgrgid(pwd.getpwnam(USERNAMEVAR)[3])[0]
USERHOME = os.path.expanduser("~{0}".format(USERNAMEVAR))
MACHINEARCH = platform.machine()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)

# Get VM State
# Detect QEMU
with open('/sys/devices/virtual/dmi/id/sys_vendor', 'r') as VAR:
    QEMUGUEST = bool("QEMU" in VAR.read().strip())
# Detect Virtualbox
with open('/sys/devices/virtual/dmi/id/product_name', 'r') as VAR:
    VBOXGUEST = bool("VirtualBox" in VAR.read().strip())
# Detect VMWare
with open('/sys/devices/virtual/dmi/id/sys_vendor', 'r') as VAR:
    VMWGUEST = bool("VMware" in VAR.read().strip())

# Set up Fedora Repos
REPOSCRIPT = """#!/bin/bash

# RPMFusion
dnf install -y https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm

# Adobe Flash
dnf -y install http://linuxdownload.adobe.com/adobe-release/adobe-release-$(uname -i)-1.0-1.noarch.rpm
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-adobe-linux

# Visual Studio Code
rpm --import https://packages.microsoft.com/keys/microsoft.asc
echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo

# Fish Shell
dnf config-manager --add-repo "http://download.opensuse.org/repositories/shells:fish:release:2/Fedora_$(rpm -E %fedora)/shells:fish:release:2.repo"

# Adapta
dnf copr enable -y heikoada/gtk-themes

# Update
dnf update -y
"""
subprocess.run(REPOSCRIPT, shell=True)

# Install Fedora Software
SOFTWARESCRIPT = """
# Install cli tools
dnf install -y fish nano tmux iotop rsync p7zip p7zip-plugins zip unzip unrar xdg-utils xdg-user-dirs util-linux-user fuse-sshfs redhat-lsb-core openssh-server openssh-clients
systemctl enable sshd

# Install GUI packages
dnf install -y @fonts @base-x @networkmanager-submodules avahi
dnf install -y powerline-fonts google-roboto-fonts google-noto-sans-fonts

# Management tools
dnf install -y yumex-dnf dnfdragora dnfdragora-gui gparted

# Install browsers
# dnf install -y chromium
dnf install -y https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
dnf install -y @firefox freshplayerplugin
dnf install -y flash-plugin

# Samba
dnf install -y samba
systemctl enable smb

# NTP configuration
systemctl enable systemd-timesyncd
timedatectl set-local-rtc false
timedatectl set-ntp 1

# Cups
dnf install -y cups-pdf

# Wine
dnf install -y wine playonlinux

# Audio/video
dnf install -y pulseaudio-module-zeroconf pulseaudio-utils paprefs ladspa-swh-plugins
dnf install -y gstreamer1-libav gstreamer1-vaapi gstreamer1-plugins-ugly gstreamer1-plugins-bad-freeworld gstreamer1-plugins-bad-nonfree
dnf install -y youtube-dl ffmpeg vlc smplayer mpv
dnf install -y audacious audacious-plugins-freeworld

# Editors
dnf install -y code

# Tilix
dnf install -y tilix tilix-nautilus

# Remote access
dnf install -y remmina remmina-plugins-vnc remmina-plugins-rdp

# Syncthing
dnf copr enable -y decathorpe/syncthing
dnf install -y syncthing syncthing-inotify

"""
# Install software for VMs
if QEMUGUEST is True:
    SOFTWARESCRIPT += "\ndnf install -y spice-vdagent qemu-guest-agent"
if VBOXGUEST is True:
    SOFTWARESCRIPT += "\ndnf install -y VirtualBox-guest-additions kmod-VirtualBox"
if VMWGUEST is True:
    SOFTWARESCRIPT += "\ndnf install -y open-vm-tools open-vm-tools-desktop"
subprocess.run(SOFTWARESCRIPT, shell=True)

# Install Desktop Software
DESKTOPSCRIPT = """"""
if args.desktop == 1:
    DESKTOPSCRIPT += """
# Gnome
dnf install -y @workstation-product @gnome-desktop
systemctl enable -f gdm
# Some Gnome Extensions
dnf install -y gnome-terminal-nautilus gnome-tweak-tool dconf-editor
dnf install -y gnome-shell-extension-gpaste gnome-shell-extension-media-player-indicator gnome-shell-extension-topicons-plus
{0}/DExtGnome.sh -d -v
# Adapta
dnf install -y gnome-shell-theme-adapta adapta-gtk-theme-metacity adapta-gtk-theme-gtk2 adapta-gtk-theme-gtk3
# Remmina Gnome integration
dnf install -y remmina-plugins-gnome
""".format(SCRIPTDIR)
elif args.desktop == 2:
    DESKTOPSCRIPT += """
# KDE
dnf install -y @kde-desktop-environment
dnf install -y ark latte-dock
systemctl enable -f sddm
"""
elif args.desktop == 3:
    DESKTOPSCRIPT += """
# MATE
dnf install -y @mate-desktop @mate-applications
systemctl enable -f lightdm
# Applications
dnf install -y dconf-editor
"""

DESKTOPSCRIPT += """
# Numix
dnf install -y numix-icon-theme-circle
# Update pixbuf cache after installing icons (for some reason doesn't do this automatically).
gdk-pixbuf-query-loaders-64 --update-cache

systemctl set-default graphical.target

# Delete defaults in sudoers.
if grep -iq $'^Defaults    secure_path' /etc/sudoers; then
    sed -e 's/^Defaults    env_reset$/Defaults    !env_reset/g' -i /etc/sudoers
	sed -i $'/^Defaults    mail_badpass/ s/^#*/#/' /etc/sudoers
	sed -i $'/^Defaults    secure_path/ s/^#*/#/' /etc/sudoers
fi
visudo -c
"""
subprocess.run(DESKTOPSCRIPT, shell=True)

# Add normal user to all reasonable groups
with open("/etc/group", 'r') as groups:
    grparray = []
    # Split the grouplist into lines
    grouplist = groups.readlines()
    # Iterate through all groups in grouplist
    for line in grouplist:
        # Remove portion after :
        splitline = line.split(":")[0]
        # Check group before adding it.
        if splitline != "root" and \
            splitline != "users" and \
            splitline != "nobody" and \
            splitline != "nogroup" and \
            splitline != USERGROUP:
            # Add group to array.
            grparray.append(line.split(":")[0])
# Add all detected groups to the current user.
for grp in grparray:
    print("Adding {0} to group {1}.".format(USERNAMEVAR, grp))
    subprocess.run("usermod -aG {1} {0}".format(USERNAMEVAR, grp), shell=True, check=True)

# Edit sudoers to add dnf.
if os.path.isdir('/etc/sudoers.d'):
    CUSTOMSUDOERSPATH = "/etc/sudoers.d/pkmgt"
    print("Writing {0}".format(CUSTOMSUDOERSPATH))
    with open(CUSTOMSUDOERSPATH, 'w') as sudoers_writefile:
        sudoers_writefile.write("""%wheel ALL=(ALL) ALL
{0} ALL=(ALL) NOPASSWD: {1}
""".format(USERNAMEVAR, shutil.which("dnf")))
    os.chmod(CUSTOMSUDOERSPATH, 0o440)
    status = subprocess.run('visudo -c', shell=True)
    if status.returncode is not 0:
        print("Visudo status not 0, removing sudoers file.")
        os.remove(CUSTOMSUDOERSPATH)

# Run only on real machine
if QEMUGUEST is not True and VBOXGUEST is not True and VMWGUEST is not True:
    # Powertop
    subprocess.run("dnf install -y powertop smartmontools hdparm; systemctl enable powertop", shell=True)

# Use atom unofficial repo
# https://github.com/alanfranz/atom-text-editor-repository
ATOMREPOFILE = "/etc/yum.repos.d/atom.repo"
with open(ATOMREPOFILE, 'w') as atomrepo_writefile:
    atomrepo_writefile.write("""[atom]
name=atom
baseurl=https://dl.bintray.com/alanfranz/atom-yum
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://www.franzoni.eu/keys/D401AB61.txt""")
# Install Atom
subprocess.run("dnf install -y atom", shell=True)

# Disable Selinux
# To get selinux status: sestatus, getenforce
# To enable or disable selinux temporarily: setenforce 1 (to enable), setenforce 0 (to disable)
subprocess.run("sed -i 's/^SELINUX=.*/SELINUX=disabled/g' /etc/selinux/config /etc/sysconfig/selinux", shell=True)