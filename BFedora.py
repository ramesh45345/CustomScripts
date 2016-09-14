#!/usr/bin/env python3

# Python includes.
import argparse
import os
import sys
import subprocess
import shutil
import stat

# Globals
SCRIPTDIR=sys.path[0]

# Get arguments
parser = argparse.ArgumentParser(description='Install Fedora into a folder/chroot.')
parser.add_argument("-n", "--noprompt",help='Do not prompt to continue.', action="store_true")
parser.add_argument("-c", "--hostname", dest="hostname", help='Hostname', default="FedoraTest")
parser.add_argument("-u", "--username", dest="username", help='Username', default="user")
parser.add_argument("-f", "--fullname", dest="fullname", help='Full Name', default="User Name")
parser.add_argument("-q", "--password", dest="password", help='Password', default="asdf")
parser.add_argument("-g", "--grub", type=int, dest="grubtype", help='Grub Install Number', default=1)
parser.add_argument("-i", "--grubpartition", dest="grubpartition", help='Grub Custom Parition (if using grub option 4, i.e. /dev/sdb)', default=None)
parser.add_argument("-t", "--type", dest="type", help='Type of release (fedora, centos, etc)', default="fedora")
parser.add_argument("-v", "--version", dest="version", help='Version of Release', default=24)
parser.add_argument("installpath", help='Path of Installation')

# Save arguments.
args = parser.parse_args()
print("Hostname:",args.hostname)
print("Username:",args.username)
print("Full Name:",args.fullname)
print("Grub Install Number:",args.grubtype)
print("Path of Installation:",args.installpath)
print("Type of release:",args.type)
print("Version of Release:",args.version)
DEVPART = subprocess.run('sh -c df -m | grep " \+'+args.installpath+'$" | grep -Eo "/dev/[a-z]d[a-z]"', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
grubautopart = format(DEVPART.stdout.strip())
print("Autodetect grub partition:",grubautopart)
print("Specified grub partition (if any):",args.grubpartition)

# Exit if not root.
if not os.geteuid() == 0:
    sys.exit("\nError: Please run this script as root.\n")

if args.noprompt == False:
    input("Press Enter to continue.")

subprocess.run("dnf --releasever={0} --installroot={1} --assumeyes install @core".format(args.version, args.installpath), shell=True, check=True)
# Generate fstab
subprocess.run("genfstab -U {0} > {0}/etc/fstab".format(args.installpath), shell=True, check=True)
# Copy resolv.conf into chroot (needed for arch-chroot)
shutil.copy2("/etc/resolv.conf", args.installpath+"/etc/resolv.conf")

# Create and run setup script.
SETUPSCRIPT_PATH = args.installpath+"/setupscript.sh"
SETUPSCRIPT_VAR = open(SETUPSCRIPT_PATH, mode='w')
SETUPSCRIPT_VAR.write("""
#!/bin/bash

# Variables

PY_HOSTNAME="{0}"
PY_USERNAME="{1}"
PY_PASSWORD="{2}"
PY_FULLNAME="{3}"

echo "Running Fedora Setup Script"

# Set hostname
echo "$PY_HOSTNAME" > /etc/hostname
# Set locale
export LANG=en_US.utf8
echo "LANG=en_US.utf8" > /etc/locale.conf
# Set timezone
[ -f /etc/localtime ] && rm -f /etc/localtime
ln -s /usr/share/zoneinfo/America/New_York /etc/localtime

# Install more packages
dnf install -y @fonts @base-x @networkmanager-submodules avahi
dnf install -y util-linux-user nano
# TODO: Move this to fedora software later
dnf install -y @workstation-product @gnome-desktop

# Unlocking root account
passwd -u root
chpasswd <<<"root:$PY_PASSWORD"
# Disable selinux
sed -i 's/SELINUX=.*/SELINUX=permissive/g' /etc/selinux/config
# Setup new user.
useradd -m -g users -G wheel -s /bin/bash $PY_USERNAME
chfn -f "$PY_FULLNAME" $PY_USERNAME
chpasswd <<<"$PY_USERNAME:$PY_PASSWORD"

# Clone csrepo
dnf install -y git
git clone "https://github.com/vinadoros/CustomScripts.git" "/opt/CustomScripts"
chmod a+rwx "/opt/CustomScripts"

# Process Grub Options
""".format(args.hostname, args.username, args.password, args.fullname))

# Install kernel, grub.
if 2 <= args.grubtype <= 4:
    SETUPSCRIPT_VAR.write("""
# Install kernel and grub
dnf install -y kernel kernel-modules kernel-modules-extra @hardware-support grub2 grub2-efi efibootmgr
# Create grub config
grub2-mkconfig -o /boot/grub2/grub.cfg
    """)

# Grub install selection statement.
# Use autodetected grub partition.
if args.grubtype == 1:
    print("Not installing grub.")
elif args.grubtype == 2:
    # Add if variable is a block device
    if stat.S_ISBLK(os.stat(grubautopart).st_mode) == True:
        SETUPSCRIPT_VAR.write('\ngrub2-install --target=i386-pc --recheck --debug {0}'.format(grubautopart))
    else:
        print("ERROR Grub Mode 2, partition {0} is not a block device.".format(grubautopart))
# Use efi partitioning
elif args.grubtype == 3:
    SETUPSCRIPT_VAR.write('\ngrub2-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=fedora --recheck --debug')
# Use pre-selected partition.
elif args.grubtype == 4:
    # Add if variable is a block device
    if stat.S_ISBLK(os.stat(args.grubpartition).st_mode) == True:
        SETUPSCRIPT_VAR.write('\ngrub2-install --target=i386-pc --recheck --debug {0}'.format(args.grubpartition))
    else:
        print("ERROR Grub Mode 4, partition {0} is not a block device.".format(args.grubpartition))

# Close and run the script.
SETUPSCRIPT_VAR.close()
os.chmod(SETUPSCRIPT_PATH, 0o777)
subprocess.run("arch-chroot {0} /setupscript.sh".format(args.installpath), shell=True)
# Remove after running
os.remove(SETUPSCRIPT_PATH)
print("Script finished successfully.")
