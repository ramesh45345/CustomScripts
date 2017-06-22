#!/bin/bash

###############################################################################
##################        Initial Setup and Variables      ####################
###############################################################################

if [ "$(id -u)" != "0" ]; then
	echo "Not running with root. Please run the script with su privledges."
	exit 1;
fi

# Get folder of this script
SCRIPTSOURCE="${BASH_SOURCE[0]}"
FLWSOURCE="$(readlink -f "$SCRIPTSOURCE")"
SCRIPTDIR="$(dirname "$FLWSOURCE")"
SCRNAME="$(basename $SCRIPTSOURCE)"
echo "Executing ${SCRNAME}."

source "$SCRIPTDIR/Comp-GeneralFunctions.sh"

###############################################################################
#########################        Compose Script      ##########################
###############################################################################

DEBRELEASE=$(lsb_release -sc)
OS=$(lsb_release -si)
NOPROMPT=0

usage () {
	echo "h - help"
	echo "e - Set Desktop Environment"
	echo "s - Samba password"
	echo "n - Do not prompt to continue."
	exit 0;
}

# Get options
while getopts ":due:s:nh" OPT
do
	case $OPT in
		h)
			echo "Select a valid option."
			usage
			;;
		e)
			SETDE="$OPTARG"
			;;
		s)
			SMBPASSWORD="$OPTARG"
			;;
		n)
			NOPROMPT=1
			;;
		\?)
			echo "Invalid option: -$OPTARG" 1>&2
			usage
			exit 1
			;;
		:)
			echo "Option -$OPTARG requires an argument" 1>&2
			usage
			exit 1
			;;
	esac
done

source "$SCRIPTDIR/Comp-InitVars.sh"

# Unlock root account first
ROOTACCTSTATUS=$(passwd -S root | awk '{print $2}')
if [ $ROOTACCTSTATUS != "P" ]; then
	echo "Please set the root password."
	passwd root
	echo "Please rerun this script now that the root account is unlocked."
	exit 0
fi

# Install a desktop environment. 0=do nothing, 1=GNOME, 2=KDE, 3=MATE
if [ -z "$SETDE" ]; then
	read -p "Enter a number to install a desktop environment (0=do nothing/default option, 1=GNOME, 2=KDE, 3=MATE):" SETDE
	export SETDE=${SETDE//[^a-zA-Z0-9_]/}
	if [ -z "$SETDE" ]; then
		echo "No input found. Defaulting to 0."
		export SETDE=0
	fi
fi
echo "Desktop Environment is $SETDE"

if [[ $NOPROMPT != 1 ]]; then
	read -p "Press any key to continue."
fi
set -eu

source "$SCRIPTDIR/Comp-UbuntuRepos.sh"

source "$SCRIPTDIR/Comp-UbuntuSoftware.sh"

source "$SCRIPTDIR/Comp-sdtimers.sh"

source "$SCRIPTDIR/Comp-sshconfig.sh"

"$SCRIPTDIR/Comp-BashFish.py"

source "$SCRIPTDIR/Comp-CSClone.sh"

source "$SCRIPTDIR/Comp-DisplayManagerConfig.sh"

source "$SCRIPTDIR/Comp-SambaConfig.sh"

source "$SCRIPTDIR/Comp-VMGeneral.sh"

source "$SCRIPTDIR/Comp-xdgdirs.sh"

"$SCRIPTDIR/Comp-zram.py"

source "$SCRIPTDIR/Comp-SysConfig.sh"

sleep 1
echo ""
echo "Script Completed Successfully."
echo ""
