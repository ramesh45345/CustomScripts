#!/usr/bin/env python3
"""Create an Arch live-cd."""

# Python includes.
import argparse
from datetime import datetime
import os
import shutil
import subprocess
import sys
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Exit if not root.
CFunc.is_root(True)

### Functions ###
def cleanup():
    """Cleanup build folder."""
    if os.path.isdir(workingfolder):
        shutil.rmtree(workingfolder)


# Get the root user's home folder.
USERHOME = os.path.expanduser("~root")

# Get arguments
parser = argparse.ArgumentParser(description='Build Arch LiveCD.')
parser.add_argument("-n", "--noprompt", help='Do not prompt.', action="store_true")
parser.add_argument("-w", "--workfolderroot", help='Location of Working Folder (default: %(default)s)', default=USERHOME)
parser.add_argument("-o", "--output", help='Output Location of ISO (default: %(default)s)', default=USERHOME)

# Save arguments.
args = parser.parse_args()

# Process variables
buildfolder = os.path.abspath(args.workfolderroot)
print("Root of Working Folder:", buildfolder)
outfolder = os.path.abspath(args.output)
print("ISO Output Folder:", outfolder)
if not os.path.isdir(outfolder):
    sys.exit("\nError, ensure {0} is a folder.".format(outfolder))

if args.noprompt is False:
    input("Press Enter to continue.")

# Working folder
workingfolder = os.path.abspath(os.path.join(buildfolder, "archiso_wf"))
cleanup()

# Copy archiso config
shutil.copytree("/usr/share/archiso/configs/releng/", workingfolder, symlinks=True)

# Set syslinux timeout
archiso_sys_path = os.path.join(workingfolder, "syslinux", "archiso_sys.cfg")
CFunc.find_replace(os.path.join(workingfolder, "syslinux"), 'TIMEOUT 150', 'TIMEOUT 20', "archiso_sys.cfg")
CFunc.find_replace(os.path.join(workingfolder, "efiboot/loader"), 'timeout 15', 'timeout 2', "loader.conf")

# Set iso name
isoname = "Arch-CustomLive"
CFunc.find_replace(workingfolder, 'iso_name="archlinux"', 'iso_name="{0}"'.format(isoname), "profiledef.sh")

with open(os.path.join(workingfolder, "packages.x86_64"), 'a') as f:
    f.write(r"""
# My custom packages

# Utilities
zip
unzip
p7zip
unrar
gparted
clonezilla
partimage
fsarchiver
btrfs-progs
xfsprogs
gnome-disk-utility
grsync
smbclient
binutils
git
chntpw
debootstrap
openssh
avahi
nss-mdns
tmux
zsh
fish

# Virtual Machine guest
spice-vdagent
qemu-guest-agent

# Desktop stuff
lxdm
xorg-server
xorg-drivers
mesa-libgl
mesa-demos
xorg-xinit
xf86-input-vmmouse
xf86-video-vmware
open-vm-tools
onboard
networkmanager
network-manager-applet
gnome-keyring
gnome-icon-theme
firefox
gvfs
gvfs-smb
tilix

# Mate Desktop
mate

# Mate Extra tools
atril
caja-open-terminal
engrampa
eom
galculator
mate-applets
mate-power-manager
mate-screensaver
mate-system-monitor
mate-terminal
mate-utils
pluma
mate-icon-theme-faenza
ttf-dejavu
ttf-liberation
ttf-roboto
noto-fonts
""")

with open(os.path.join(workingfolder, "airootfs/root/customize_airootfs.sh"), 'a') as f:
    f.write(r"""set -x
SCRIPTBASENAME="/opt/CustomScripts"

git clone https://github.com/ramesh45345/CustomScripts.git /opt/CustomScripts
chmod a+rwx -R /opt/CustomScripts

# Set timezone
ln -sf /usr/share/zoneinfo/US/Eastern /etc/localtime

systemctl enable qemu-guest-agent
systemctl disable multi-user.target

systemctl -f enable lxdm
sed -i 's/#\ autologin=dgod/autologin=liveuser/g' /etc/lxdm/lxdm.conf
sed -i 's/#\ session=\/usr\/bin\/startlxde/session=\/usr\/bin\/mate-session/g' /etc/lxdm/lxdm.conf

systemctl enable NetworkManager

# Set root password
echo "root:asdf" | chpasswd
chsh -s /bin/bash root

# User setup
useradd -m liveuser
echo "liveuser:asdf" | chpasswd
usermod -aG wheel,network,floppy,audio,input,disk,video,storage,optical,systemd-journal,lp liveuser
/opt/CustomScripts/CShellConfig.py -z -d -f -u liveuser
echo "liveuser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/nopw
chmod 0440 /etc/sudoers.d/nopw

# Mate config
/opt/CustomScripts/DExtMate.py

# Enable avahi and ssh
systemctl enable sshd
systemctl enable avahi-daemon
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

# Set computer to not sleep on lid close
if ! grep -Fxq "HandleLidSwitch=lock" /etc/systemd/logind.conf; then
    echo 'HandleLidSwitch=lock' >> /etc/systemd/logind.conf
fi

# --- BEGIN Update CustomScripts on startup ---

cat >/etc/systemd/system/updatecs.service <<EOL
[Unit]
Description=updatecs service
Requires=network-online.target
After=network.target nss-lookup.target network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/bash -c "cd /opt/CustomScripts; git pull"
Restart=on-failure
RestartSec=3s
TimeoutStopSec=7s

[Install]
WantedBy=graphical.target
EOL
systemctl enable updatecs.service

# --- END Update CustomScripts on startup ---

# Run MATE Settings script on desktop startup.
cat >"/etc/xdg/autostart/matesettings.desktop" <<"EOL"
[Desktop Entry]
Name=MATE Settings Script
Exec=/opt/CustomScripts/Dset.py
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
""")

### Build LiveCD ###
beforetime = datetime.now()
os.chdir(workingfolder)
subprocess.run(["mkarchiso", "-v", "-o", outfolder, workingfolder], check=True)
os.chdir(USERHOME)
cleanup()
# chmod a+rwx "$OUTFOLDER/$ISOFILENAME"*
print("Build completed in :", datetime.now() - beforetime)
