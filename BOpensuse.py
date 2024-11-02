#!/usr/bin/env python3
"""Install Opensuse Tumbleweed."""

# Python includes.
import argparse
import functools
import os
import sys
import subprocess
import stat
# Custom Includes
from passlib import hash
import zch

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

### Functions ###
def zypper_install_chroot(chroot_folder: str, packages: str):
    """Install zypper packages in chroot."""
    zch.ChrootCommand(chroot_folder, "zypper install -y {0}".format(packages))
    return


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Install Arch into a folder/chroot.')
    parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
    parser.add_argument("-c", "--hostname", help='Hostname', default="OpensuseTest")
    parser.add_argument("-u", "--username", help='Username', default="user")
    parser.add_argument("-f", "--fullname", help='Full Name', default="User Name")
    parser.add_argument("-q", "--password", help='Password', default="asdf")
    parser.add_argument("-g", "--grubtype", type=int, help='Grub Install Number', default=3)
    parser.add_argument("-i", "--grubpartition", help='Grub Custom Parition (if autodetection isnt working, i.e. /dev/sdb)', default=None)
    parser.add_argument("installpath", help='Path of Installation')

    # Save arguments.
    args = parser.parse_args()
    print("Hostname:", args.hostname)
    print("Username:", args.username)
    print("Full Name:", args.fullname)
    print("Grub Install Number:", args.grubtype)
    # Get absolute path of the given path.
    absinstallpath = os.path.realpath(args.installpath)
    print("Path of Installation:", absinstallpath)
    DEVPART = subprocess.run('sh -c df -m | grep " \+' + absinstallpath + '$" | grep -Eo "/dev/[a-z]d[a-z]"', shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    grubautopart = format(DEVPART.stdout.strip())
    print("Autodetect grub partition:", grubautopart)
    if args.grubpartition is not None and stat.S_ISBLK(os.stat(args.grubpartition).st_mode) is True:
        grubpart = args.grubpartition
    else:
        grubpart = grubautopart
    print("Grub partition to be used:", grubpart)

    # Exit if not root.
    if os.geteuid() != 0:
        sys.exit("\nError: Please run this script as root.\n")

    if args.noprompt is False:
        input("Press Enter to continue.")

    # zypper root commands
    subprocess.run(f"zypper --root {absinstallpath} addrepo -f https://download.opensuse.org/tumbleweed/repo/oss/ tw-oss", shell=True, check=True)
    subprocess.run(f"zypper --root {absinstallpath} addrepo -f https://download.opensuse.org/tumbleweed/repo/non-oss/ tw-nonoss", shell=True, check=True)
    subprocess.run(f"zypper --root {absinstallpath} --gpg-auto-import-keys ref", shell=True, check=True)
    subprocess.run(f"zypper --root {absinstallpath} install -y sysuser-shadow", shell=True, check=True)
    subprocess.run(f"zypper --root {absinstallpath} install -y patterns-base-enhanced_base patterns-base-bootloader", shell=True, check=True)

    # Import gpg key for repos
    zch.ChrootCommand(absinstallpath, "rpm --import https://download.opensuse.org/tumbleweed/repo/oss/gpg-pubkey-29b700a4-62b07e22.asc")
    # Install kernel and initram
    zypper_install_chroot(absinstallpath, "kernel-default kernel-firmware grub2-branding-openSUSE")
    zch.ChrootCommand(absinstallpath, "dracut --regenerate-all")

    # Generate hashed password
    sha512_password = hash.sha512_crypt.hash(args.password, rounds=5000)
    # Set root password
    subprocess.run(f"""echo 'root:{sha512_password}' | chpasswd -R {absinstallpath} -e""", shell=True, check=True)
    # Setup normal user
    zch.ChrootCommand(absinstallpath, f"useradd -u 1000 -m -g users -G wheel -s /bin/bash {args.username}")
    zch.ChrootCommand(absinstallpath, f'chfn -f "{args.fullname}" {args.username}')
    subprocess.run(f"""echo '{args.username}:{sha512_password}' | chpasswd -R {absinstallpath} -e""", shell=True, check=True)

    # Enable ssh and network-manager
    zypper_install_chroot(absinstallpath, "openssh-server openssh-server-config-rootlogin")
    zch.ChrootCommand(absinstallpath, "systemctl enable sshd NetworkManager")

    # Grub install selection statement.
    if args.grubtype == 1:
        print("Not installing grub.")
    else:
        # Create fstab for other grub scenarios
        subprocess.run(f"genfstab -U {absinstallpath} > {absinstallpath}/etc/fstab", shell=True)
        subprocess.run(f"sed -i '/zram0/d' {absinstallpath}/etc/fstab", shell=True)
        # Install grub config
        zch.ChrootCommand(absinstallpath, "grub2-mkconfig -o /boot/grub2/grub.cfg")
    # Use autodetected or specified grub partition.
    if args.grubtype == 2:
        # Add if partition is a block device
        if stat.S_ISBLK(os.stat(grubpart).st_mode) is True:
            zch.ChrootCommand(absinstallpath, f"grub2-install --target=i386-pc --recheck {grubpart}")
        else:
            print(f"ERROR Grub Mode 2, partition {grubpart} is not a block device.")
    # Use efi partitioning
    elif args.grubtype == 3:
        # Add if /boot/efi is mounted, and partition is a block device.
        if os.path.ismount(os.path.join(absinstallpath, "boot", "efi")) is True and stat.S_ISBLK(os.stat(grubpart).st_mode) is True:
            zch.ChrootCommand(absinstallpath, "grub2-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=opensuse --recheck")
        else:
            print(f"ERROR Grub Mode 3, {absinstallpath}/boot/efi isn't a mount point or {grubpart} is not a block device.")
