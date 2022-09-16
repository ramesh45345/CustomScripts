#!/usr/bin/env python3
"""Install Arch."""

# Python includes.
import argparse
import os
import sys
import subprocess
import stat
# Custom Includes
import CFunc
import zch

# Folder of this script
SCRIPTDIR = sys.path[0]

### Functions ###
def pacman_install_chroot(chroot_folder: str, packages: str):
    """Install pacman packages in chroot."""
    zch.ChrootCommand(chroot_folder, "pacman -Syu --noconfirm --needed {0}".format(packages))
    return
def ctr_create(path: str, cmd: str):
    """Run a chroot create command using a container runtime."""
    full_cmd = ["podman", "run", "--rm", "--privileged", "--pull=always", "-it", "--volume={0}:/chrootfld".format(path), "--name=chrootsetup", "docker.io/library/archlinux:latest", "bash", "-c", cmd]
    print("Running {0}".format(full_cmd))
    subprocess.run(full_cmd, check=True)


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Install Arch into a folder/chroot.')
    parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
    parser.add_argument("-c", "--hostname", help='Hostname', default="ArchTest")
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

    if args.noprompt == False:
        input("Press Enter to continue.")

    # Bootstrap the chroot environment.
    ctr_create(absinstallpath, "sed -i 's/^#ParallelDownloads/ParallelDownloads/g' /etc/pacman.conf && pacman -Sy --noconfirm --needed arch-install-scripts && pacstrap -c /chrootfld base base-devel && genfstab -U /chrootfld > /chrootfld/etc/fstab && sed -i '/zram0/d' /chrootfld/etc/fstab")

    # Create and run setup script.
    SETUPSCRIPT = '''#!/bin/bash
echo "Running Arch Setup Script"

# Install locales
export LANG=en_US.UTF-8
echo "LANG=en_US.UTF-8" > "/etc/locale.conf"
sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/g' "/etc/locale.gen"
locale-gen

# Set hostname
sed -i 's/\(127.0.0.1\\tlocalhost.localdomain\\tlocalhost\)\(.*\)/\\1 '{HOSTNAME}'/g' "/etc/hosts"
echo "{HOSTNAME}" > /etc/hostname

# Set timezone
[ -f /etc/localtime ] && rm -f /etc/localtime
ln -s /usr/share/zoneinfo/US/Eastern /etc/localtime

# Set root password
chpasswd <<<"root:{PASSWORD}"
# Setup normal user
if ! grep -i "^{USERNAME}" /etc/passwd; then
    useradd -m -g users -G wheel -s /bin/bash {USERNAME}
    chfn -f "{FULLNAME}" {USERNAME}
fi
chpasswd <<<"{USERNAME}:{PASSWORD}"

# Setup multilib
if [ $(uname -m) == "x86_64" ]; then
    if ! grep -Fxq "[multilib]" /etc/pacman.conf; then
        sh -c "cat >>/etc/pacman.conf" <<'EOL'

[multilib]
Include = /etc/pacman.d/mirrorlist
EOL
    fi
fi

# Update system
pacman -Syu --noconfirm
pacman -S --needed --noconfirm base-devel rsync

# Enable sudo for wheel group.
if grep -iq "# %wheel ALL=(ALL) ALL" /etc/sudoers; then
    sed -i.w 's/# %wheel ALL=(ALL) ALL/%wheel ALL=(ALL) ALL/' /etc/sudoers
fi
visudo -c
if [ -f /etc/sudoers.w ]; then
    rm /etc/sudoers.w
fi

# Network Manager and openssh.
pacman -S --needed --noconfirm wget networkmanager dhclient ntfs-3g gptfdisk dosfstools btrfs-progs xfsprogs f2fs-tools lvm2 openssh
systemctl enable NetworkManager
systemctl enable sshd

#Install xorg, display manger...
pacman -S --needed --noconfirm xorg-server xorg-server-utils xorg-drivers xf86-input-libinput mesa-libgl xorg-xinit xterm mesa mesa-vdpau libva-mesa-driver libva-intel-driver libva-vdpau-driver libva
# Causes crashing in chroots.
#pacman -S --needed --noconfirm libvdpau-va-gl
if [ $(uname -m) == "x86_64" ]; then
    pacman -S --needed --noconfirm lib32-mesa-vdpau
fi

pacman -S --needed --noconfirm network-manager-applet gnome-keyring gnome-icon-theme ipw2200-fw dosfstools system-config-printer alsa-utils

#Install openbox
pacman -S --needed --noconfirm openbox

usermod -aG lp,network,video,audio,storage,scanner,power,disk,sys,games,optical,avahi,uucp,systemd-journal {USERNAME}

# Python
pacman -S --needed --noconfirm python

# Custom Scripts
pacman -S --needed --noconfirm git
git clone "https://github.com/vinadoros/CustomScripts.git" "/opt/CustomScripts"
chmod a+rwx "/opt/CustomScripts"'''.format(HOSTNAME=args.hostname, USERNAME=args.username, PASSWORD=args.password, FULLNAME=args.fullname)

    # Init grub script
    GRUBSCRIPT = """#!/bin/bash
# Grub Script
# Install Linux
pacman -S --needed --noconfirm linux linux-firmware
    """
    # Grub install selection statement.
    if args.grubtype == 1:
        print("Not installing grub.")
    # Use autodetected or specified grub partition.
    elif args.grubtype == 2:
        # Add if partition is a block device
        if stat.S_ISBLK(os.stat(grubpart).st_mode) is True:
            GRUBSCRIPT += """
pacman -S --needed --noconfirm grub os-prober
grub-mkconfig -o /boot/grub/grub.cfg
grub-install --target=i386-pc --recheck --debug {0}
""".format(grubpart)
        else:
            print("ERROR Grub Mode 2, partition {0} is not a block device.".format(grubpart))
    # Use efi partitioning
    elif args.grubtype == 3:
        # Add if /boot/efi is mounted, and partition is a block device.
        if os.path.ismount("{0}/boot/efi".format(absinstallpath)) is True and stat.S_ISBLK(os.stat(grubpart).st_mode) is True:
            GRUBSCRIPT += """
pacman -S --needed --noconfirm efibootmgr os-prober grub
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=arch --recheck
grub-mkconfig -o /boot/grub/grub.cfg
"""
        else:
            print("ERROR Grub Mode 3, {0}/boot/efi isn't a mount point or {0} is not a block device.".format(absinstallpath, grubpart))

    # Close the setup script.
    SETUPSCRIPT_PATH = os.path.join(absinstallpath, "setupscript.sh")
    SETUPSCRIPT_VAR = open(SETUPSCRIPT_PATH, mode='w')
    SETUPSCRIPT_VAR.write(SETUPSCRIPT)
    SETUPSCRIPT_VAR.close()
    os.chmod(SETUPSCRIPT_PATH, 0o777)
    # Close the grub script.
    GRUBSCRIPT_PATH = os.path.join(absinstallpath, "grubscript.sh")
    GRUBSCRIPT_VAR = open(GRUBSCRIPT_PATH, mode='w')
    GRUBSCRIPT_VAR.write(GRUBSCRIPT)
    GRUBSCRIPT_VAR.close()
    os.chmod(GRUBSCRIPT_PATH, 0o777)
    # Run the setup script.
    zch.ChrootCommand(absinstallpath, "/setupscript.sh")
    # Run the grub script.
    zch.ChrootCommand(absinstallpath, "/grubscript.sh")
    # Remove after running
    os.remove(SETUPSCRIPT_PATH)
    os.remove(GRUBSCRIPT_PATH)
    print("Script finished successfully.")
