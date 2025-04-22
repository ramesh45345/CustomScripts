#!/usr/bin/env python3
"""Turn screen off using dpms."""

# Script powersaves the display every 20 seconds. Useful if a proper screensaver or power management isn't active for the current system.
# Parameter 1 is the delay to start the sleep cycle. Parameter 2 is the gap between setting the displays off when inside the loop.

# Python includes.
import argparse
import os
import subprocess
import time
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))


### Functions ###
def is_wayland():
    """Determine if wayland is used. Return true if wayland."""
    loginctl_value = CFunc.subpout("loginctl show-session $(loginctl|grep $(whoami) |awk '{print $1}') -p Type --value", error_on_fail=False)
    if loginctl_value == "wayland":
        return True
    else:
        return False
def is_kde():
    """Determine if KDE Plasma (kwin) is being used."""
    if subprocess.run(["pgrep", "kwin"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0:
        return True
    else:
        return False
def is_gnome():
    """Determine if Gnome (gnome-shell) is being used."""
    if subprocess.run(["pgrep", "gnome-shell"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0:
        return True
    else:
        return False
def kde_dpms():
    """DPMS for Plasma desktop."""
    subprocess.run("dbus-send --session --print-reply --dest=org.kde.kglobalaccel  /component/org_kde_powerdevil org.kde.kglobalaccel.Component.invokeShortcut string:'Turn Off Screen'", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, check=True)
def gnome_dpms():
    """DPMS for Gnome desktop."""
    subprocess.run("busctl --user call org.gnome.Shell /org/gnome/ScreenSaver org.gnome.ScreenSaver SetActive b true", shell=True, check=True)
def xset_dpms():
    """DPMS for xorg."""
    subprocess.run("xset dpms force off", shell=True, check=True)
def dpms_detect():
    """Detect system for dpms."""
    system_type = ""
    if is_kde():
        system_type = "kde"
    elif is_gnome():
        system_type = "gnome"
    elif not is_wayland():
        system_type = "x11"
    return system_type
def dpms_execute(dpms_type: str = ""):
    """Execute DPMS."""
    if dpms_type == "":
        dpms_type = dpms_detect()
    if dpms_type == "kde":
        kde_dpms()
    if dpms_type == "gnome":
        gnome_dpms()
    if dpms_type == "x11":
        xset_dpms()


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Turn screen off using dpms.')
    parser.add_argument("-i", "--init", help='Initial timeout before starting dpms loop.', type=int, default=5)
    parser.add_argument("-c", "--continuous", help='Continual timeout within dpms loop.', type=int, default=30)
    args = parser.parse_args()

    dpms_system_type = dpms_detect()
    print("Init Timeout: {0}, Continuous Timeout: {1}".format(args.init, args.continuous))
    print("DPMS type: {0}".format(dpms_system_type))

    # DPMS loop
    time.sleep(args.init)
    while True:
        dpms_execute(dpms_system_type)
        time.sleep(args.continuous)
