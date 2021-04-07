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
SCRIPTDIR = sys.path[0]

# Exit if not root.
CFunc.is_root(True)


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
def install_aur_pkg(package: str):
    """Install an aur package using makepkg."""
    package_gitcheckout_folder = os.path.join(os.sep, "tmp", package)
    subprocess.run("cd /tmp ; git clone https://aur.archlinux.org/{0}.git".format(package), shell=True, check=True)
    CFunc.chown_recursive(package_gitcheckout_folder, USERNAMEVAR, USERGROUP)
    CFunc.run_as_user(USERNAMEVAR, "cd {0} ; makepkg --noconfirm -si".format(package_gitcheckout_folder), error_on_fail=True)
    shutil.rmtree(package_gitcheckout_folder)


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

    # Get VM State
    vmstatus = CFunc.getvmstate()

    # Update mirrors.
    CFunc.pacman_install("reflector")
    subprocess.run("reflector --country 'United States' --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist", shell=True, check=True)
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
    # Yay
    if not shutil.which("yay"):
        install_aur_pkg("yay-bin")
    # Set pacman.conf to use PackageRequired, don't check sigs for database.
    # https://wiki.archlinux.org/index.php/Powerpill#Troubleshooting
    subprocess.run("sed -i 's/^SigLevel\s*=\s*Required\s*DatabaseOptional/SigLevel = PackageRequired/g' /etc/pacman.conf", shell=True, check=True)
    # Import Xyne gpg key
    CFunc.run_as_user(USERNAMEVAR, "pacman-key --export 1D1F0DC78F173680 > /tmp/xyne.asc", error_on_fail=True)
    CFunc.run_as_user(USERNAMEVAR, "gpg --import /tmp/xyne.asc", error_on_fail=True)
    # Powerpill
    yay_install(USERNAMEVAR, "powerpill")
    # Have yay use powerpill
    CFunc.run_as_user(USERNAMEVAR, "yay --pacman powerpill --save", error_on_fail=True)
    CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("powerpill")))

    # Cli tools
    CFunc.pacman_install("bash-completion fish zsh zsh-completions nano git tmux iotop rsync p7zip zip unzip unrar xdg-utils xdg-user-dirs sshfs openssh avahi nss-mdns ntfs-3g exfat-utils python-pip")
    CFunc.sysctl_enable("sshd avahi-daemon", error_on_fail=True)
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
    # EarlyOOM
    CFunc.pacman_install("earlyoom")
    CFunc.sysctl_enable("earlyoom", error_on_fail=True)
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
        # Audio/video
        CFunc.pacman_install("paprefs")
        # Remote access
        CFunc.pacman_install("remmina")
        # Tilix
        CFunc.pacman_install("tilix")
        CFunc.pacman_install("youtube-dl ffmpeg smplayer mpv")
        # Editors
        CFunc.pacman_install("code")
        # Syncthing
        CFunc.pacman_install("syncthing")
        # Flameshot
        CFunc.pacman_install("flameshot")
        os.makedirs(os.path.join(USERHOME, ".config", "autostart"), exist_ok=True)
        # Start flameshot on user login.
        if os.path.isfile(os.path.join(os.sep, "usr", "share", "applications", "flameshot.desktop")):
            shutil.copy(os.path.join(os.sep, "usr", "share", "applications", "flameshot.desktop"), os.path.join(USERHOME, ".config", "autostart"))
        CFunc.chown_recursive(os.path.join(USERHOME, ".config", ), USERNAMEVAR, USERGROUP)
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
    if vmstatus == "vmware":
        CFunc.pacman_install("open-vm-tools")

    # Install Desktop Software
    if args.desktop == "gnome":
        # Gnome
        CFunc.pacman_install("baobab eog evince file-roller gdm gedit gnome-backgrounds gnome-calculator gnome-characters gnome-clocks gnome-color-manager gnome-control-center gnome-font-viewer gnome-getting-started-docs gnome-keyring gnome-logs gnome-menus gnome-remote-desktop gnome-screenshot gnome-session gnome-settings-daemon gnome-shell gnome-shell-extensions gnome-system-monitor gnome-terminal gnome-themes-extra gnome-user-docs gnome-video-effects gnome-weather gvfs gvfs-google gvfs-gphoto2 gvfs-mtp gvfs-nfs gvfs-smb mutter nautilus orca sushi tracker tracker-miners vino xdg-user-dirs-gtk xdg-desktop-portal-gtk yelp gnome-firmware")
        CFunc.sysctl_enable("-f gdm", error_on_fail=True)
        # Some Gnome Extensions
        CFunc.pacman_install("gnome-tweaks")
        CFunc.pacman_install("gpaste")
        yay_install(USERNAMEVAR, "aur/gnome-shell-extension-topicons-plus-git")
        # Install gs installer script.
        gs_installer = CFunc.downloadfile("https://raw.githubusercontent.com/brunelli/gnome-shell-extension-installer/master/gnome-shell-extension-installer", os.path.join(os.sep, "usr", "local", "bin"), overwrite=True)
        os.chmod(gs_installer[0], 0o777)
        # Install volume extension
        CFunc.run_as_user(USERNAMEVAR, "{0} --yes 858".format(gs_installer[0]), error_on_fail=True)
        # Install dashtodock extension
        CFunc.run_as_user(USERNAMEVAR, "{0} --yes 307".format(gs_installer[0]), error_on_fail=True)
    elif args.desktop == "kde":
        # KDE
        CFunc.pacman_install("plasma kio-extras kdebase sddm")
        CFunc.pacman_install("latte-dock")
        CFunc.pacman_install("pamac-qt pamac-tray-appindicator")
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
        CFunc.pacman_install("xfce4-gtk3 xfce4-terminal network-manager-applet xfce4-notifyd-gtk3 xfce4-whiskermenu-plugin-gtk3 tumbler engrampa")
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
        # Install snapd
        yay_install(USERNAMEVAR, "snapd")
        if not os.path.islink("/snap"):
            os.symlink("/var/lib/snapd/snap", "/snap", target_is_directory=True)
        CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("snap")))
        CFunc.sysctl_enable("snapd.socket", error_on_fail=True)

        # Flatpak setup
        CFunc.pacman_install("flatpak xdg-desktop-portal")
        CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("flatpak")))

    # Disable mitigations
    CFuncExt.GrubEnvAdd(os.path.join(os.sep, "etc", "default", "grub"), "GRUB_CMDLINE_LINUX", "mitigations=off")
    CFuncExt.GrubUpdate()

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
