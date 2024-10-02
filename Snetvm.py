#!/usr/bin/env python3
"""List IP addressess of all detected VMs"""

# Python includes.
import os
import shutil
import subprocess

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

### Functions ###
def subpout(cmd):
    """Get output from subprocess"""
    output = subprocess.run("{0}".format(cmd), shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
    return output


### Virtualbox Section ###
if shutil.which("VBoxManage"):
    vboxvms = subpout("VBoxManage list runningvms").splitlines()
    for vboxvm in vboxvms:
        # Split at quotations to get VM names
        vboxvm = vboxvm.split('"')
        if vboxvm is not None and len(vboxvm) > 1:
            print("\nIPs for VirtualBox VM {0}.".format(vboxvm[1]))
            subprocess.run('VBoxManage guestproperty enumerate "{0}" | grep IP'.format(vboxvm[1]), shell=True)
else:
    print("VBoxManage utility not found. Skipping VirtualBox networks.")


### libvirt section ###
if shutil.which("virsh"):
    virtnetworks = subpout("virsh --connect qemu:///system net-list --all --name").splitlines()
    for virtnet in virtnetworks:
        if virtnet is not None:
            print("\nIPs for libvirt network", virtnet)
            subprocess.run("virsh --connect qemu:///system net-dhcp-leases {0}".format(virtnet), shell=True)
else:
    print("virsh utility not found. Skipping libvirt networks.")
