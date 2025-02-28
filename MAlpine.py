#!/usr/bin/env python3
"""Install Alpine Software"""

# Python includes.
import argparse
import os
import re
import shutil
import subprocess
import sys
# Custom includes
import CFunc
import CFuncExt

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]


### Functions ###
def apkinstall(apks):
    """Install packages with apk."""
    subprocess.run("apk add {0}".format(apks), shell=True)


# Get arguments
parser = argparse.ArgumentParser(description='Install Alpine Software.')
parser.add_argument("-d", "--desktop", help='Desktop Environment (i.e. gnome, kde, mate, etc)')
parser.add_argument("-x", "--nogui", help='Configure script to disable GUI.', action="store_true")

# Save arguments.
args = parser.parse_args()
print("Desktop Environment:", args.desktop)

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)

# Get VM State
vmstatus = CFunc.getvmstate()


# Uncomment community repo in repositories
with open(os.path.join(os.sep, "etc", "apk", "repositories"), 'r') as sfile:
    lines = sfile.readlines()
with open(os.path.join(os.sep, "etc", "apk", "repositories"), 'w') as tfile:
    # Replace the # on the 3rd line.
    lines[2] = re.sub("#", "", lines[2])
    tfile.writelines(lines)
subprocess.run("apk upgrade --update-cache --available", shell=True)

### Software ###
apkinstall("git nano sudo bash zsh fish shadow")
# Sudoers changes
CFuncExt.SudoersEnvSettings()
# Edit sudoers to add dnf.
sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
CFunc.AddLineToSudoersFile(sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("apk")))
# Avahi
apkinstall("avahi")
subprocess.run("rc-update add avahi-daemon", shell=True)


# GUI Packages
if not args.nogui:
    # Dbus/udev
    apkinstall("dbus dbus-x11 udev")
    subprocess.run("rc-update add dbus", shell=True)
    subprocess.run("rc-update add udev", shell=True)
    # Xorg and wayland
    subprocess.run("setup-xorg-base", shell=True)
    subprocess.run("setup-wayland-base", shell=True)
    apkinstall("xhost xrandr font-ubuntu font-dejavu font-liberation font-noto")
    # Addons for GUI
    apkinstall("libinput")
    # Gvfs
    apkinstall("gvfs-cdda gvfs-goa gvfs-mtp gvfs-smb gvfs gvfs-afc gvfs-nfs gvfs-archive gvfs-fuse gvfs-gphoto2 gvfs-avahi")
    # Browsers
    apkinstall("firefox")

    # Install Desktop Software
    if args.desktop == "gnome":
        subprocess.run("setup-desktop gnome", shell=True)
    elif args.desktop == "kde":
        subprocess.run("setup-desktop plasma", shell=True)
    elif args.desktop == "mate":
        subprocess.run("setup-desktop mate", shell=True)
    elif args.desktop == "xfce":
        subprocess.run("setup-desktop xfce", shell=True)

# Install software for VMs
if vmstatus == "kvm":
    apkinstall("qemu-guest-agent")
    subprocess.run("rc-update add qemu-guest-agent", shell=True)
if vmstatus == "vbox":
    apkinstall("virtualbox-guest-additions")
    if not args.nogui:
        apkinstall("virtualbox-guest-additions-x11")
    subprocess.run("rc-update add virtualbox-guest-additions", shell=True)

subprocess.run("apk fix", shell=True)

# Extra scripts
subprocess.run(os.path.join(SCRIPTDIR, "CCSClone.py"), shell=True, check=True)
subprocess.run(os.path.join(SCRIPTDIR, "Csshconfig.py"), shell=True, check=True)
subprocess.run(os.path.join(SCRIPTDIR, "CShellConfig.py") + " -f -z -d", shell=True, check=True)
subprocess.run(os.path.join(SCRIPTDIR, "CDisplayManagerConfig.py"), shell=True, check=True)
subprocess.run(os.path.join(SCRIPTDIR, "CVMGeneral.py"), shell=True, check=True)
subprocess.run(os.path.join(SCRIPTDIR, "Cxdgdirs.py"), shell=True, check=True)
# subprocess.run(os.path.join(SCRIPTDIR, "Czram.py"), shell=True, check=True)
subprocess.run(os.path.join(SCRIPTDIR, "CSysConfig.sh"), shell=True, check=True)
