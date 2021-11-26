#!/usr/bin/env python3
"""Create an Ubuntu live-cd."""

# Python includes.
import argparse
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import signal
import sys
import time
import traceback
# Custom includes
import CFunc
import zch

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]


### Functions ###
def cleanup():
    """Cleanup build folder."""
    if os.path.isdir(rootfsfolder):
        zch.ChrootUnmountPaths(rootfsfolder)
        shutil.rmtree(rootfsfolder)
def signal_handler(sig, frame):
    """Cleanup if given early termination."""
    cleanup()
    print('Exiting due to SIGINT.')
    sys.exit(1)


# Exit if not root.
CFunc.is_root(True)
# Attach signal handler.
signal.signal(signal.SIGINT, signal_handler)

# Get the root user's home folder.
USERHOME = os.path.expanduser("~root")
workfolder_default = os.path.join(USERHOME, "ubulive")

# Get arguments
parser = argparse.ArgumentParser(description='Build LiveCD.')
parser.add_argument("-n", "--noprompt", help='Do not prompt.', action="store_true")
parser.add_argument("-w", "--workfolder", help='Location of Working Folder (default: %(default)s)', default=workfolder_default)
parser.add_argument("-r", "--release", help='Ubuntu Release, default: %(default)s', default="focal")

# Save arguments.
args = parser.parse_args()

# Process variables
buildfolder = os.path.abspath(args.workfolder)
rootfsfolder = os.path.join(buildfolder, "chroot")
print("Using work folder {0}.".format(buildfolder))
print("Ubuntu Release: {0}".format(args.release))

if args.noprompt is False:
    input("Press Enter to continue.")


# Create the work folder
if os.path.isdir(buildfolder):
    print("Work folder {0} already exists.".format(buildfolder))
else:
    print("Creating work folder {0}.".format(buildfolder))
    os.makedirs(buildfolder, 0o777)
# Cleanup before starting.
cleanup()

# Save start time.
beforetime = datetime.now()
# Isoname
currentdatetime = time.strftime("%Y-%m-%d_%H%M")
isoname = "Ubuntu-CustomLive-{0}.iso".format(currentdatetime)

# Initiate logger
buildlog_path = os.path.join(buildfolder, "{0}.log".format(isoname))
CFunc.log_config(buildlog_path)

### Build LiveCD ###
# https://github.com/mvallim/live-custom-ubuntu-from-scratch

CFunc.aptupdate()
CFunc.aptinstall("debootstrap binutils squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools dosfstools unzip")
CFunc.subpout_logger("debootstrap --arch=amd64 --variant=minbase {0} {1}  http://us.archive.ubuntu.com/ubuntu/".format(args.release, rootfsfolder))

# Create chroot script.
with open(os.path.join(rootfsfolder, "chrootscript.sh"), 'w') as f_handle:
    f_handle.write("""#!/bin/bash -e
# Setup
export HOME=/root
export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive
echo "ubuntu-fs-live" > /etc/hostname
apt-get update
# Install systemd
apt-get install -y systemd-sysv
# Configure machine-id and divert
dbus-uuidgen > /etc/machine-id
ln -fs /etc/machine-id /var/lib/dbus/machine-id
dpkg-divert --local --rename --add /sbin/initctl
ln -s /bin/true /sbin/initctl

apt-get install -y --no-install-recommends software-properties-common
add-apt-repository main && add-apt-repository restricted && add-apt-repository universe && add-apt-repository multiverse
apt-get update
# Install locales
apt-get install -y locales
sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
echo 'LANG="en_US.UTF-8"'>/etc/default/locale
locale-gen --purge en_US en_US.UTF-8
dpkg-reconfigure --frontend=noninteractive locales
update-locale
# Locale fix for gnome-terminal.
echo "LANG=en_US.UTF-8" > /etc/locale.conf
# Set keymap for Ubuntu
echo "console-setup	console-setup/charmap47	select	UTF-8" | debconf-set-selections

# Live System software
apt-get install -y \
casper \
lupin-casper \
discover \
laptop-detect \
os-prober \
network-manager \
resolvconf \
net-tools \
wireless-tools \
wpagui \
locales \
linux-generic \
memtest86+

# Install CLI Software
apt-get install -y \
btrfs-progs \
chntpw \
clonezilla \
curl \
debootstrap \
dmraid \
efibootmgr \
exfat-utils \
exfat-fuse \
f2fs-tools \
fonts-powerline \
fsarchiver \
fstransform \
git \
iotop \
less \
lvm2 \
mdadm \
nano \
nfs-common \
rsync \
screen \
ssh \
testdisk \
tilix \
tmux \
whois \
xfsdump \
xfsprogs \
zfsutils-linux \
zsh

# Allow root login from ssh
sed -i '/^#PermitRootLogin.*/s/^#//g' /etc/ssh/sshd_config
sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config

# Hold gnome packages (not needed for MATE desktop)
apt-mark hold gnome-shell gdm3 gnome-session gnome-session-bin ubuntu-session gnome-desktop3-data gnome-control-center cheese

# Install GUI software
apt-get install -y \
avahi-daemon \
avahi-discover \
caja-open-terminal \
firefox \
dconf-cli \
gnome-keyring \
gnome-disk-utility \
gparted \
gvfs \
lightdm \
mate-desktop-environment \
ubuntu-mate-core \
gnome-icon-theme \
network-manager \
network-manager-gnome \
net-tools \
wireless-tools \
xserver-xorg

# Install VM software
apt-get install -y \
dkms \
spice-vdagent \
qemu-guest-agent \
open-vm-tools \
open-vm-tools-desktop \
virtualbox-guest-utils \
virtualbox-guest-dkms \
virtualbox-guest-x11 \
build-essential

# Install pacman
apt install --no-install-recommends -y meson libarchive-dev libssl-dev libgpgme-dev libcurl4-openssl-dev python3-setuptools
cd /root
git clone https://git.archlinux.org/pacman.git/
cd pacman
meson builddir
cd builddir
ninja
ninja install
ldconfig
cd /root
rm -rf /root/pacman
apt install --no-install-recommends -y asciidoc m4 xsltproc
git clone https://git.archlinux.org/arch-install-scripts.git
cd arch-install-scripts
make
make install
sudo apt remove -y --purge asciidoc m4 xsltproc meson libarchive-dev libssl-dev libgpgme-dev libcurl4-openssl-dev python3-setuptools
cd /root
rm -rf /root/arch-install-scripts
mkdir -p /etc/pacman.d/

cat <<EOF > /etc/NetworkManager/NetworkManager.conf
[main]
rc-manager=resolvconf
plugins=ifupdown,keyfile
dns=dnsmasq

[ifupdown]
managed=false
EOF
dpkg-reconfigure network-manager
dpkg-reconfigure --frontend=noninteractive resolvconf

passwd -u root
chpasswd <<<"root:asdf"

[ ! -d /opt/CustomScripts ] && git clone https://github.com/ramesh45345/CustomScripts /opt/CustomScripts
[ -d /opt/CustomScripts ] && cd /opt/CustomScripts && git pull

# Create liveuser ahead of when it will really be created
useradd -m ubuntu

# Shell Configuration
/opt/CustomScripts/CShellConfig.py -z -d -u ubuntu

# Sudoers configuration
/opt/CustomScripts/CFuncExt.py -s

# Mate Configuration
/opt/CustomScripts/DExtMate.py

# Update CustomScripts on startup
cat >"/etc/systemd/system/updatecs.service" <<'EOL'
[Unit]
Description=updatecs service
Requires=network-online.target
After=network.target nss-lookup.target network-online.target

[Service]
Type=simple
ExecStart=/bin/bash -c "cd /opt/CustomScripts; git pull"
Restart=on-failure
RestartSec=3s
TimeoutStopSec=7s

[Install]
WantedBy=graphical.target
EOL
systemctl enable updatecs.service

# Dset
cat >"/etc/xdg/autostart/dset.desktop" <<"EOL"
[Desktop Entry]
Name=Dset
Exec=/opt/CustomScripts/Dset.py -p
Terminal=false
Type=Application
EOL

# Autoset resolution
cat >"/etc/xdg/autostart/ra.desktop" <<"EOL"
[Desktop Entry]
Name=Autoresize Resolution
Exec=/usr/local/bin/ra.sh
Terminal=false
Type=Application
EOL
cat >"/usr/local/bin/ra.sh" <<'EOL'
#!/bin/bash
while true; do
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
done
EOL
chmod a+rwx /usr/local/bin/ra.sh

# Set computer to not sleep on lid close
if ! grep -Fxq "HandleLidSwitch=lock" /etc/systemd/logind.conf; then
    echo 'HandleLidSwitch=lock' >> /etc/systemd/logind.conf
fi

# Casper script
cat <<'EOLXYZ' >/usr/share/initramfs-tools/scripts/casper-bottom/99custom
#!/bin/sh

PREREQ=""
DESCRIPTION="Disabling unity8's first run wizard..."

prereqs()
{
       echo "$PREREQ"
}

case $1 in
# get pre-requisites
prereqs)
       prereqs
       exit 0
       ;;
esac

. /scripts/casper-functions

log_begin_msg "$DESCRIPTION"

# Add CustomScripts to path
SCRIPTBASENAME="/opt/CustomScripts"
if ! grep "$SCRIPTBASENAME" /root/.bashrc; then
    cat >>/root/.bashrc <<EOLBASH

if [ -d $SCRIPTBASENAME ]; then
    export PATH=\$PATH:$SCRIPTBASENAME
fi
EOLBASH
fi
if ! grep "$SCRIPTBASENAME" /root/home/$USERNAME/.bashrc; then
    cat >>/root/home/$USERNAME/.bashrc <<EOLBASH

if [ -d $SCRIPTBASENAME ]; then
    export PATH=\$PATH:$SCRIPTBASENAME:/sbin:/usr/sbin
fi
EOLBASH
fi

log_end_msg
EOLXYZ
chmod 755 /usr/share/initramfs-tools/scripts/casper-bottom/99custom


# Final initram generation
update-initramfs -c -k all

# Clean environment
apt-get purge -y locales
apt-get clean
# From https://git.launchpad.net/livecd-rootfs/tree/live-build/ubuntu-core/hooks/10-remove-documentation.binary
echo "I: Remove unneeded files from /usr/share/doc "
find /usr/share/doc -depth -type f ! -name copyright|xargs rm -f || true
find /usr/share/doc -empty|xargs rmdir || true
find /usr/share/doc -type f -exec gzip -9 {} \;

echo "I: Remove man/info pages"
rm -rf /usr/share/man \
       /usr/share/groff \
       /usr/share/info \
       /usr/share/lintian \
       /usr/share/linda \
       /var/cache/man

echo "I: Removing /var/lib/apt/lists/*"
find /var/lib/apt/lists/ -type f | xargs rm -f

echo "I: Removing /var/cache/apt/*.bin"
rm -f /var/cache/apt/*.bin

# Cleanup the chroot environment
truncate -s 0 /etc/machine-id
rm /sbin/initctl
dpkg-divert --rename --remove /sbin/initctl
rm -rf /tmp/* ~/.bash_history
export HISTSIZE=0
""")
os.chmod(os.path.join(rootfsfolder, "chrootscript.sh"), 0o777)

# Commands to run inside chroot
try:
    # Run the script in the chroot.
    zch.ChrootCommand(rootfsfolder, os.path.join(os.sep, "chrootscript.sh"))
    os.remove(os.path.join(rootfsfolder, "chrootscript.sh"))
except Exception:
    logging.error("ERROR: Chroot command failed.")
    logging.error(traceback.format_exc())
    # Unmount the chroot filesystems upon error.
    zch.ChrootUnmountPaths(rootfsfolder)
    sys.exit()


# Create the CD image directory and populate it
os.chdir(buildfolder)
os.makedirs(os.path.join(buildfolder, "image", "casper"), exist_ok=True)
os.makedirs(os.path.join(buildfolder, "image", "isolinux"), exist_ok=True)
os.makedirs(os.path.join(buildfolder, "image", "install"), exist_ok=True)
CFunc.subpout_logger("cp {0}/chroot/boot/vmlinuz-**-**-generic {0}/image/casper/vmlinuz".format(buildfolder))
CFunc.subpout_logger("cp {0}/chroot/boot/initrd.img-**-**-generic {0}/image/casper/initrd".format(buildfolder))
CFunc.subpout_logger("cp {0}/chroot/boot/memtest86+.bin {0}/image/install/memtest86+".format(buildfolder))
CFunc.subpout_logger("wget --progress=dot https://www.memtest86.com/downloads/memtest86-usb.zip -O {0}/image/install/memtest86-usb.zip".format(buildfolder))
CFunc.subpout_logger("unzip -p {0}/image/install/memtest86-usb.zip memtest86-usb.img > {0}/image/install/memtest86".format(buildfolder))
os.remove(os.path.join(buildfolder, "image", "install", "memtest86-usb.zip"))

# Grub configuration
iso_label = "Ubuntu-{0}".format(currentdatetime)
debcustom_path = Path(os.path.join(buildfolder, "image", "ubuntu"))
debcustom_path.touch(exist_ok=True)
with open(os.path.join(buildfolder, "image", "isolinux", "grub.cfg"), 'w') as f:
    f.write("""search --set=root --file /ubuntu

insmod all_video

set default="0"
set timeout=1

menuentry "Load Ubuntu" {
   linux /casper/vmlinuz boot=casper fsck.mode=skip noprompt quiet splash ---
   initrd /casper/initrd
}

menuentry "Check disc for defects" {
   linux /casper/vmlinuz boot=casper quiet splash ---
   initrd /casper/initrd
}

menuentry "Test memory Memtest86+ (BIOS)" {
   linux16 /install/memtest86+
}

menuentry "Test memory Memtest86 (UEFI, long load time)" {
   insmod part_gpt
   insmod search_fs_uuid
   insmod chain
   loopback loop /install/memtest86
   chainloader (loop,gpt1)/efi/boot/BOOTX64.efi
}
""")

# Create manifest
CFunc.subpout_logger("chroot chroot dpkg-query -W --showformat='${Package} ${Version}\n' | tee image/casper/filesystem.manifest")
CFunc.subpout_logger("cp -v image/casper/filesystem.manifest image/casper/filesystem.manifest-desktop")
CFunc.subpout_logger("sed -i '/ubiquity/d' image/casper/filesystem.manifest-desktop")
CFunc.subpout_logger("sed -i '/casper/d' image/casper/filesystem.manifest-desktop")
CFunc.subpout_logger("sed -i '/discover/d' image/casper/filesystem.manifest-desktop")
CFunc.subpout_logger("sed -i '/laptop-detect/d' image/casper/filesystem.manifest-desktop")
CFunc.subpout_logger("sed -i '/os-prober/d' image/casper/filesystem.manifest-desktop")

# Compress the chroot
# Create squashfs
CFunc.subpout_logger("mksquashfs chroot {0}/image/casper/filesystem.squashfs -noappend".format(buildfolder))
# Write the filesystem.size
with open(os.path.join(buildfolder, "image", "casper", "filesystem.size"), 'w') as f:
    f.write(CFunc.subpout('du -sx --block-size=1 "{0}" | cut -f1'.format(os.path.join(buildfolder, "chroot"))))

# Create diskdefines
with open(os.path.join(buildfolder, "image", "README.diskdefines"), 'w') as f:
    f.write("""#define DISKNAME  Ubuntu from scratch
#define TYPE  binary
#define TYPEbinary  1
#define ARCH  amd64
#define ARCHamd64  1
#define DISKNUM  1
#define DISKNUM1  1
#define TOTALNUM  0
#define TOTALNUM0  1""")

# Begin ISO creation
os.chdir(os.path.join(buildfolder, "image"))
# Create grub UEFI image
CFunc.subpout_logger('''grub-mkstandalone \
    --format=x86_64-efi \
    --output=isolinux/bootx64.efi \
    --locales="" \
    --fonts="" \
    "boot/grub/grub.cfg=isolinux/grub.cfg"''')
# Create a FAT16 UEFI boot disk image containing the EFI bootloader
CFunc.subpout_logger("""(
    cd isolinux && \
    dd if=/dev/zero of=efiboot.img bs=1M count=10 && \
    mkfs.vfat efiboot.img && \
    LC_CTYPE=C mmd -i efiboot.img efi efi/boot && \
    LC_CTYPE=C mcopy -i efiboot.img ./bootx64.efi ::efi/boot/
)""")
# Create a grub BIOS image
os.chdir(os.path.join(buildfolder, "image"))
CFunc.subpout_logger('''grub-mkstandalone \
    --format=i386-pc \
    --output=isolinux/core.img \
    --install-modules="linux16 linux normal iso9660 biosdisk memdisk search tar ls" \
    --modules="linux16 linux normal iso9660 biosdisk search" \
    --locales="" \
    --fonts="" \
    "boot/grub/grub.cfg=isolinux/grub.cfg"''')
# Combine a bootable Grub cdboot.img
CFunc.subpout_logger("cat /usr/lib/grub/i386-pc/cdboot.img {0}/image/isolinux/core.img > {0}/image/isolinux/bios.img".format(buildfolder))
# Generate md5sum.txt
with open(os.path.join(buildfolder, "image", "md5sum.txt"), 'w') as f:
    f.write(CFunc.subpout('find . -type f -print0 | xargs -0 md5sum | grep -v "./md5sum.txt"'))
# Create iso from the image directory using the command-line
CFunc.subpout_logger("""xorriso \
    -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "{2}" \
    -eltorito-boot boot/grub/bios.img \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    --eltorito-catalog boot/grub/boot.cat \
    --grub2-boot-info \
    --grub2-mbr /usr/lib/grub/i386-pc/boot_hybrid.img \
    -eltorito-alt-boot \
    -e EFI/efiboot.img \
    -no-emul-boot \
    -append_partition 2 0xef isolinux/efiboot.img \
    -output "{0}/{1}" \
    -graft-points \
        "." \
        /boot/grub/bios.img=isolinux/bios.img \
        /EFI/efiboot.img=isolinux/efiboot.img""".format(buildfolder, isoname, iso_label))
# Set permissions of iso and log
os.chmod(os.path.join(buildfolder, isoname), 0o777)
os.chmod(os.path.join(buildlog_path), 0o777)

if os.path.isfile(os.path.join(buildfolder, isoname)):
    print('Run to test: "qemu-system-x86_64 -enable-kvm -m 2048 {0}"'.format(os.path.join(buildfolder, isoname)))
else:
    print("ERROR: Build failed, iso not found.")
print("Build completed in :", datetime.now() - beforetime)
