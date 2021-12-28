#!/usr/bin/env python3
"""Install CentOS 8 Software"""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
# Custom includes
import CFunc
import CFuncExt

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]

# Get arguments
parser = argparse.ArgumentParser(description='Install CentOS 8 Software.')
parser.add_argument("-d", "--desktop", help='Desktop Environment (choices: %(choices)s) (default: %(default)s)', default="kde", choices=["gnome", "kde"])
parser.add_argument("-x", "--nogui", help='Configure script to disable GUI.', action="store_true")

# Save arguments.
args = parser.parse_args()
print("Desktop Environment:", args.desktop)
print("No GUI:", args.nogui)

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)

# Get VM State
vmstatus = CFunc.getvmstate()

### Repos ###
# Enable powertools
subprocess.run(["dnf", "config-manager", "--set-enabled", "powertools"], check=True)
# EPEL
CFunc.dnfinstall("https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm")
# RPMFusion
CFunc.dnfinstall("https://download1.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm https://download1.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-8.noarch.rpm")
# Visual Studio Code
CFunc.rpmimport("https://packages.microsoft.com/keys/microsoft.asc")
with open("/etc/yum.repos.d/vscode.repo", 'w') as vscoderepofile_write:
    vscoderepofile_write.write('[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc"')
# EL Repo
# https://elrepo.org
subprocess.run("rpm --import https://www.elrepo.org/RPM-GPG-KEY-elrepo.org ; dnf install -y https://www.elrepo.org/elrepo-release-8.0-2.el8.elrepo.noarch.rpm ; dnf config-manager --enable elrepo-kernel", shell=True)

# Update system after enabling repos.
CFunc.dnfupdate()

### Install CentOS Software ###
# Cli tools
CFunc.dnfinstall("zsh fish nano tmux iotop rsync p7zip p7zip-plugins zip unzip xdg-utils xdg-user-dirs util-linux-user redhat-lsb-core openssh-server openssh-clients avahi")
CFunc.sysctl_enable("sshd avahi-daemon")
CFunc.dnfinstall("google-noto-sans-fonts")
# Samba
CFunc.dnfinstall("samba")
CFunc.sysctl_enable("smb")
# cifs-utils
CFunc.dnfinstall("cifs-utils")
# Enable setuid for mount.cifs to enable mounting as a normal user
subprocess.run("sudo chmod u+s /sbin/mount.cifs", shell=True)
# NTP Configuration
subprocess.run("systemctl enable systemd-timesyncd; timedatectl set-local-rtc false; timedatectl set-ntp 1", shell=True)
# Install kernel
CFunc.dnfinstall("kernel-ml kernel-ml-devel kernel-ml-modules-extra")
# Install powerline fonts
powerline_git_path = os.path.join(tempfile.gettempdir(), "pl-fonts")
CFunc.gitclone("https://github.com/powerline/fonts", powerline_git_path)
subprocess.run(os.path.join(powerline_git_path, "install.sh"), shell=True)
CFunc.run_as_user(USERNAMEVAR, os.path.join(powerline_git_path, "install.sh"))
shutil.rmtree(powerline_git_path)
# firewalld
CFunc.dnfinstall("firewalld")
CFunc.sysctl_enable("firewalld", now=True, error_on_fail=True)
CFuncExt.FirewalldConfig()

# GUI Packages
if not args.nogui:
    CFunc.dnfinstall("@base-x")
    # Enable graphical target
    subprocess.run("systemctl set-default graphical.target", shell=True)
    # Browsers
    CFunc.dnfinstall("firefox")
    # Editors
    CFunc.dnfinstall("code")
    # Flameshot
    CFunc.dnfinstall("flameshot")
    os.makedirs(os.path.join(USERHOME, ".config", "autostart"), exist_ok=True)
    # Start flameshot on user login.
    if os.path.isfile(os.path.join(os.sep, "usr", "share", "applications", "flameshot.desktop")):
        shutil.copy(os.path.join(os.sep, "usr", "share", "applications", "flameshot.desktop"), os.path.join(USERHOME, ".config", "autostart"))
    CFunc.chown_recursive(os.path.join(USERHOME, ".config", ), USERNAMEVAR, USERGROUP)

    # Numix Icon Theme
    CFuncExt.numix_icons(os.path.join(os.sep, "usr", "local", "share", "icons"))

# Desktop Environments
if args.desktop == "gnome":
    # Workstation
    CFunc.dnfinstall("@workstation --skip-broken")
    # Misc tools
    CFunc.dnfinstall("dconf-editor chrome-gnome-shell")
    # Gnome Stuff
    CFunc.dnfinstall("gnome-tweaks")
    # Gnome Shell extensions
    # Install gs installer script.
    gs_installer = CFunc.downloadfile("https://raw.githubusercontent.com/brunelli/gnome-shell-extension-installer/master/gnome-shell-extension-installer", os.path.join(os.sep, "usr", "local", "bin"), overwrite=True)
    os.chmod(gs_installer[0], 0o777)
    # Install volume extension
    CFunc.run_as_user(USERNAMEVAR, "{0} --yes 858".format(gs_installer[0]))
    # Install dashtodock extension
    CFunc.run_as_user(USERNAMEVAR, "{0} --yes 307".format(gs_installer[0]))
    # Topicons plus
    CFunc.run_as_user(USERNAMEVAR, "{0} --yes 1031".format(gs_installer[0]))
elif args.desktop == "kde":
    # Plasma
    CFunc.dnfinstall('--skip-broken install @"KDE Plasma Workspaces" --exclude kf5-akonadi-server-mysql')
    CFunc.sysctl_enable("sddm")

# Install software for VMs
if vmstatus == "kvm":
    CFunc.dnfinstall("spice-vdagent qemu-guest-agent")
if vmstatus == "vbox":
    CFunc.dnfinstall("virtualbox-guest-additions virtualbox-guest-additions-ogl")
if vmstatus == "vmware":
    CFunc.dnfinstall("open-vm-tools")
    if not args.nogui:
        CFunc.dnfinstall("open-vm-tools-desktop")

# Add normal user to all reasonable groups
CFunc.AddUserToGroup("disk")
CFunc.AddUserToGroup("lp")
CFunc.AddUserToGroup("wheel")
CFunc.AddUserToGroup("cdrom")
CFunc.AddUserToGroup("man")
CFunc.AddUserToGroup("dialout")
CFunc.AddUserToGroup("floppy")
CFunc.AddUserToGroup("games")
CFunc.AddUserToGroup("tape")
CFunc.AddUserToGroup("video")
CFunc.AddUserToGroup("audio")
CFunc.AddUserToGroup("input")
CFunc.AddUserToGroup("kvm")
CFunc.AddUserToGroup("systemd-journal")
CFunc.AddUserToGroup("systemd-resolve")
CFunc.AddUserToGroup("pipewire")
CFunc.AddUserToGroup("colord")
CFunc.AddUserToGroup("nm-openconnect")

# Sudoers changes
CFuncExt.SudoersEnvSettings()
# Edit sudoers to add dnf.
fedora_sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
CFunc.AddLineToSudoersFile(fedora_sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("dnf")))

# Hdparm
CFunc.dnfinstall("smartmontools hdparm")

if not args.nogui:
    # Flatpak setup
    CFunc.dnfinstall("flatpak xdg-desktop-portal")
    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("flatpak")))

    # Flatpak apps
    subprocess.run(os.path.join(SCRIPTDIR, "CFlatpakConfig.py"), shell=True, check=True)

# Disable Selinux
# To get selinux status: sestatus, getenforce
CFuncExt.GrubEnvAdd(os.path.join(os.sep, "etc", "default", "grub"), "GRUB_CMDLINE_LINUX", "selinux=0")
CFuncExt.GrubUpdate()
subprocess.run('grubby --update-kernel=ALL --args="selinux=0"', shell=True, check=True)
subprocess.run("sed -i 's/^SELINUX=.*/SELINUX=disabled/g' /etc/selinux/config /etc/sysconfig/selinux", shell=True, check=False)

# Disable mitigations
CFuncExt.GrubEnvAdd(os.path.join(os.sep, "etc", "default", "grub"), "GRUB_CMDLINE_LINUX", "mitigations=off")
CFuncExt.GrubUpdate()
subprocess.run('grubby --update-kernel=ALL --args="mitigations=off"', shell=True, check=True)

# Extra scripts
subprocess.run("{0}/Csshconfig.sh".format(SCRIPTDIR), shell=True)
subprocess.run("{0}/CShellConfig.py -z -d".format(SCRIPTDIR), shell=True)
subprocess.run("{0}/CCSClone.py".format(SCRIPTDIR), shell=True)
subprocess.run("{0}/CDisplayManagerConfig.py".format(SCRIPTDIR), shell=True)
subprocess.run("{0}/CVMGeneral.py".format(SCRIPTDIR), shell=True)
subprocess.run("{0}/Cxdgdirs.py".format(SCRIPTDIR), shell=True)
subprocess.run("{0}/Czram.py".format(SCRIPTDIR), shell=True)
subprocess.run("{0}/CSysConfig.sh".format(SCRIPTDIR), shell=True)

print("\nScript End")
