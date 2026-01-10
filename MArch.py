#!/usr/bin/env python3
"""Provision Arch."""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
# Custom includes
import CFunc
import CFuncExt

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

### Functions ###
def yay_invoke(run_as_user: str, options: str):
    """Invoke yay as normal user"""
    if shutil.which("yay"):
        CFunc.run_as_user(run_as_user, "yay --noconfirm {0}".format(options), error_on_fail=True)
    else:
        print("ERROR: yay not found. Exiting.")
        sys.exit(1)
def pacman_update():
    """Pacman system update"""
    CFunc.pacman_invoke("-Syu")
def yay_install(run_as_user: str, packages: str):
    """Install packages with yay"""
    yay_invoke(run_as_user, "-S --needed {0}".format(packages))
def pacman_check_remove(package):
    """Check if a package is installed, and remove it (and its dependencies)"""
    # Search for the pacakge.
    package_found_status = subprocess.run("pacman -Qi {0}".format(package), shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    if package_found_status == 0:
        subprocess.run("pacman -Rscn --noconfirm {0}".format(package), shell=True, check=False)
def lightdm_configure():
    """Configure lightdm"""
    CFunc.pacman_install("lightdm lightdm-webkit2-greeter lightdm-webkit-theme-litarvan")
    subprocess.run("sed -i '/^#greeter-session=.*/s/^#//g' /etc/lightdm/lightdm.conf", shell=True, check=True)
    subprocess.run("sed -i 's/^greeter-session=.*/greeter-session=lightdm-webkit2-greeter/g' /etc/lightdm/lightdm.conf", shell=True, check=True)
    subprocess.run("sed -i 's/^webkit_theme=.*/webkit_theme=litarvan/g' /etc/lightdm/lightdm-webkit2-greeter.conf", shell=True, check=True)
    CFunc.sysctl_enable("-f lightdm", error_on_fail=True)
def install_aur_pkg(package: str, username, usergroup):
    """Install an aur package using makepkg."""
    package_gitcheckout_folder = os.path.join(os.sep, "tmp", package)
    subprocess.run("cd /tmp ; git clone https://aur.archlinux.org/{0}.git".format(package), shell=True, check=True)
    CFunc.chown_recursive(package_gitcheckout_folder, username, usergroup)
    CFunc.run_as_user(username, "cd {0} ; makepkg --noconfirm -si".format(package_gitcheckout_folder), error_on_fail=True)
    shutil.rmtree(package_gitcheckout_folder)
def snapper_arch():
    """Install snapper on Arch."""
    status = subprocess.run('mount -v | grep " on / type btrfs"', check=False, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    if status == 0:
        print("Installing snapper for Arch.")
        CFunc.pacman_install("snapper snap-pac grub-btrfs inotify-tools")
        yayuser = CFunc.getnormaluser()
        yay_install(yayuser[0], "btrfs-assistant")
        # Create snapper configs
        subprocess.run("snapper -c root create-config /", check=True, shell=True)
        subprocess.run("snapper -c home create-config /home", check=True, shell=True)
        subprocess.run("snapper -c var create-config /var", check=True, shell=True)
        # Create snapshots
        subprocess.run("snapper -c root create", check=True, shell=True)
        subprocess.run("snapper -c home create", check=True, shell=True)
        # snapper config
        with open("/etc/snapper/configs/root", 'w') as f:
            f.write('''
SUBVOLUME="/"
FSTYPE="btrfs"
QGROUP=""
SPACE_LIMIT="0.5"
FREE_LIMIT="0.2"
ALLOW_USERS=""
ALLOW_GROUPS=""
SYNC_ACL="no"
BACKGROUND_COMPARISON="yes"
NUMBER_CLEANUP="yes"
NUMBER_MIN_AGE="1800"
NUMBER_LIMIT="25"
NUMBER_LIMIT_IMPORTANT="10"
TIMELINE_CREATE="yes"
TIMELINE_CLEANUP="yes"
TIMELINE_MIN_AGE="1800"
TIMELINE_LIMIT_HOURLY="4"
TIMELINE_LIMIT_DAILY="7"
TIMELINE_LIMIT_WEEKLY="5"
TIMELINE_LIMIT_MONTHLY="3"
TIMELINE_LIMIT_YEARLY="0"
EMPTY_PRE_POST_CLEANUP="yes"
EMPTY_PRE_POST_MIN_AGE="1800"
''')
        # Enable snapper timers
        CFunc.sysctl_enable("snapper-cleanup.timer snapper-timeline.timer grub-btrfsd", now=True)
        # First execution
        subprocess.run("/etc/grub.d/41_snapshots-btrfs", check=False, shell=True)
        # grub update
        CFuncExt.GrubUpdate()


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Install Arch Software.')
    parser.add_argument("-d", "--desktop", help='Desktop Environment (i.e. gnome, kde, mate, etc)')
    parser.add_argument("-x", "--nogui", help='Configure script to disable GUI.', action="store_true")
    args = parser.parse_args()

    # Get non-root user information.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
    MACHINEARCH = CFunc.machinearch()
    print("Username is:", USERNAMEVAR)
    print("Group Name is:", USERGROUP)
    print("Desktop Environment:", args.desktop)

    # Exit if not root.
    CFunc.is_root(True)

    # Get VM State
    vmstatus = CFunc.getvmstate()

    # Update mirrors.
    CFunc.pacman_install("pacman-mirrorlist")
    CFunc.pacman_invoke("-Syy")

    ### Install Software ###
    # Install AUR dependencies
    CFunc.pacman_install("base-devel git")
    # Sudoers changes
    CFuncExt.SudoersEnvSettings()
    # Edit sudoers to add pacman.
    sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
    CFunc.AddLineToSudoersFile(sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
    CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("pacman")))
    if vmstatus:
        CFunc.AddLineToSudoersFile(os.path.join(os.sep, "etc", "sudoers.d", "vmconfig"), f"{USERNAMEVAR} ALL=(ALL) NOPASSWD: ALL", overwrite=True)
    # Yay
    if not shutil.which("yay"):
        install_aur_pkg("yay-bin", USERNAMEVAR, USERGROUP)

    # Cli tools
    CFunc.pacman_install("bash-completion fish starship zsh zsh-completions nano git tmux iotop rsync p7zip zip unzip unrar xdg-utils xdg-user-dirs sshfs openssh avahi nss-mdns ntfs-3g exfat-utils python-pip")
    CFunc.sysctl_enable("sshd avahi-daemon", error_on_fail=True)
    # Topgrade
    yay_install(USERNAMEVAR, "topgrade-bin")
    # Add mdns_minimal to nsswitch to resolve .local domains.
    subprocess.run('sed -i "s/^hosts: files mymachines mdns4_minimal/hosts: files mdns_minimal mymachines mdns4_minimal/g" /etc/nsswitch.conf', shell=True, check=False)
    CFunc.pacman_install("powerline-fonts ttf-roboto ttf-roboto-mono noto-fonts ttf-dejavu ttf-liberation")
    # Samba
    CFunc.pacman_install("samba")
    CFunc.sysctl_enable("smb nmb winbind", error_on_fail=True)
    # cifs-utils
    CFunc.pacman_install("cifs-utils")
    # NTP Configuration
    CFunc.sysctl_enable("systemd-timesyncd", error_on_fail=True)
    subprocess.run("timedatectl set-local-rtc false; timedatectl set-ntp 1", shell=True, check=True)
    # oomd
    CFunc.sysctl_enable("systemd-oomd", error_on_fail=True)
    # firewalld
    CFunc.pacman_install("firewalld")
    CFunc.sysctl_enable("firewalld", now=True, error_on_fail=True)
    CFuncExt.FirewalldConfig()
    # GUI Packages
    if not args.nogui:
        # X Server
        CFunc.pacman_install("xorg xorg-drivers")
        # Update font cache
        subprocess.run("fc-cache", shell=True, check=True)
        # Browsers
        CFunc.pacman_install("firefox")
        # Cups
        CFunc.pacman_install("cups-pdf")
        # Remote access
        CFunc.pacman_install("remmina")
        CFunc.pacman_install("ffmpeg mpv yt-dlp")
        yay_install(USERNAMEVAR, "yt-dlp-drop-in")
        # Editors
        yay_install(USERNAMEVAR, "vscodium-bin")
        # Syncthing
        CFunc.pacman_install("syncthing")
        CFunc.pacman_install("dconf-editor")
        CFunc.pacman_install("gnome-disk-utility")

    # Install software for VMs
    if vmstatus == "kvm":
        CFunc.pacman_install("spice-vdagent qemu-guest-agent")
        CFunc.sysctl_enable("spice-vdagentd qemu-guest-agent", error_on_fail=True)
    if vmstatus == "vbox":
        if args.nogui:
            CFunc.pacman_install("virtualbox-guest-utils-nox")
        else:
            CFunc.pacman_install("virtualbox-guest-utils")
        CFunc.pacman_install("virtualbox-guest-dkms")

    # Install Desktop Software
    if args.desktop == "gnome":
        # Gnome
        CFunc.pacman_install("gnome dconf-editor gedit gnome-tweaks gnome-firmware ptyxis")
        CFunc.sysctl_enable("-f gdm", error_on_fail=True)
        # Some Gnome Extensions
        CFunc.pacman_install("gnome-shell-extensions gpaste")
        yay_install(USERNAMEVAR, "aur/gnome-browser-connector")
        # Install gs installer script.
        gs_installer = CFunc.downloadfile("https://raw.githubusercontent.com/PedMan/gnome-shell-extension-installer/master/gnome-shell-extension-installer", os.path.join(os.sep, "usr", "local", "bin"), overwrite=True)
        os.chmod(gs_installer[0], 0o777)
        # Dash to panel
        CFunc.run_as_user_su(USERNAMEVAR, "{0} --yes 1160".format(gs_installer[0]))
        # Kstatusnotifier
        CFunc.run_as_user_su(USERNAMEVAR, "{0} --yes 615".format(gs_installer[0]))
    elif args.desktop == "kde":
        # KDE
        CFunc.pacman_install("plasma-meta kio-extras sddm okular gwenview kio-extras kio-zeroconf kde-system-meta ark konsole kcalc kwrite kwalletmanager")
        CFunc.sysctl_enable("-f sddm", error_on_fail=True)
    elif args.desktop == "mate":
        # MATE
        CFunc.pacman_install("mate network-manager-applet mate-extra")
        lightdm_configure()
        # Brisk-menu
        yay_install(USERNAMEVAR, "brisk-menu")
        # Run MATE Configuration
        subprocess.run("{0}/DExtMate.py".format(SCRIPTDIR), shell=True, check=True)
    elif args.desktop == "xfce":
        CFunc.pacman_install("xfce4 xfce4-terminal network-manager-applet xfce4-notifyd xfce4-whiskermenu-plugin engrampa")
        # xfce4-goodies
        CFunc.pacman_install("thunar-archive-plugin thunar-media-tags-plugin xfce4-artwork xfce4-battery-plugin xfce4-clipman-plugin xfce4-cpufreq-plugin xfce4-cpugraph-plugin xfce4-datetime-plugin xfce4-diskperf-plugin xfce4-fsguard-plugin xfce4-genmon-plugin xfce4-mount-plugin xfce4-mpc-plugin xfce4-netload-plugin xfce4-notifyd xfce4-pulseaudio-plugin xfce4-screensaver xfce4-screenshooter xfce4-sensors-plugin xfce4-systemload-plugin xfce4-taskmanager xfce4-timer-plugin xfce4-wavelan-plugin xfce4-weather-plugin xfce4-xkb-plugin xfce4-whiskermenu-plugin")
        lightdm_configure()

    if not args.nogui:
        # Numix
        yay_install(USERNAMEVAR, "aur/numix-icon-theme-git aur/numix-circle-icon-theme-git")
        # Disable multi-user target.
        CFunc.sysctl_disable("multi-user.target", error_on_fail=False)

    # Add normal user to all reasonable groups
    CFunc.AddUserToGroup("disk")
    CFunc.AddUserToGroup("lp")
    CFunc.AddUserToGroup("wheel")
    CFunc.AddUserToGroup("cdrom")
    CFunc.AddUserToGroup("man")
    CFunc.AddUserToGroup("dialout")
    CFunc.AddUserToGroup("floppy")
    CFunc.AddUserToGroup("games")
    CFunc.AddUserToGroup("tape")
    CFunc.AddUserToGroup("video")
    CFunc.AddUserToGroup("audio")
    CFunc.AddUserToGroup("input")
    CFunc.AddUserToGroup("network")
    CFunc.AddUserToGroup("sys")
    CFunc.AddUserToGroup("power")
    CFunc.AddUserToGroup("kvm")
    CFunc.AddUserToGroup("systemd-journal")
    CFunc.AddUserToGroup("systemd-network")
    CFunc.AddUserToGroup("systemd-resolve")
    CFunc.AddUserToGroup("systemd-timesync")
    CFunc.AddUserToGroup("pipewire")
    CFunc.AddUserToGroup("colord")
    CFunc.AddUserToGroup("nm-openconnect")
    CFunc.AddUserToGroup("vboxsf")

    # Hdparm
    CFunc.pacman_install("smartmontools hdparm")

    if not args.nogui:
        # Flatpak setup
        CFunc.pacman_install("flatpak xdg-desktop-portal")
        CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("flatpak")))

    # Disable mitigations
    CFuncExt.GrubEnvAdd(os.path.join(os.sep, "etc", "default", "grub"), "GRUB_CMDLINE_LINUX", "mitigations=off")
    CFuncExt.GrubUpdate()

    # Enable snapper
    snapper_arch()

    # Extra scripts
    subprocess.run("{0}/CCSClone.py".format(SCRIPTDIR), shell=True, check=True)
    if not args.nogui:
        subprocess.run(os.path.join(SCRIPTDIR, "CFlatpakConfig.py"), shell=True, check=True)
    subprocess.run("{0}/Csshconfig.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/CShellConfig.py -f -z -d".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/CDisplayManagerConfig.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/CVMGeneral.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/Cxdgdirs.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/Czram.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/CSysConfig.sh".format(SCRIPTDIR), shell=True, check=True)

    # Update system. Done at the end to avoid kernel updates.
    pacman_update()

    print("\nScript End")
