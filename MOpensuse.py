#!/usr/bin/env python3
"""Install OpenSUSE Software"""

# Python includes.
import argparse
import os
import shutil
import subprocess
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Install OpenSUSE Software.')
parser.add_argument("-d", "--desktop", help='Desktop Environment (i.e. gnome, kde, mate, etc)')
parser.add_argument("-a", "--allextra", help='Run Extra Scripts', action="store_true")

# Save arguments.
args = parser.parse_args()
print("Desktop Environment:", args.desktop)
print("Run extra scripts:", args.allextra)

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)

# Get VM State
vmstatus = CFunc.getvmstate()

# Set up OpenSUSE Repos
REPOSCRIPT = """#!/bin/bash

# Remove existing CD repo
source /etc/os-release
if ls /etc/zypp/repos.d/openSUSE-$VERSION_ID*.repo; then
    rm /etc/zypp/repos.d/openSUSE-$VERSION_ID*.repo
fi
# Add tumbleweed online repos
zypper ar -f http://download.opensuse.org/tumbleweed/repo/oss/ repo-oss
zypper ar -f http://download.opensuse.org/update/tumbleweed/ repo-update
# Add non-oss tumbleweed repo
zypper ar -f http://download.opensuse.org/tumbleweed/repo/non-oss/ repo-non-oss

# Packman
zypper ar -f -n packman http://ftp.gwdg.de/pub/linux/misc/packman/suse/openSUSE_Tumbleweed/ packman

# Numix repo
zypper ar -f http://download.opensuse.org/repositories/home:/lbssousa:/numix/openSUSE_Tumbleweed/ "lbssousa-numix"

# Terminix repo
zypper ar -f http://download.opensuse.org/repositories/devel:/languages:/D/openSUSE_Tumbleweed/ "devel:languages:D"

# Emulators
zypper ar -f http://download.opensuse.org/repositories/Emulators/openSUSE_Tumbleweed/ "Emulators"

# Import all gpg keys
zypper --non-interactive --gpg-auto-import-keys refresh

"""
subprocess.run(REPOSCRIPT, shell=True)

# Install Software
SOFTWARESCRIPT = """
# Install cli tools
zypper in -yl zsh nano tmux iotop rsync p7zip zip unzip xdg-utils xdg-user-dirs

# Management tools
zypper in -yl gparted leafpad

# Install browsers
zypper in -yl chromium MozillaFirefox
# Adobe Flash
zypper in -yl flash-player-ppapi freshplayerplugin

# Samba
zypper in -yl samba samba-client
systemctl enable smb

# NTP configuration
systemctl disable ntpd
systemctl enable systemd-timesyncd
timedatectl set-local-rtc false
timedatectl set-ntp 1

# Cups
zypper in -yl cups-pdf

# Wine
zypper in -yl wine wine-32bit PlayOnLinux

# Libreoffice
zypper in -yl libreoffice

# Multimedia
zypper in -yl libva-vdpau-driver vaapi-intel-driver vaapi-tools libgstvdpau libvdpau_va_gl1 gstreamer-plugins-libav gstreamer-plugins-vaapi
zypper in --from packman -yl audacious vlc ffmpeg youtube-dl
zypper in -yl pavucontrol paprefs smplayer gstreamer-fluendo-mp3
# Fix issue with paprefs. Need to file bug at some point...
ln -sf /usr/lib64/pulse-10.0 /usr/lib64/pulse-9.0

# terminator
# zypper in -yl typelib-1_0-Vte-2.91 terminator
# Terminix
zypper in -yl terminix

# Numix Circle icon theme
zypper in -yl numix-icon-theme-circle

# Fonts
zypper in -yl noto-sans-fonts ubuntu-fonts liberation-fonts google-roboto-fonts

# VNC and synergy
zypper in -yl xorg-x11-Xvnc tigervnc synergy qsynergy

# Change to NetworkManager
systemctl daemon-reload
systemctl disable wicked
systemctl enable NetworkManager
"""
subprocess.run(SOFTWARESCRIPT, shell=True)

# Install software for VMs
if vmstatus == "kvm":
    CFunc.zpinstall("spice-vdagent qemu-guest-agent")
if vmstatus == "vbox":
    CFunc.zpinstall("virtualbox-guest-tools virtualbox-guest-x11")
if vmstatus == "vmware":
    CFunc.zpinstall("open-vm-tools open-vm-tools-desktop")

# Install Desktop Software
DESKTOPSCRIPT = """"""
if args.desktop == "gnome":
    DESKTOPSCRIPT += """
# Gnome
zypper in -yl -t pattern gnome_admin gnome_basis gnome_basis_opt gnome_imaging gnome_utilities gnome_laptop gnome_yast sw_management_gnome
zypper in -yl eog gedit gedit-plugins dconf-editor caribou evince gnome-disk-utility gnome-logs gnome-system-monitor nautilus-evince mousetweaks
zypper in -yl gnome-shell-extension-gpaste gnome-shell-classic
# Remove packagekit/gnome-software-service
[ -f /etc/xdg/autostart/gnome-software-service.desktop ] && rm -f /etc/xdg/autostart/gnome-software-service.desktop
# Change display manager to gdm
zypper in -yl gdm
sed -i 's/DISPLAYMANAGER=.*$/DISPLAYMANAGER="gdm"/g' /etc/sysconfig/displaymanager
"""
elif args.desktop == "kde":
    DESKTOPSCRIPT += """
# KDE
if rpm -iq patterns-yast-x11_yast; then
    zypper rm -y patterns-yast-x11_yast
fi
zypper in -yl -t pattern kde_plasma
zypper in -yl -t pattern kde
# Systray fixes, http://blog.martin-graesslin.com/blog/2014/06/where-are-my-systray-icons/
zypper in -yl libappindicator1 libappindicator3-1 sni-qt sni-qt-32bit
# Change display manager to sddm
zypper in -yl sddm
sed -i 's/DISPLAYMANAGER=.*$/DISPLAYMANAGER="sddm"/g' /etc/sysconfig/displaymanager
"""
elif args.desktop == "mate":
    DESKTOPSCRIPT += """
# MATE
zypper in -yl -t pattern mate_basis mate_admin mate_utilities
# Applications
zypper in -yl --force-resolution dconf-editor atril eom mate-search-tool mate-system-monitor caja-extension-open-terminal caja-extension-atril caja-extension-gksu mate-tweak
# Change display manager to lightdm
zypper in -yl lightdm lightdm-gtk-greeter
sed -i 's/DISPLAYMANAGER=.*$/DISPLAYMANAGER="lightdm"/g' /etc/sysconfig/displaymanager
"""

subprocess.run("systemctl set-default graphical.target", shell=True)

# Edit sudoers to add zypper.
sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
CFunc.AddLineToSudoersFile(sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("zypper")))

# Configure Fonts
FONTSCRIPT = """
sed -i 's/^VERBOSITY=.*$/VERBOSITY="1"/g' /etc/sysconfig/fonts-config
sed -i 's/^FORCE_HINTSTYLE=.*$/FORCE_HINTSTYLE="hintfull"/g' /etc/sysconfig/fonts-config
sed -i 's/^USE_LCDFILTER=.*$/USE_LCDFILTER="lcddefault"/g' /etc/sysconfig/fonts-config
sed -i 's/^USE_RGBA=.*$/USE_RGBA="rgb"/g' /etc/sysconfig/fonts-config
# Execute Changes
/usr/sbin/fonts-config
"""
subprocess.run(FONTSCRIPT, shell=True)

# Extra scripts
if args.allextra is True:
    subprocess.run("{0}/Csshconfig.py".format(SCRIPTDIR), shell=True)
    subprocess.run("{0}/CShellConfig.py -z -f -d".format(SCRIPTDIR), shell=True)
    subprocess.run("{0}/CCSClone.py".format(SCRIPTDIR), shell=True)
    subprocess.run("{0}/CDisplayManagerConfig.py".format(SCRIPTDIR), shell=True)
    subprocess.run("{0}/CVMGeneral.py".format(SCRIPTDIR), shell=True)
    subprocess.run("{0}/Cxdgdirs.py".format(SCRIPTDIR), shell=True)
    subprocess.run("{0}/Czram.py".format(SCRIPTDIR), shell=True)
    subprocess.run("{0}/CSysConfig.sh".format(SCRIPTDIR), shell=True)

print("\nScript End")
