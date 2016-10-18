#!/bin/bash

# Get folder of this script
SCRIPTSOURCE="${BASH_SOURCE[0]}"
FLWSOURCE="$(readlink -f "$SCRIPTSOURCE")"
SCRIPTDIR="$(dirname "$FLWSOURCE")"
SCRNAME="$(basename $SCRIPTSOURCE)"
echo "Executing ${SCRNAME}."

# Disable error handlingss
set +eu

# Add general functions if they don't exist.
type -t grepadd >> /dev/null || source "$SCRIPTDIR/Comp-GeneralFunctions.sh"

# Set user folders if they don't exist.
if [ -z $USERNAMEVAR ]; then
	if [[ ! -z "$SUDO_USER" && "$SUDO_USER" != "root" ]]; then
		export USERNAMEVAR="$SUDO_USER"
	elif [ "$USER" != "root" ]; then
		export USERNAMEVAR="$USER"
	else
		export USERNAMEVAR="$(id 1000 -un)"
	fi
	USERGROUP="$(id 1000 -gn)"
	USERHOME="/home/$USERNAMEVAR"
fi

[ -z "$MACHINEARCH" ] && MACHINEARCH="$(uname -m)"


if [ "$(id -u)" != "0" ]; then
	echo "Not running with root. Please run the script with su privledges."
	exit 1;
fi


# Set computer to not sleep on lid close
if ! grep -Fxq "HandleLidSwitch=ignore" /etc/systemd/logind.conf && grep -iq "Latitude D610" "/sys/devices/virtual/dmi/id/product_name"; then
	echo 'HandleLidSwitch=ignore' | sudo tee -a /etc/systemd/logind.conf
elif ! grep -Fxq "HandleLidSwitch=lock" /etc/systemd/logind.conf && ! grep -iq "Latitude D610" "/sys/devices/virtual/dmi/id/product_name"; then
    echo 'HandleLidSwitch=lock' | sudo tee -a /etc/systemd/logind.conf
fi

#Xorg fix for Joysticks
if [ ! -d /etc/X11/xorg.conf.d/ ]; then
	mkdir -p /etc/X11/xorg.conf.d/
	chmod a+r /etc/X11/xorg.conf.d/
fi
bash -c "cat >>/etc/X11/xorg.conf.d/50-joystick.conf" <<'EOL'
Section "InputClass"
        Identifier "joystick catchall"
        MatchIsJoystick "on"
        MatchDevicePath "/dev/input/event*"
        Driver "joystick"
        Option "StartKeysEnabled" "False"       #Disable mouse
        Option "StartMouseEnabled" "False"      #support
EndSection
EOL

# Enable pulseaudio flat volumes
if ! grep -iq "^flat-volumes = no" /etc/pulse/daemon.conf; then
	sed -i '/^;.*flat-volumes =.*/s/^;//g' /etc/pulse/daemon.conf
	sed -i 's/flat-volumes =.*/flat-volumes = no/g' /etc/pulse/daemon.conf
fi

# Modify journald log size
# https://unix.stackexchange.com/questions/139513/how-to-clear-journalctl
if [ -f /etc/systemd/journald.conf ]; then
	# Remove commented lines
	sed -i '/^#Compress=.*/s/^#//g' /etc/systemd/journald.conf
	sed -i '/^#SystemMaxUse=.*/s/^#//g' /etc/systemd/journald.conf
	# Edit uncommented lines
	sed -i 's/^Compress=.*/Compress=yes/g' /etc/systemd/journald.conf
	sed -i 's/^SystemMaxUse=.*/SystemMaxUse=300M/g' /etc/systemd/journald.conf
	# Vacuum existing logs
	journalctl --vacuum-size=295M
	# Vacuum all logs
	#journalctl --vacuum-time=1s
fi
# Disable copy-on-write for journal logs
if [ -d /var/log/journal ]; then
	chattr -R +C /var/log/journal/
fi

# Anacron configuration
if [ -f /etc/anacrontab ]; then
	sed -i 's/RANDOM_DELAY=.*$/RANDOM_DELAY=0/g' /etc/anacrontab
	sed -i 's/START_HOURS_RANGE=.*$/START_HOURS_RANGE=0-24/g' /etc/anacrontab
	sed -i -e 's/1.*\tcron.daily/1\t0\tcron.daily/g' /etc/anacrontab
	sed -i -e 's/7.*\tcron.weekly/7\t0\tcron.weekly/g' /etc/anacrontab
	sed -i -e 's/@monthly.*\tcron.monthly/@monthly 0\tcron.monthly/g' /etc/anacrontab
	sed -i '/^MAILTO=.*/s/^/#/g' /etc/anacrontab
fi

# Some personal cron scripts
# Cleanup thumbnails cron script.
if [ -d "/etc/cron.weekly" ]; then
	multilinereplace "/etc/cron.weekly/cleanthumbs" << EOFXYZ
#!/bin/bash
set -eu
echo "Executing \$0"
su $USERNAMEVAR -s /bin/bash <<'EOL'

if [ -d $USERHOME/.cache/thumbnails ]; then
	SIZEVAR="\$(du -s $USERHOME/.cache/thumbnails | awk '{ print \$1 }')"
	echo "Size is \$SIZEVAR"
	if [[ \$SIZEVAR -ge 100000 ]]; then
		echo "Removing thumbnails."
		rm -rf $USERHOME/.cache/thumbnails
	else
		echo "Not Removing thumbnails."
	fi
else
	echo "No thumbnail folder detected. Exiting."
fi

EOL
EOFXYZ
fi

if [ "${MACHINEARCH}" != "armv7l" ]; then
	echo "Install x86 specific tweaks."

	# Edit grub timeout
	if [ -f /etc/default/grub ]; then
		sed -i 's/GRUB_TIMEOUT=.*$/GRUB_TIMEOUT=1/g' /etc/default/grub
		sed -i 's/GRUB_HIDDEN_TIMEOUT=.*$/GRUB_HIDDEN_TIMEOUT=1/g' /etc/default/grub
		grub_update
	fi

elif [ "${MACHINEARCH}" = "armv7l" ]; then
	echo "Install arm specific tweaks."

fi
