#!/bin/sh

# Set dconf info for virt-manager
dconf write /org/virt-manager/virt-manager/stats/enable-cpu-poll true
dconf write /org/virt-manager/virt-manager/stats/enable-disk-poll true
dconf write /org/virt-manager/virt-manager/stats/enable-memory-poll true
dconf write /org/virt-manager/virt-manager/stats/enable-net-poll true
dconf write /org/virt-manager/virt-manager/vmlist-fields/cpu-usage true
dconf write /org/virt-manager/virt-manager/vmlist-fields/disk-usage false
dconf write /org/virt-manager/virt-manager/vmlist-fields/memory-usage true
dconf write /org/virt-manager/virt-manager/vmlist-fields/network-traffic true
dconf write /org/virt-manager/virt-manager/console/resize-guest 1
dconf write /org/virt-manager/virt-manager/enable-libguestfs-vm-inspection true
dconf write /org/virt-manager/virt-manager/xmleditor-enabled true