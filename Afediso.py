#!/usr/bin/env python3
"""Create a Fedora live-cd."""

# Python includes.
import argparse
from datetime import datetime
import os
import shutil
import subprocess
import time
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Exit if not root.
CFunc.is_root(True)

# Get the root user's home folder.
USERHOME = os.path.expanduser("~root")
workfolder_default = os.path.join(USERHOME, "fedlive")

# Get arguments
parser = argparse.ArgumentParser(description='Build Fedora LiveCD.')
parser.add_argument("-n", "--noprompt", help='Do not prompt.', action="store_true")
parser.add_argument("-w", "--workfolderroot", help='Location of Working Folder (default: %(default)s)', default=workfolder_default)
parser.add_argument("-o", "--output", help='Output Location of ISO (default: %(default)s)', default=workfolder_default)
parser.add_argument("-r", "--releasever", help='Release Version, default: %(default)s', type=int, default=38)

# Save arguments.
args = parser.parse_args()

# Process variables
buildfolder = os.path.abspath(args.workfolderroot)
print("Root of Working Folder:", buildfolder)
outfolder = os.path.abspath(args.output)
print("ISO Output Folder:", outfolder)
print("Release Version is {0}".format(args.releasever))

if args.noprompt is False:
    input("Press Enter to continue.")

# Create the work folder
if os.path.isdir(buildfolder):
    print("Work folder {0} already exists.".format(buildfolder))
else:
    print("Creating work folder {0}.".format(buildfolder))
    os.makedirs(buildfolder, 0o777)

# Modify lorax isolinux config
subprocess.run('sed -i "s/^timeout.*/timeout 10/g" /usr/share/lorax/templates.d/99-generic/config_files/x86/isolinux.cfg', shell=True, check=True)
subprocess.run('sed -i "/menu default/d" /usr/share/lorax/templates.d/99-generic/config_files/x86/isolinux.cfg', shell=True, check=True)
subprocess.run(r'sed -i "/label linux/a \ \ menu default" /usr/share/lorax/templates.d/99-generic/config_files/x86/isolinux.cfg', shell=True, check=True)
# Grub settings
subprocess.run('sed -i "s/^set default=.*/set default=0/g" /usr/share/lorax/templates.d/99-generic/live/config_files/x86/grub2-efi.cfg /usr/share/lorax/templates.d/99-generic/config_files/x86/grub2-efi.cfg /usr/share/lorax/templates.d/99-generic/live/config_files/x86/grub2-bios.cfg /usr/share/lorax/templates.d/99-generic/config_files/x86/grub2-bios.cfg', shell=True, check=True)
subprocess.run('sed -i "s/^set timeout=.*/set timeout=1/g" /usr/share/lorax/templates.d/99-generic/live/config_files/x86/grub2-efi.cfg /usr/share/lorax/templates.d/99-generic/config_files/x86/grub2-efi.cfg /usr/share/lorax/templates.d/99-generic/live/config_files/x86/grub2-bios.cfg /usr/share/lorax/templates.d/99-generic/config_files/x86/grub2-bios.cfg', shell=True, check=True)
# Disable selinux and mitigations
subprocess.run('sed -i "s/ quiet$/ quiet selinux=0 mitigations=off/g" /usr/share/lorax/templates.d/99-generic/live/config_files/x86/grub2-bios.cfg /usr/share/lorax/templates.d/99-generic/config_files/x86/grub2-bios.cfg /usr/share/lorax/templates.d/99-generic/config_files/x86/isolinux.cfg /usr/share/lorax/templates.d/99-generic/live/config_files/x86/grub2-efi.cfg /usr/share/lorax/templates.d/99-generic/config_files/x86/grub2-efi.cfg', shell=True, check=True)
# Modify kickstart repos
with open(os.path.join(os.sep, "usr", "share", "spin-kickstarts", "fedora-repo.ks"), 'w') as f:
    f.write("%include fedora-repo-not-rawhide.ks")
# Remove auth statements. Temporary workaround, to be removed.
subprocess.run("sed -i '/^auth */d' /usr/share/spin-kickstarts/fedora-live-base.ks", shell=True, check=False)
# Remove x86-baremetal-tools. Temporary workaround, to be removed when https://github.com/rhinstaller/kickstart-tests/issues/740 is fixed.
subprocess.run("sed -i '/x86-baremetal-tools/d' /usr/share/spin-kickstarts/fedora-live-base.ks", shell=True, check=False)


### Prep Environment ###
# https://fedoraproject.org/wiki/Livemedia-creator-_How_to_create_and_use_a_Live_CD
# https://github.com/rhinstaller/lorax/blob/master/docs/livemedia-creator.rst
ks_text = r"""
%include /usr/share/spin-kickstarts/fedora-live-base.ks
%include /usr/share/spin-kickstarts/fedora-live-minimization.ks

part / --size 7168
selinux --disabled

%packages

# Desktop Environment
@mate-desktop
@mate-applications
@networkmanager-submodules
NetworkManager-wifi
network-manager-applet

# Firmware
iwl4965-firmware
iwl5000-firmware
iwl5150-firmware
iwl6000-firmware
iwl6000g2a-firmware
iwl6000g2b-firmware
iwl6050-firmware
iwl7260-firmware
libertas-sd8686-firmware
libertas-sd8787-firmware
libertas-usb8388-firmware
iwlax2xx-firmware

# CLI Utils
git
zsh
powerline-fonts
nano
tmux
iotop
btop
s-tui
rsync
p7zip
p7zip-plugins
zip
unzip
openssh-server
openssh-clients
avahi
chntpw
debootstrap
gnupg
pacman
arch-install-scripts
podman

# Filesystem utils
fstransform
partclone
btrfs-progs
f2fs-tools
exfatprogs
cryptsetup
device-mapper

# VM Utils
spice-vdagent
qemu-guest-agent
open-vm-tools
open-vm-tools-desktop

# Graphical Utils
gnome-disk-utility
gparted
xset

# For clonezilla
dialog
make
bc

# Exclusions
-thunderbird
-pidgin

%end


%post

# Set DNS nameservers
rm -f /etc/resolv.conf
echo -e "nameserver 1.0.0.1\\nnameserver 1.1.1.1\\nnameserver 2606:4700:4700::1111\\nnameserver 2606:4700:4700::1001" > /etc/resolv.conf

# Pull CustomScripts
git clone https://github.com/ramesh45345/CustomScripts /opt/CustomScripts

# Create liveuser ahead of when it will really be created
useradd -m liveuser
# ShellConfig
python3 /opt/CustomScripts/CShellConfig.py -z -d -u liveuser

# Enable openssh
systemctl enable sshd
# Enable ssh root login with password
sed -i 's/PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config
sed -i '/^#PermitRootLogin.*/s/^#//g' /etc/ssh/sshd_config

# Clonezilla
git clone https://gitlab.com/stevenshiau/drbl drbl
cd drbl
make all
make install
cd ..
git clone https://gitlab.com/stevenshiau/clonezilla clonezilla
cd clonezilla
make all
make install
cd ..

# Delete defaults in sudoers.
sed -e 's/^Defaults    env_reset$/Defaults    !env_reset/g' -i /etc/sudoers
sed -i $'/^Defaults    mail_badpass/ s/^#*/#/' /etc/sudoers
sed -i $'/^Defaults    secure_path/ s/^#*/#/' /etc/sudoers

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

# Run MATE Settings script on desktop startup.
cat >"/etc/xdg/autostart/mate-dset.desktop" <<"EOL"
[Desktop Entry]
Name=MATE Settings Script
Exec=/opt/CustomScripts/Dset.py -p
Terminal=false
Type=Application
EOL

# Script run on boot
cat >> /etc/rc.d/init.d/livesys << EOF

# Set root password
passwd -u root
echo "root:asdf" | chpasswd

# Change shell to zsh
chsh -s /bin/zsh liveuser
# Set path
# echo 'PATH=$PATH:/opt/CustomScripts' | tee -a /root/.bashrc /home/liveuser/.bashrc /root/.zshrc /home/liveuser/.zshrc

# LightDM Autologin
sed -i 's/^#autologin-user=.*/autologin-user=liveuser/' /etc/lightdm/lightdm.conf
# sed -i 's/^#autologin-user-timeout=.*/autologin-user-timeout=0/' /etc/lightdm/lightdm.conf
echo -e "[SeatDefaults]\nautologin-user=liveuser\nuser-session=mate" > /etc/lightdm/lightdm.conf.d/12-autologin.conf
groupadd autologin
gpasswd -a liveuser autologin

# rebuild schema cache with any overrides we installed
glib-compile-schemas /usr/share/glib-2.0/schemas

# set MATE as default session, otherwise login will fail
sed -i 's/^#user-session=.*/user-session=mate/' /etc/lightdm/lightdm.conf

# Turn off PackageKit-command-not-found while uninstalled
if [ -f /etc/PackageKit/CommandNotFound.conf ]; then
  sed -i -e 's/^SoftwareSourceSearch=true/SoftwareSourceSearch=false/' /etc/PackageKit/CommandNotFound.conf
fi

# no updater applet in live environment
rm -f /etc/xdg/autostart/org.mageia.dnfdragora-updater.desktop

mkdir -p /home/liveuser/Desktop
# make sure to set the right permissions and selinux contexts
chown -R liveuser:liveuser /home/liveuser/
restorecon -R /home/liveuser/
EOF

%end
"""
ks_path = os.path.join(buildfolder, "fediso.ks")
with open(ks_path, 'w') as ks_write:
    ks_write.write(ks_text)

# Flatten kickstart file
ks_flat = os.path.join(buildfolder, "flat_fediso.ks")
subprocess.run("ksflatten --config {0} -o {1}".format(ks_path, ks_flat), shell=True, check=True)

### Build LiveCD ###
resultsfolder = os.path.join(buildfolder, "results")
if os.path.isdir(resultsfolder):
    shutil.rmtree(resultsfolder)
# Get Dates
currentdatetime = time.strftime("%Y-%m-%d_%H%M")
shortdate = time.strftime("%Y%m%d")
beforetime = datetime.now()
isoname = "Fedora-CustomLive-{0}.iso".format(currentdatetime)
# Start Build
subprocess.run("livemedia-creator --ks {ks} --resultdir {resultdir} --logfile {outfolder}/livemedia.log --project Fedora-CustomLive --make-iso --volid Fedora-CustomLive-{shortdate} --iso-only --iso-name {isoname} --releasever {releasever} --fs-label Fedora-CustomLive --nomacboot --no-virt".format(ks=ks_flat, resultdir=resultsfolder, isoname=isoname, shortdate=shortdate, outfolder=outfolder, releasever=args.releasever), shell=True, check=False)
subprocess.run("chmod a+rw -R {0}".format(buildfolder), shell=True, check=True)
if os.path.isfile(os.path.join(buildfolder, "results", isoname)):
    shutil.move(os.path.join(buildfolder, "results", isoname), outfolder)
    print('Run to test: "qemu-system-x86_64 -enable-kvm -m 4096 {0}"'.format(os.path.join(outfolder, isoname)))
else:
    print("ERROR: Build failed, iso not found.")
print("Build completed in :", datetime.now() - beforetime)
