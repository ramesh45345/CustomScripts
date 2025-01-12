#!/usr/bin/env python3
"""Install FreeBSD Software"""

# Python includes.
import argparse
from datetime import datetime
import os
import shutil
import subprocess
# Custom includes
import CFunc
import CFuncExt

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Install FreeBSD Software.')
parser.add_argument("-d", "--desktop", help='Desktop Environment (i.e. gnome, kde, mate, etc)')
parser.add_argument("-x", "--nogui", help='Configure script to disable GUI.', action="store_true")

# Save arguments.
args = parser.parse_args()
print("Desktop Environment:", args.desktop)


### Functions ###
def pkg_install(packages):
    """Installl package using pkg"""
    subprocess.run("pkg install -y {0}".format(packages), shell=True, check=True)
    return
def sysrc_cmd(cmd):
    """Run command for sysrc"""
    subprocess.run("sysrc {0}".format(cmd), shell=True, check=True)
    return
def setup_slim(slim_session_name):
    pkg_install("slim")
    sysrc_cmd('slim_enable=yes')
    sysrc_cmd('gdm_enable=')
    sysrc_cmd('sddm_enable=')
    # Setup slim
    with open(os.path.join(os.sep, "root", ".xinitrc"), 'w') as file:
        file.write("exec {0}".format(slim_session_name))
    with open(os.path.join(USERHOME, ".xinitrc"), 'w') as file:
        file.write("exec {0}".format(slim_session_name))


# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)
# Time script was started.
time_start = datetime.now()

# Override FreeBSD Quarterly repo with latest repo
os.makedirs("/usr/local/etc/pkg/repos", exist_ok=True)
with open("/usr/local/etc/pkg/repos/FreeBSD.conf", 'w') as file:
    file.write('FreeBSD: { url: "pkg+http://pkg.FreeBSD.org/${ABI}/latest" }')

# Update system
subprocess.run(["freebsd-update", "--not-running-from-cron", "fetch", "install"], check=True)
# Update packages
subprocess.run(["pkg", "update", "-f"], check=True)

# Get VM State
pkg_install("dmidecode")
vmstatus = CFunc.getvmstate()


### Install FreeBSD Software ###
# Cli tools
pkg_install("git python3 sudo nano bash zsh tmux rsync wget 7-zip zip unzip xdg-utils xdg-user-dirs fusefs-sshfs")
pkg_install("powerline-fonts ubuntu-font roboto-fonts-ttf noto-basic liberation-fonts-ttf")
# Portmaster
pkg_install("portmaster")
# Avahi
pkg_install("avahi-app avahi-autoipd avahi-libdns nss_mdns")
sysrc_cmd('dbus_enable=yes avahi_daemon_enable=yes avahi_dnsconfd_enable=yes')
# Samba
pkg_install("samba419")
sysrc_cmd('samba_server_enable=yes winbindd_enable=yes')
# NTP Configuration
sysrc_cmd('ntpd_enable=yes')
# GUI Packages
if not args.nogui:
    # Browsers
    pkg_install("firefox")
    # Wine
    pkg_install("wine winetricks")
    # Remote access
    pkg_install("remmina")
    # Editors
    pkg_install("geany")
    # Terminator
    pkg_install("terminator")

# Install software for VMs
if vmstatus == "vbox":
    pkg_install("virtualbox-ose-additions")
    sysrc_cmd('vboxguest_enable=yes vboxservice_enable=yes')

# Install Desktop Software
if not args.nogui:
    pkg_install("xorg xorg-drivers")
    sysrc_cmd("moused_enable=yes dbus_enable=yes hald_enable=yes")
if args.desktop == "gnome":
    pkg_install("gnome")
    sysrc_cmd('gdm_enable=yes')
    sysrc_cmd('slim_enable=')
    slim_session_name = "gnome-session"
    pkg_install("gnome-shell-extension-dashtopanel")
    subprocess.run("glib-compile-schemas /usr/local/share/gnome-shell/extensions/dash-to-panel@jderose9.github.com/schemas", shell=True, check=True)
elif args.desktop == "kde":
    pkg_install("plasma6-plasma sddm")
    sysrc_cmd('sddm_enable=yes')
    sysrc_cmd('slim_enable=')
elif args.desktop == "mate":
    pkg_install("mate")
    setup_slim("mate-session")
elif args.desktop == "lumina":
    pkg_install("lumina")
    setup_slim("lumina-session")

# Post-desktop installs
if not args.nogui:
    # Numix Icon Theme
    CFuncExt.numix_icons(os.path.join(os.sep, "usr", "local", "share", "icons"))

# Edit sudoers to add pkg.
CFuncExt.SudoersEnvSettings(sudoers_file="/usr/local/etc/sudoers")
# Edit sudoers to add apt.
sudoersfile = os.path.join(os.sep, "usr", "local", "etc", "sudoers.d", "pkmgt")
CFunc.AddLineToSudoersFile(sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("pkg")))
subprocess.run("pw usermod {0} -G wheel,video,operator".format(USERNAMEVAR), shell=True, check=True)

# Extra scripts
subprocess.run("{0}/CCSClone.py".format(SCRIPTDIR), shell=True, check=True)
subprocess.run("{0}/CShellConfig.py -z -d".format(SCRIPTDIR), shell=True, check=True)
subprocess.run("{0}/CDisplayManagerConfig.py".format(SCRIPTDIR), shell=True, check=True)
subprocess.run("{0}/CVMGeneral.py".format(SCRIPTDIR), shell=True, check=True)
subprocess.run("{0}/Cxdgdirs.py".format(SCRIPTDIR), shell=True, check=True)
subprocess.run("bash {0}/CSysConfig.sh".format(SCRIPTDIR), shell=True, check=True)

# Wait for processes to finish before exiting.
time_finishmain = datetime.now()

print("\nScript End in {0}".format(str(time_finishmain - time_start)))
