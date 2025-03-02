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
    subprocess.run(f"apk add {apks}", shell=True)
def rcupdate_add(service: str):
    """Add a service to startup."""
    subprocess.run(f"rc-update add {service}", shell=True)


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
apkinstall("btop git nano sudo bash zsh fish shadow tmux perl-datetime-hires rsync curl util-linux util-linux-login")
# Sudoers changes
CFuncExt.SudoersEnvSettings()
# Edit sudoers to add dnf.
sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
CFunc.AddLineToSudoersFile(sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("apk")))
# Avahi
apkinstall("avahi")
rcupdate_add("avahi-daemon")
# Network Manager
apkinstall("networkmanager networkmanager-tui networkmanager-cli networkmanager-wifi wpa_supplicant")
rcupdate_add("networkmanager default")
subprocess.run("rc-update del networking boot", shell=True)
subprocess.run("rc-update del wpa_supplicant boot", shell=True)
with open(os.path.join(os.sep, "etc", "NetworkManager", "NetworkManager.conf"), 'w') as f:
    f.write("""[main]
dhcp=internal
plugins=ifupdown,keyfile

[ifupdown]
managed=true

[device]
wifi.scan-rand-mac-address=yes
wifi.backend=wpa_supplicant
""")

# GUI Packages
if not args.nogui:
    # Xorg and wayland
    subprocess.run("setup-xorg-base", shell=True)
    subprocess.run("setup-wayland-base", shell=True)
    apkinstall("xhost xrandr font-ubuntu font-dejavu font-liberation font-noto")
    # Addons for GUI
    apkinstall("libinput")
    # Gvfs
    apkinstall("gvfs-cdda gvfs-goa gvfs-mtp gvfs-smb gvfs gvfs-afc gvfs-nfs gvfs-archive gvfs-fuse gvfs-gphoto2 gvfs-avahi")
    # udev
    subprocess.run("setup-devd udev", shell=True)
    # elogind
    apkinstall("elogind polkit polkit-elogind")
    rcupdate_add("elogind")
    rcupdate_add("polkit")
    # Browsers
    apkinstall("firefox")

    # Install Desktop Software
    if args.desktop == "gnome":
        subprocess.run("setup-desktop gnome", shell=True)
    elif args.desktop == "kde":
        subprocess.run("setup-desktop plasma", shell=True)
        apkinstall("plasma-nm")
    elif args.desktop == "mate":
        subprocess.run("setup-desktop mate", shell=True)
        apkinstall("network-manager-applet")
    elif args.desktop == "xfce":
        subprocess.run("setup-desktop xfce", shell=True)
        apkinstall("network-manager-applet")

# Install software for VMs
if vmstatus == "kvm":
    apkinstall("qemu-guest-agent spice-vdagent")
    rcupdate_add("qemu-guest-agent")
    rcupdate_add("spice-vdagentd")
if vmstatus == "vbox":
    apkinstall("virtualbox-guest-additions")
    if not args.nogui:
        apkinstall("virtualbox-guest-additions-x11")
    rcupdate_add("virtualbox-guest-additions")

# Add user to groups
CFunc.AddUserToGroup("dialout")
CFunc.AddUserToGroup("disk")
CFunc.AddUserToGroup("plugdev")
CFunc.AddUserToGroup("video")
CFunc.AddUserToGroup("wheel")

# Fix any I/O errors
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
