#!/usr/bin/env python3
"""Install OpenSUSE Software"""

# Python includes.
import argparse
import os
import shutil
import subprocess
# Custom includes
import CFunc
import CFuncExt

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Exit if not root.
CFunc.is_root(True)

### Functions ###
def repos():
    """Install repos"""
    # Packman
    subprocess.run("zypper ar -f -n packman http://ftp.gwdg.de/pub/linux/misc/packman/suse/openSUSE_Tumbleweed/ packman", shell=True, check=False)
    # Emulators
    subprocess.run('zypper ar -f http://download.opensuse.org/repositories/Emulators/openSUSE_Tumbleweed/ "Emulators"', shell=True, check=False)
    subprocess.run('zypper --gpg-auto-import-keys refresh', shell=True, check=True)
def zypp_install(packages: str):
    """Install packages using zypper."""
    subprocess.run(f"zypper install -y {packages}", shell=True, check=True)


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Install OpenSUSE Software.')
    parser.add_argument("-d", "--desktop", help='Desktop Environment', choices=['gnome', 'kde', 'mate', 'xfce', 'lxqt', 'cinnamon', None], default=None)
    parser.add_argument("-x", "--nogui", help='Configure script to disable GUI.', action="store_true")

    # Save arguments.
    args = parser.parse_args()
    print("Desktop Environment:", args.desktop)

    # Get non-root user information.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
    MACHINEARCH = CFunc.machinearch()
    print("Username is:", USERNAMEVAR)
    print("Group Name is:", USERGROUP)

    # Get VM State
    vmstatus = CFunc.getvmstate()

    # Set up OpenSUSE Repos
    repos()

    # Software
    zypp_install("zsh fish nano tmux iotop rsync p7zip zip unzip xdg-utils xdg-user-dirs")

    # NTP
    # CFunc.sysctl_disable("ntpd")
    CFunc.sysctl_enable("systemd-timesyncd")
    subprocess.run("timedatectl set-local-rtc false", shell=True, check=True)
    subprocess.run("timedatectl set-ntp 1", shell=True, check=True)

    # Samba
    zypp_install("samba samba-client")
    CFunc.sysctl_enable("smb")

    # Podman
    zypp_install("podman podman-docker")

    # Install software for VMs
    if vmstatus == "kvm":
        zypp_install("spice-vdagent qemu-guest-agent")
    if vmstatus == "vbox":
        zypp_install("virtualbox-guest-tools virtualbox-guest-x11")

    # GUI Packages
    if not args.nogui:
        # Browser
        zypp_install("MozillaFirefox MozillaFirefox-branding-openSUSE")

        # Numix Circle icon theme
        CFuncExt.numix_icons()

        # Fonts
        zypp_install("noto-sans-fonts ubuntu-fonts liberation-fonts google-roboto-fonts")

        # Yast
        zypp_install("patterns-yast-x11_yast patterns-yast-yast2_desktop")

        subprocess.run("systemctl set-default graphical.target", shell=True, check=True)

    # Install Desktop Software
    if args.desktop == "gnome":
        # Gnome
        zypp_install("patterns-gnome-gnome patterns-gnome-gnome_x11 patterns-gnome-gnome_yast gnome-shell-extension-gpaste tilix")
        # Install gs installer script.
        gs_installer = CFunc.downloadfile("https://raw.githubusercontent.com/brunelli/gnome-shell-extension-installer/master/gnome-shell-extension-installer", os.path.join(os.sep, "usr", "local", "bin"), overwrite=True)
        os.chmod(gs_installer[0], 0o777)
        # Dash to panel
        CFunc.run_as_user_su(USERNAMEVAR, "{0} --yes 1160".format(gs_installer[0]))
        # Kstatusnotifier
        CFunc.run_as_user_su(USERNAMEVAR, "{0} --yes 615".format(gs_installer[0]))
    elif args.desktop == "kde":
        # KDE
        zypp_install("patterns-kde-kde_plasma patterns-kde-kde_yast patterns-kde-kde_utilities")
    elif args.desktop == "xfce":
        zypp_install("patterns-xfce-xfce")

    # Sudoers
    CFuncExt.SudoersEnvSettings()
    # Edit sudoers to add zypper.
    opensuse_sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
    CFunc.AddLineToSudoersFile(opensuse_sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
    CFunc.AddLineToSudoersFile(opensuse_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("zypper")))
    CFunc.AddLineToSudoersFile(opensuse_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("podman")))

    # Add normal user to all reasonable groups
    CFunc.AddUserToGroup("disk")
    CFunc.AddUserToGroup("lp")
    CFunc.AddUserToGroup("wheel")
    CFunc.AddUserToGroup("cdrom")
    CFunc.AddUserToGroup("man")
    CFunc.AddUserToGroup("dialout")
    CFunc.AddUserToGroup("tape")
    CFunc.AddUserToGroup("video")
    CFunc.AddUserToGroup("audio")
    CFunc.AddUserToGroup("input")
    CFunc.AddUserToGroup("kvm")
    CFunc.AddUserToGroup("systemd-journal")
    CFunc.AddUserToGroup("systemd-timesync")
    CFunc.AddUserToGroup("pipewire")
    CFunc.AddUserToGroup("colord")
    CFunc.AddUserToGroup("nm-openconnect")
    CFunc.AddUserToGroup("vboxsf")

    # Plymouth and grub
    zypp_install("plymouth plymouth-branding-openSUSE plymouth-dracut")
    subprocess.run("plymouth-set-default-theme spinner -R", shell=True, check=True)
    grub_config = os.path.join(os.sep, "etc", "default", "grub")
    # Comment grub console
    subprocess.run("sed -i '/GRUB_CONSOLE/ s/^#*/#/' {0}".format(grub_config), shell=True, check=True)
    # Disable mitigations
    CFuncExt.GrubEnvAdd(grub_config, "GRUB_CMDLINE_LINUX", "mitigations=off")
    CFuncExt.GrubUpdate()

    # Extra scripts
    subprocess.run(os.path.join(SCRIPTDIR, "CCSClone.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Csshconfig.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CShellConfig.py") + " -f -z -d", shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CDisplayManagerConfig.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CVMGeneral.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Cxdgdirs.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Czram.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CSysConfig.sh"), shell=True, check=True)

    print("\nScript End")
