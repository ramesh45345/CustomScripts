#!/usr/bin/env python3
"""Create a Fedora live-cd."""

# Python includes.
import argparse
from datetime import datetime
import functools
import os
import shutil
import subprocess
import time
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

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
parser.add_argument("-r", "--releasever", help='Release Version, default: %(default)s', type=int, default=43)

# Save arguments.
args = parser.parse_args()

# Process variables
buildfolder = os.path.abspath(args.workfolderroot)
print(f"Root of Working Folder: {buildfolder}")
outfolder = os.path.abspath(args.output)
print(f"ISO Output Folder: {outfolder}")
print(f"Release Version is {args.releasever}")

if args.noprompt is False:
    input("Press Enter to continue.")

# Create the work folder
if os.path.isdir(buildfolder):
    print("Work folder {0} already exists.".format(buildfolder))
else:
    print("Creating work folder {0}.".format(buildfolder))
    os.makedirs(buildfolder, 0o777)

# Clone fedora-kiwi to work folder
fedoralivegit_folder = os.path.join(buildfolder, "fedora-kiwi-descriptions")
CFunc.gitclone("https://pagure.io/fedora-kiwi-descriptions.git", fedoralivegit_folder)
subprocess.run(f"cd {fedoralivegit_folder}; git checkout -f; git pull; git checkout f{args.releasever}", shell=True)

# Clean
imgroot = os.path.join(fedoralivegit_folder, "outdir-build", "build", "image-root")
if os.path.exists(imgroot):
    shutil.rmtree(imgroot)

# grub timeout
subprocess.run(f"""sed -i 's/^set default=.*/set default="0"/g' {os.path.join(fedoralivegit_folder, "grub-x86.cfg.iso-template")}""", shell=True, check=True)
subprocess.run(f"""sed -i 's/^set timeout=.*/set timeout=1/g' {os.path.join(fedoralivegit_folder, "grub-x86.cfg.iso-template")}""", shell=True, check=True)

# config.sh
configsh_text = r"""#!/bin/bash

set -euxo pipefail

#======================================
# Functions...
#--------------------------------------
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile

#======================================
# Greeting...
#--------------------------------------
echo "Configure image: [$kiwi_iname]-[$kiwi_profiles]..."

#======================================
# Set SELinux booleans
#--------------------------------------
if [[ "$kiwi_profiles" != *"Container"* ]] && [[ "$kiwi_profiles" != *"FEX"* ]] && [[ "$kiwi_profiles" != *"WSL"* ]]; then
	## Fixes KDE Plasma, see rhbz#2058657
	setsebool -P selinuxuser_execmod 1
fi

#======================================
# Clear machine specific configuration
#--------------------------------------
## Clear machine-id on pre generated images
rm -f /etc/machine-id
echo 'uninitialized' > /etc/machine-id
## remove random seed, the newly installed instance should make its own
rm -f /var/lib/systemd/random-seed

#======================================
# Configure grub correctly
#--------------------------------------
## Works around issues with grub-bls
## See: https://github.com/OSInside/kiwi/issues/2198
echo "GRUB_DEFAULT=0" >> /etc/default/grub
echo "GRUB_TIMEOUT=1" >> /etc/default/grub
## Disable submenus to match Fedora
echo "GRUB_DISABLE_SUBMENU=true" >> /etc/default/grub
## Disable recovery entries to match Fedora
echo "GRUB_DISABLE_RECOVERY=true" >> /etc/default/grub

# Unlock root
passwd -u root
chsh -s /bin/bash root

# Xfce
echo 'livesys_session="xfce"' > /etc/sysconfig/livesys

cat > /etc/sudoers.d/cssudo << EOSUDOER
## Ensure the liveuser user always can use sudo
Defaults:liveuser !requiretty
liveuser ALL=(ALL) NOPASSWD: ALL
EOSUDOER
chmod 0440 /etc/sudoers.d/cssudo


# Set install langs macro so that new rpms that get installed will
# only install langs that we limit it to.
LANG="en_US"
echo "%_install_langs $LANG" > /etc/rpm/macros.image-language-conf

# https://bugzilla.redhat.com/show_bug.cgi?id=1727489
echo 'LANG="C.UTF-8"' >  /etc/locale.conf

# https://bugzilla.redhat.com/show_bug.cgi?id=1400682
echo "Import RPM GPG key"
releasever=$(rpm --eval '%{?fedora}')
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-fedora-$releasever-primary

# RPMFusion
dnf install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
# RPMSphere
dnf install -y https://github.com/rpmsphere/noarch/raw/master/r/rpmsphere-release-40-1.noarch.rpm
# Terra
dnf install -y --nogpgcheck --repofrompath 'terra,https://repos.fyralabs.com/terra$releasever' terra-release
# vscodium
tee -a /etc/yum.repos.d/vscodium.repo << 'EOF'
[gitlab.com_paulcarroty_vscodium_repo]
name=gitlab.com_paulcarroty_vscodium_repo
baseurl=https://paulcarroty.gitlab.io/vscodium-deb-rpm-repo/rpms/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://gitlab.com/paulcarroty/vscodium-deb-rpm-repo/raw/master/pub.gpg
metadata_expire=1h
EOF

# Packages
dnf install -y  \
    arch-install-scripts \
    btop \
    chntpw \
    fish \
    git \
    iotop \
    openssh-server \
    p7zip \
    p7zip-plugins \
    perl-Time-HiRes \
    podman \
    powerline-fonts \
    python3-passlib \
    qemu-guest-agent \
    rsync \
    s-tui \
    spice-vdagent \
    starship \
    tmux \
    unzip \
    vscodium \
    xfce4-clipman-plugin \
    xfce4-diskperf-plugin \
    xfce4-systemload-plugin \
    xfce4-whiskermenu-plugin \
    xrandr \
    xset \
    zip \
    zsh
# Filesystem utils
dnf install -y \
    btrfs-progs \
    cryptsetup \
    device-mapper \
    exfatprogs \
    f2fs-tools \
    fstransform \
    gdisk \
    gnome-disk-utility \
    gparted \
    partclone
# Clonezilla
dnf install -y clonezilla

# Enable ssh root login with password
sed -i 's/PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config
sed -i '/^#PermitRootLogin.*/s/^#//g' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication.*/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sed -i '/^#PasswordAuthentication.*/s/^#//g' /etc/ssh/sshd_config
sed -i 's/PermitEmptyPasswords.*/PermitEmptyPasswords yes/g' /etc/ssh/sshd_config
sed -i '/^#PermitEmptyPasswords.*/s/^#//g' /etc/ssh/sshd_config

git clone https://github.com/ramesh45345/CustomScripts /opt/CustomScripts
chown 1000:1000 -R /opt/CustomScripts

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
User=liveuser

[Install]
WantedBy=graphical.target
EOL
systemctl enable updatecs.service

# Init scripts
cat > "/usr/local/bin/initsetup" <<"EOL"
#!/bin/bash
/opt/CustomScripts/Cvscode.py &
sudo /opt/CustomScripts/CShellConfig.py -z -f -d
# Set root password
echo "root:asdf" | sudo chpasswd
# Enabling ssh doesn't work during provision for some reason. Do it now.
sudo systemctl daemon-reload
sudo systemctl enable --now sshd
/opt/CustomScripts/Dset.py -p
EOL
chmod a+rwx /usr/local/bin/initsetup

# Run Settings script on desktop startup.
cat >"/etc/xdg/autostart/initsetup.desktop" <<"EOL"
[Desktop Entry]
Name=Settings Script
Exec=/usr/local/bin/initsetup
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
    RADISPLAYS=$(xrandr --listmonitors | awk '{{print $4}}')
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

"""
configsh_path = os.path.join(fedoralivegit_folder, "config.sh")
with open(configsh_path, 'w') as ks_write:
    ks_write.write(configsh_text)

# Get Dates
currentdatetime = time.strftime("%Y-%m-%d_%H%M")
shortdate = time.strftime("%Y%m%d")
beforetime = datetime.now()
isoname = "Fedora-CustomLive-{0}.iso".format(currentdatetime)

# Build
os.chdir(fedoralivegit_folder)
subprocess.run(f"{fedoralivegit_folder}/kiwi-build --kiwi-file=Fedora.kiwi --image-type=iso --image-profile=Xfce-Live --output-dir {fedoralivegit_folder}/outdir --debug", check=True, shell=True)

### Build LiveCD ###
output_iso = os.path.join(fedoralivegit_folder, "outdir-build", f"Fedora.x86_64-{args.releasever}.iso")
if os.path.isfile(output_iso):
    subprocess.run(f"chmod a+rw {output_iso}; chown 1000:100 {output_iso}", shell=True, check=False)
    shutil.move(output_iso, os.path.join(outfolder, isoname))
else:
    print("ERROR: Build failed, iso not found.")
print("Build completed in :", datetime.now() - beforetime)
