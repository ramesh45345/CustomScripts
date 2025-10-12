#!/usr/bin/env python3
"""General Virtual Machine script."""

# Python includes.
import os
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)

# Get VM State
vmstatus = CFunc.getvmstate()

# Global variables
fstab_path = os.path.join(os.sep, "etc", "fstab")


### Begin Code ###

# KVM/QEMU section
if vmstatus == "kvm":
    # Create randr script
    ra_script_path = os.path.join(os.sep, "usr", "local", "bin", "ra.sh")
    ra_script_text = """#!/bin/bash

sleep 5
if [ -z $DISPLAY ]; then
    echo "Display variable not set. Exiting."
    exit 1;
fi
xhost +localhost
# Detect the display output from xrandr.
RADISPLAYS=$(xrandr --listmonitors | awk '{print $4}')
while true; do
    sleep 1
    # Loop through every detected display and autoset them.
    for disp in ${RADISPLAYS[@]}; do
        xrandr --output $disp --auto
    done
done
"""
    with open(ra_script_path, 'w') as f:
        f.write(ra_script_text)
    os.chmod(ra_script_path, 0o777)
    # Create ra user service
    ra_service_text = """[Unit]
Description=Display Resize script

[Service]
Type=simple
ExecStart={0}
Restart=on-failure
RestartSec=5s
TimeoutStopSec=7s

[Install]
WantedBy=default.target""".format(ra_script_path)
    CFunc.systemd_createuserunit("ra.service", ra_service_text)

    # Set up virtio filesystem mounts.
    fstab_mnt_text = "mnt /mnt/sf_mnt virtiofs defaults,rw,relatime,nofail,x-systemd.automount 0 0"
    fstab_home_text = "home /mnt/sf_home virtiofs defaults,rw,relatime,nofail,x-systemd.automount 0 0"
    if not CFunc.Fstab_CheckStringInFile(fstab_path, "virtio"):
        os.makedirs(os.path.join(os.sep, "mnt", "sf_mnt"), 0o777, exist_ok=True)
        os.makedirs(os.path.join(os.sep, "mnt", "sf_home"), 0o777, exist_ok=True)
        CFunc.Fstab_AddLine(fstab_path, fstab_mnt_text)
        CFunc.Fstab_AddLine(fstab_path, fstab_home_text)
