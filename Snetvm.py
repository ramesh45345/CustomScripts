#!/usr/bin/env python3
"""List IP addressess of all detected VMs"""

# Python includes.
import argparse
import shutil
import subprocess
# Custom includes
import CFunc


### Functions ###
def libvirt_virtnetworks():
    """Find all networks in libvirt"""
    virtnetworks = CFunc.subpout("virsh --connect qemu:///system net-list --all --name").splitlines()
    return virtnetworks
def libvirt_mactable(hostname: str):
    """Return array containing all mac addresses for a given VM."""
    macaddress_fields = CFunc.subpout(f"virsh -q domiflist {hostname}", error_on_fail=False)
    # Create a 2D list containing the mac information.
    # 0: Interface, 1: Type, 2: Source, 3: Model, 4: MAC
    macarray = []
    for mac_lines in macaddress_fields.split("\n"):
        macarray += [mac_lines.split()]
    return macarray
def libvirt_ipv4(hostname: str):
    """
    Return an ipv4 address for a given VM name.
    Inspired by https://github.com/earlruby/create-vm/blob/main/get-vm-ip
    The shell version of this function:
        HOSTNAME=U1 ; MAC=$(virsh -q domiflist $HOSTNAME | awk '{ print $5 }') ; virsh --connect qemu:///system net-dhcp-leases default "$MAC" | grep -i ipv4 | awk '{ print $5 }' | sed 's@/.*$@@g'
    """
    # Get the MAC for the last interface that has a type of "bridge". Its also possible to filter by the source being "virbr0".
    macaddress = None
    for mac_line in libvirt_mactable(hostname):
        if mac_line[1] == "bridge":
            macaddress = mac_line[4]
    lease_line_found = None
    # Try to find the ip in every available network.
    for virtnet in libvirt_virtnetworks():
        if virtnet is not None:
            # Get the lines containing the leases for the given network. Keep the \n, since we will split the lines by them and loop over those lines.
            lease_lines_all = subprocess.run(f'virsh --connect qemu:///system net-dhcp-leases {virtnet} --mac "{macaddress}"', stdout=subprocess.PIPE, universal_newlines=False, shell=True).stdout
            for lease_line in lease_lines_all.decode('ascii').split('\n'):
                # After looping through every network, if we find the ipv4 line, store the last one we found.
                if (lease_line != "" or not None) and "ipv4" in lease_line.lower():
                    lease_line_found = lease_line
    ipv4_addr = None
    if lease_line_found is not None:
        # Instead of using awk, split against spaces, and split the IP address again to remove everything after the /.
        lease_line_processed = lease_line_found.split()
        ipv4_addr = lease_line_processed[4].split("/")[0]
    return ipv4_addr


if __name__ == '__main__':

    # Get arguments
    parser = argparse.ArgumentParser(description='List IP addressess of VMs')
    parser.add_argument("-v", "--vmname", help='Get the ipv4 address of a libvirt VM (case sensitive and exact name)')
    args = parser.parse_args()

    if args.vmname:
        print(libvirt_ipv4(args.vmname))
    else:
        ### Virtualbox Section ###
        if shutil.which("VBoxManage"):
            vboxvms = CFunc.subpout("VBoxManage list runningvms").splitlines()
            for vboxvm in vboxvms:
                # Split at quotations to get VM names
                vboxvm = vboxvm.split('"')
                if vboxvm is not None and len(vboxvm) > 1:
                    print("\nIPs for VirtualBox VM {0}.".format(vboxvm[1]))
                    subprocess.run('VBoxManage guestproperty enumerate "{0}" | grep IP'.format(vboxvm[1]), shell=True)

        ### libvirt section ###
        if shutil.which("virsh"):
            virtnetworks = libvirt_virtnetworks()
            for virtnet in virtnetworks:
                if virtnet is not None:
                    print("\nIPs for libvirt network", virtnet)
                    subprocess.run("virsh --connect qemu:///system net-dhcp-leases {0}".format(virtnet), shell=True)
