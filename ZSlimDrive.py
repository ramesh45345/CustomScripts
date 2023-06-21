#!/usr/bin/env python3
"""Format and mount a block device."""

# Python includes.
import argparse
import os
import sys
import subprocess
import stat
import time
# Custom includes
import CFunc

# Globals
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Automatically create partition scheme for VMs.')
parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
parser.add_argument("-f", "--filesystem", help='Filesystem (i.e, ext4, btrfs, xfs...)', default="ext4")
parser.add_argument("-b", "--blockdevice", help='Block Device to use')
parser.add_argument("-g", "--gpt", help='Use GPT partitioning for EFI', action="store_true")
parser.add_argument("-p", "--pathtomount", help='Path to mount partitions', default="/mnt")
parser.add_argument("-k", "--keep", help='Keep existing partitions (do not format)', action="store_true")

# Save arguments.
args = parser.parse_args()
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
blocksize_string = subprocess.run('blockdev --getsize64 {0}'.format(devicetopartition), shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True)
blocksize = int(blocksize_string.stdout.strip())
blocksizeMB = int(blocksize / 1000000)
print("Size of Block Device: {0} MB".format(blocksizeMB))

# Exit if not root.
CFunc.is_root(True)

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
    subprocess.run('dd if=/dev/zero of="{0}" bs=1M count=4 conv=notrunc'.format(devicetopartition), shell=True, check=True)
    # Set up drive as gpt if true.
    if args.gpt is True:
        subprocess.run('parted -s -a optimal "{0}" -- mktable gpt'.format(devicetopartition), shell=True, check=True)
    else:
        subprocess.run('parted -s -a optimal "{0}" -- mktable msdos'.format(devicetopartition), shell=True, check=True)

    # Create partitions
    efisize = 100
    mainsize = blocksizeMB - efisize
    if args.gpt:
        subprocess.run('parted -s -a optimal "{0}" -- mkpart primary ext2 1 {1}'.format(devicetopartition, mainsize), shell=True, check=True)
        subprocess.run('parted -s -a optimal "{0}" -- mkpart primary fat32 {1} 100%'.format(devicetopartition, mainsize), shell=True, check=True)
        # Set the efi partition to be bootable on gpt.
        subprocess.run('parted -s -a optimal "{0}" -- set 2 boot on'.format(devicetopartition), shell=True, check=True)
        # Wait for partitions to exist
        os.sync()
        time.sleep(1)
        # Format EFI partition
        subprocess.run('mkfs.vfat -n efi -F 32 {0}2'.format(devicetopartition), shell=True, check=True)
    else:
        subprocess.run('parted -s -a optimal "{0}" -- mkpart primary ext2 1 100%'.format(devicetopartition), shell=True, check=True)
        # Wait for partitions to exist
        os.sync()
        time.sleep(1)
    # Format main partition
    subprocess.run('mkfs.{0} {1}1'.format(args.filesystem, devicetopartition), shell=True, check=True)
    subprocess.run('fdisk -l {0}'.format(devicetopartition), shell=True, check=True)

# Mount the parititons
subprocess.run('mount {0}1 {1}'.format(devicetopartition, args.pathtomount), shell=True, check=True)
if args.gpt is True:
    os.makedirs("{0}/boot/efi".format(args.pathtomount), exist_ok=True)
    subprocess.run('mount {0}2 {1}/boot/efi'.format(devicetopartition, args.pathtomount), shell=True, check=True)
