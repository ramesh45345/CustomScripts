#!/bin/bash
set -eu

# Date if ISO build.
DATE=$(date +"%F")
# Name of ISO.
ISOFILENAME=archMATEcustom

# Set location to perform build and store ISO.
if [ -d /mnt/Storage ]; then
	ARCHLIVEPATH=/mnt/Storage/archlive
	OUTFOLDER=/mnt/Storage
elif [ -d /media/sf_Storage ]; then
	ARCHLIVEPATH=~/archlive
	OUTFOLDER=/media/sf_Storage
else
	ARCHLIVEPATH=~/archlive
	OUTFOLDER=~
fi

# Repo variables

# Folder to build pacakges in.
BUILDFOLDER=/tmp

# Folder to store repo in.
REPONAME=localrepo
REPOFOLDER=/tmp/${REPONAME}

# Repo Functions

# Function for AUR build.
aur_build(){
	cd $BUILDFOLDER
	#AUR2LTR=$(echo "${AURPKG}" | cut -c-2)
	wget https://aur4.archlinux.org/cgit/aur.git/snapshot/${AURPKG}.tar.gz
	#curl -O https://aur.archlinux.org/packages/${AUR2LTR}/${AURPKG}/${AURPKG}.tar.gz
	tar zxvf ${AURPKG}.tar.gz
	sudo chmod a+rwx -R ${AURPKG}
	cd ${AURPKG}
	sudo su nobody -s /bin/bash <<'EOL'
		makepkg --noconfirm -c -f
EOL
	sudo chmod a+rwx ${AURPKG}-*.pkg.tar.xz
	sudo chown 1000:100 ${AURPKG}-*.pkg.tar.xz
	sudo mv ${AURPKG}-*.pkg.tar.xz ../
	cd ..
	sudo rm -rf ${AURPKG}/
	sudo rm ${AURPKG}.tar.gz
}

# Function for building the repo
build_repo(){
	echo "Building Local Repository at ${REPOFOLDER}."
	if stat --printf='' ${BUILDFOLDER}/*-x86_64.pkg.tar.xz 2>/dev/null; then
		sudo mv ${BUILDFOLDER}/*-x86_64.pkg.tar.xz ${REPOFOLDER}/x86_64
	fi
	if stat --printf='' ${BUILDFOLDER}/*-i686.pkg.tar.xz 2>/dev/null; then
		sudo mv ${BUILDFOLDER}/*-i686.pkg.tar.xz ${REPOFOLDER}/i686
	fi
	if stat --printf='' ${BUILDFOLDER}/*-any.pkg.tar.xz 2>/dev/null; then
		sudo mv ${BUILDFOLDER}/*-any.pkg.tar.xz ${REPOFOLDER}/x86_64
		sudo cp ${REPOFOLDER}/x86_64/*-any.pkg.tar.xz ${REPOFOLDER}/i686/
	fi
	sudo repo-add ${REPOFOLDER}/x86_64/${REPONAME}.db.tar.gz ${REPOFOLDER}/x86_64/*.pkg.tar.xz
	sudo repo-add ${REPOFOLDER}/i686/${REPONAME}.db.tar.gz ${REPOFOLDER}/i686/*.pkg.tar.xz
	sudo chmod a+rwx -R ${REPOFOLDER}
	sudo chown 1000:100 -R ${REPOFOLDER}
}



# Install archiso if folders are missing.
if [ ! -d /usr/share/archiso/configs/releng/ ]; then
	sudo pacman -S --needed --noconfirm archiso curl
fi

if [ -d $ARCHLIVEPATH ]; then
	echo "Cleaning existing archlive folder."
	set +e
	sudo umount -l $ARCHLIVEPATH/work/mnt/airootfs
	sudo umount -l $ARCHLIVEPATH/work/i686/airootfs
	sudo umount -l $ARCHLIVEPATH/work/x86_64/airootfs
	sudo rm -rf $ARCHLIVEPATH
	set -e
fi

# Clean local repo if it exists.
if [ -d ${REPOFOLDER} ]; then
	rm -rf ${REPOFOLDER}
fi

cp -r /usr/share/archiso/configs/releng/ $ARCHLIVEPATH

<<"COMMENT5"
if ! grep -Fq "copytoram" $ARCHLIVEPATH/syslinux/archiso_sys64.cfg; then
	sed -i '/APPEND/ s|$| copytoram=y |' $ARCHLIVEPATH/syslinux/archiso_sys32.cfg
	sed -i '/APPEND/ s|$| copytoram=y |' $ARCHLIVEPATH/syslinux/archiso_sys64.cfg
fi
COMMENT5

# Set syslinux timeout
if ! grep -iq "^TIMEOUT" "$ARCHLIVEPATH/syslinux/archiso_sys_both_inc.cfg"; then
	echo "TIMEOUT 50" >> "$ARCHLIVEPATH/syslinux/archiso_sys_both_inc.cfg"
	echo "TOTALTIMEOUT 600" >> "$ARCHLIVEPATH/syslinux/archiso_sys_both_inc.cfg"
fi

# Prepare AUR packages for local repo.
if [ ! -d ${REPOFOLDER} ]; then
	echo "Creating ${REPOFOLDER}."
	mkdir -p ${REPOFOLDER}
	echo "Creating ${REPOFOLDER}/i686."
	mkdir -p ${REPOFOLDER}/i686
	echo "Creating ${REPOFOLDER}/x86_64."
	mkdir -p ${REPOFOLDER}/x86_64
	chmod 777 -R ${REPOFOLDER}
fi

# Build debootstrap from AUR
AURPKG=debootstrap
aur_build

# Build the local repo (twice, since the first build yields a corrupted archive).
build_repo
build_repo

# Add local created repo if it exists to pacman.conf for live disk.
if [ -d ${REPOFOLDER} ] && ! grep -ixq "\[${REPONAME}\]" $ARCHLIVEPATH/pacman.conf; then
	echo "Adding ${REPONAME} to $ARCHLIVEPATH/pacman.conf."
	bash -c "cat >>${ARCHLIVEPATH}/pacman.conf" <<EOL
[${REPONAME}]
SigLevel = Optional TrustAll
Server = file://${REPOFOLDER}/\$arch

EOL
fi

if ! grep -Fq "lxdm" $ARCHLIVEPATH/packages.both; then
	sudo sh -c "cat >>$ARCHLIVEPATH/packages.both" <<'EOL'
ipw2200-fw
zd1211-firmware
xorg-server
xorg-server-utils
xorg-drivers
mesa-libgl
xorg-xinit
virtualbox-guest-modules
virtualbox-guest-utils
xf86-input-vmmouse
xf86-video-vmware
open-vm-tools
mate
mate-extra
networkmanager
network-manager-applet
gnome-keyring
gnome-icon-theme
zip
unzip
p7zip
unrar
lxdm
gparted
clonezilla
partimage
fsarchiver
btrfs-progs
xfsprogs
gnome-disk-utility
midori
fsarchiver
grsync
smbclient
gvfs
gvfs-smb
davfs2
binutils
debootstrap
EOL
fi


if ! grep -Fq "Arch-Plain.sh" $ARCHLIVEPATH/airootfs/root/customize_airootfs.sh; then
	sudo sh -c "cat >>$ARCHLIVEPATH/airootfs/root/customize_airootfs.sh" <<'EOLXYZ'

savespace(){
	localepurge
	yes | pacman -Scc
}

<<COMMENT2
if ! grep -iq "user-data-dir" /usr/bin/chromium; then
	sed -i 's/exec \/usr\/lib\/chromium\/chromium \$CHROMIUM_FLAGS \"\$\@\"/exec \/usr\/lib\/chromium\/chromium \$CHROMIUM_FLAGS \"\$\@\" --user-data-dir/g' /usr/bin/chromium
fi
COMMENT2

if [ $(uname -m) = "x86_64" ]; then
	if ! grep -Fq "multilib" /etc/pacman.conf; then
		cat >>/etc/pacman.conf <<'EOL'

[multilib]
SigLevel = PackageRequired
Include = /etc/pacman.d/mirrorlist
EOL
	fi
fi

# Virtualbox stuff
if [ ! -f /etc/modules-load.d/virtualbox.conf ]; then
	cat >>/etc/modules-load.d/virtualbox.conf <<EOL
vboxguest
vboxsf
vboxvideo
EOL
fi

systemctl enable vboxservice
systemctl enable vmtoolsd
systemctl enable vmware-vmblock-fuse.service

systemctl disable multi-user.target

systemctl -f enable lxdm
sed -i 's/#\ autologin=dgod/autologin=root/g' /etc/lxdm/lxdm.conf
sed -i 's/#\ session=\/usr\/bin\/startlxde/session=\/usr\/bin\/mate-session/g' /etc/lxdm/lxdm.conf

systemctl enable NetworkManager

# Set computer to not sleep on lid close
if ! grep -Fxq "HandleLidSwitch=lock" /etc/systemd/logind.conf; then
	echo 'HandleLidSwitch=lock' >> /etc/systemd/logind.conf
fi

# Create box.com mount
mkdir -p /media/Box
echo "https://dav.box.com/dav rmkrish55+box@gmail.com h7*q9HAHPzEJ" >> /etc/davfs2/secrets
echo "use_locks 0" >> /etc/davfs2/davfs2.conf
echo "" >> /etc/fstab
echo "https://dav.box.com/dav /media/Box davfs rw,noauto,x-systemd.automount 0 0" >> /etc/fstab

# Add box to path
if ! grep "Box" /root/.zshrc; then
	cat >>/root/.zshrc <<'EOLZSH'

if [ -d /media/Box/LinuxScripts ]; then
	export PATH=$PATH:/media/Box/LinuxScripts
fi
EOLZSH
fi

#savespace

EOLXYZ
fi

cd $ARCHLIVEPATH


sudo bash <<EOF
$ARCHLIVEPATH/build.sh -v -o $OUTFOLDER -N $ISOFILENAME
rm -rf $ARCHLIVEPATH
if [ -d ${REPOFOLDER} ]; then
	rm -rf ${REPOFOLDER}
fi
chown $USER:users $OUTFOLDER/$ISOFILENAME*
chmod 777 $OUTFOLDER/$ISOFILENAME*
EOF

