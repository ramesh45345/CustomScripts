#!/usr/bin/env python3
"""Format and mount a block device."""

# Python includes.
import argparse
import functools
import os
import sys
import subprocess
import stat
import time
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Globals
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Automatically create partition scheme for VMs.')
parser.add_argument("-b", "--btrfs", help="Format with btrfs, with default subvolumes.", action="store_true")
parser.add_argument("-d", "--blockdevice", help='Block Device to use')
parser.add_argument("-f", "--filesystem", help='Filesystem (i.e, ext4, btrfs, xfs...)', default="ext4")
parser.add_argument("-g", "--gpt", help='Use GPT partitioning for EFI', action="store_true")
parser.add_argument("-k", "--keep", help='Keep existing partitions (do not format)', action="store_true")
parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
parser.add_argument("-p", "--pathtomount", help='Path to mount partitions', default="/mnt")

# Save arguments.
args = parser.parse_args()

# Exit if not root.
CFunc.is_root(True)

# Process arguments.
if args.btrfs:
    args.filesystem = "btrfs"
print("Filesystem:", args.filesystem)
print("User-specified Block Device (if any):", args.blockdevice)
if args.blockdevice is not None and os.path.exists(args.blockdevice) is True and stat.S_ISBLK(os.stat(args.blockdevice).st_mode) is True:
    devicetopartition = args.blockdevice
elif os.path.exists("/dev/sda") is True and stat.S_ISBLK(os.stat("/dev/sda").st_mode) is True:
    devicetopartition = "/dev/sda"
elif os.path.exists("/dev/vda") is True and stat.S_ISBLK(os.stat("/dev/vda").st_mode) is True:
    devicetopartition = "/dev/vda"
else:
    sys.exit("\nError, no block device detected. Please specify one.")
print("Block Device to use:", devicetopartition)
blocksize_string = subprocess.run(f'blockdev --getsize64 {devicetopartition}', shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)
blocksize = int(blocksize_string.stdout.strip())
blocksizeMB = int(blocksize / 1000000)
print(f"Size of Block Device: {blocksizeMB} MB")

if args.noprompt is False:
    input("Press Enter to continue.")

# Unmount any mounted partitions.
os.sync()
subprocess.run("""
swapoff -a
# Unmount each partition
for v_partition in $(parted -s "{0}" print|awk '/^ / {{print $1}}')
do
    echo "Unmounting {0}$v_partition"
    umount "{0}$v_partition"
    umount -l "{0}$v_partition"
    umount -f "{0}$v_partition"
done
""".format(devicetopartition), shell=True, check=False)
os.sync()

if args.keep is False:
    # Remove each partition
    REMOVESCRIPT = """
for v_partition in $(parted -s "{0}" print|awk '/^ / {{print $1}}')
do
   parted -s -a minimal "{0}" rm $v_partition
done
    """.format(devicetopartition)
    subprocess.run(REMOVESCRIPT, shell=True, check=False)

    # Zero out first few mb of drive.
    subprocess.run(f'dd if=/dev/zero of="{devicetopartition}" bs=1M count=4 conv=notrunc', shell=True, check=True)
    # Set up drive as gpt if true.
    if args.gpt is True:
        subprocess.run(f'parted -s -a optimal "{devicetopartition}" -- mktable gpt', shell=True, check=True)
    else:
        subprocess.run(f'parted -s -a optimal "{devicetopartition}" -- mktable msdos', shell=True, check=True)

    # Create partitions
    efisize = 100
    mainsize = blocksizeMB - efisize
    if args.gpt:
        subprocess.run(f'parted -s -a optimal "{devicetopartition}" -- mkpart primary ext2 1 {mainsize}', shell=True, check=True)
        subprocess.run(f'parted -s -a optimal "{devicetopartition}" -- mkpart primary fat32 {mainsize} 100%', shell=True, check=True)
        # Set the efi partition to be bootable on gpt.
        subprocess.run(f'parted -s -a optimal "{devicetopartition}" -- set 2 boot on', shell=True, check=True)
        # Wait for partitions to exist
        os.sync()
        time.sleep(1)
        # Format EFI partition
        subprocess.run(f'mkfs.vfat -n efi -F 32 {devicetopartition}2', shell=True, check=True)
    else:
        subprocess.run(f'parted -s -a optimal "{devicetopartition}" -- mkpart primary ext2 1 100%', shell=True, check=True)
        # Wait for partitions to exist
        os.sync()
        time.sleep(1)
    # Format main partition
    subprocess.run(f'mkfs.{args.filesystem} {devicetopartition}1', shell=True, check=True)
    if args.btrfs or args.filesystem == "btrfs":
        subprocess.run(f'mount {devicetopartition}1 {args.pathtomount}', shell=True, check=True)
        # Create subvolumes in mounted root
        subprocess.run(f'btrfs subvolume create {args.pathtomount}/root', shell=True, check=True)
        subprocess.run(f'btrfs subvolume create {args.pathtomount}/home', shell=True, check=True)
        subprocess.run(f'btrfs subvolume create {args.pathtomount}/var', shell=True, check=True)
        # Set default subvolume
        subprocess.run(f'btrfs subvolume set-default {args.pathtomount}/root', shell=True, check=True)
        # Unmount.
        subprocess.run(f'umount -f {devicetopartition}1 ; umount -l {devicetopartition}1 ; sleep 1', shell=True, check=False)
    subprocess.run(f'fdisk -l {devicetopartition}', shell=True, check=True)

# Mount the parititons
subprocess.run(f'mount {devicetopartition}1 {args.pathtomount}', shell=True, check=True)
if args.btrfs or args.filesystem == "btrfs":
    subprocess.run(f'mkdir {args.pathtomount}/home ; mount -o subvol=/home,compress=zstd:1 {devicetopartition}1 {args.pathtomount}/home', shell=True, check=True)
    subprocess.run(f'mkdir {args.pathtomount}/var ; mount -o subvol=/var,compress=zstd:1 {devicetopartition}1 {args.pathtomount}/var', shell=True, check=True)
if args.gpt is True:
    os.makedirs(f"{args.pathtomount}/boot/efi", exist_ok=True)
    subprocess.run(f'mount {devicetopartition}2 {args.pathtomount}/boot/efi', shell=True, check=True)
