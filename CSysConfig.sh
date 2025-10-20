#!/bin/bash

# Get folder of this script
SCRIPTSOURCE="${BASH_SOURCE[0]}"
FLWSOURCE="$(readlink -f "$SCRIPTSOURCE")"
SCRIPTDIR="$(dirname "$FLWSOURCE")"
SCRNAME="$(basename $SCRIPTSOURCE)"
echo "Executing ${SCRNAME}."

# Disable error handlingss
set +eu

# Set user folders if they don't exist.
if [[ ! -z "$SUDO_USER" && "$SUDO_USER" != "root" ]]; then
	export USERNAMEVAR="$SUDO_USER"
elif [ "$USER" != "root" ]; then
	export USERNAMEVAR="$USER"
else
	export USERNAMEVAR="$(id 1000 -un)"
fi
USERGROUP="$(id $USERNAMEVAR -gn)"
USERHOME="/home/$USERNAMEVAR"

[ -z "$MACHINEARCH" ] && MACHINEARCH="$(uname -m)"


if [ "$(id -u)" != "0" ]; then
	echo "Not running with root. Please run the script with su privledges."
	exit 1;
fi


# Logind config edits
if [ -f /etc/systemd/logind.conf ]; then
	# Set computer to not sleep on lid close
	sed -i '/^#HandleLidSwitch=.*/s/^#//g' /etc/systemd/logind.conf
	sed -i 's/^HandleLidSwitch=.*/HandleLidSwitch=lock/g' /etc/systemd/logind.conf
fi

# Modify journald log size
# https://unix.stackexchange.com/questions/139513/how-to-clear-journalctl
if [ -f /etc/systemd/journald.conf ]; then
	# Remove commented lines
	sed -i '/^#Compress=.*/s/^#//g' /etc/systemd/journald.conf
	sed -i '/^#SystemMaxUse=.*/s/^#//g' /etc/systemd/journald.conf
	# Edit uncommented lines
	sed -i 's/^Compress=.*/Compress=yes/g' /etc/systemd/journald.conf
	sed -i 's/^SystemMaxUse=.*/SystemMaxUse=600M/g' /etc/systemd/journald.conf
	# Vacuum existing logs
	journalctl --vacuum-size=595M
fi

# Nano Configuration
NANOCONFIG="set linenumbers\nset constantshow\nset softwrap\nset tabsize 4"
# For root
echo -e $NANOCONFIG > "/root/.nanorc"
# For user
echo -e $NANOCONFIG > "$USERHOME/.nanorc"
chown $USERNAMEVAR:$USERGROUP "$USERHOME/.nanorc"
