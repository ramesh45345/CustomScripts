#!/usr/bin/env python3
"""Install Fedora Software"""

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
def repo_rpmfusion():
    """Install RPMFusion repository"""
    CFunc.dnfinstall("https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm")
    CFunc.dnfinstall("rpmfusion-nonfree-appstream-data rpmfusion-free-appstream-data")
    CFunc.dnfinstall("rpmfusion-free-release-tainted rpmfusion-nonfree-release-tainted")
def repo_vscode():
    """Install vscode repository"""
    with open(os.path.join(os.sep, "etc", "yum.repos.d", "vscodium.repo"), 'w') as f:
        f.write("""[gitlab.com_paulcarroty_vscodium_repo]
name=gitlab.com_paulcarroty_vscodium_repo
baseurl=https://paulcarroty.gitlab.io/vscodium-deb-rpm-repo/rpms/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://gitlab.com/paulcarroty/vscodium-deb-rpm-repo/raw/master/pub.gpg
metadata_expire=1h
""")


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Install Fedora Software.')
    parser.add_argument("-d", "--desktop", help='Desktop Environment (i.e. gnome, kde, mate, etc)')
    parser.add_argument("-x", "--nogui", help='Configure script to disable GUI.', action="store_true")

    # Save arguments.
    args = parser.parse_args()
    print("Desktop Environment:", args.desktop)

    # Exit if not root.
    CFunc.is_root(True)

    # Get non-root user information.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
    MACHINEARCH = CFunc.machinearch()
    print("Username is:", USERNAMEVAR)
    print("Group Name is:", USERGROUP)

    # Get VM State
    vmstatus = CFunc.getvmstate()

    ### Fedora Repos ###
    # RPMFusion
    repo_rpmfusion()
    if not args.nogui:
        # Visual Studio Code
        repo_vscode()

    # Update system after enabling repos.
    CFunc.dnfupdate()

    ### Install Fedora Software ###
    # Cli tools
    CFunc.dnfinstall("fish zsh nano tmux iotop rsync p7zip p7zip-plugins zip unzip xdg-utils xdg-user-dirs util-linux-user fuse-sshfs redhat-lsb-core openssh-server openssh-clients avahi nss-mdns dnf-plugin-system-upgrade xfsprogs python3-pip")
    CFunc.dnfinstall("unrar")
    CFunc.sysctl_enable("sshd", error_on_fail=True)
    CFunc.dnfinstall("powerline-fonts google-roboto-fonts google-noto-sans-fonts")
    # Samba
    CFunc.dnfinstall("samba")
    CFunc.sysctl_enable("smb", error_on_fail=True)
    # cifs-utils
    CFunc.dnfinstall("cifs-utils")
    # NTP Configuration
    CFunc.sysctl_enable("systemd-timesyncd", error_on_fail=True)
    subprocess.run("timedatectl set-local-rtc false; timedatectl set-ntp 1", shell=True, check=True)
    # firewalld
    CFunc.dnfinstall("firewalld")
    CFunc.sysctl_enable("firewalld", now=True, error_on_fail=True)
    CFuncExt.FirewalldConfig()
    # Podman
    CFunc.dnfinstall("podman")
    # GUI Packages
    if not args.nogui:
        # Toolbox
        CFunc.dnfinstall("toolbox")
        # Base Packages
        CFunc.dnfinstall("@fonts @base-x @networkmanager-submodules xrandr xset")
        # Browsers
        # Official Google Chrome
        # CFunc.dnfinstall("https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm")
        CFunc.dnfinstall("@firefox")
        # Cups
        CFunc.dnfinstall("cups-pdf")
        # Remote access
        CFunc.dnfinstall("remmina remmina-plugins-vnc remmina-plugins-rdp")
        # Multimedia
        CFunc.dnfinstall("@multimedia")
        CFunc.dnfinstall("gstreamer1-vaapi")
        CFunc.dnfinstall("ffmpeg smplayer mpv")
        CFuncExt.ytdlp_install()
        # Editors
        CFunc.dnfinstall("codium")
        # Syncthing
        CFunc.dnfinstall("syncthing")
        # Flameshot
        CFunc.dnfinstall("flameshot")
        os.makedirs(os.path.join(USERHOME, ".config", "autostart"), exist_ok=True)
        # Start flameshot on user login.
        shutil.copy(os.path.join(os.sep, "usr", "share", "applications", "org.flameshot.Flameshot.desktop"), os.path.join(USERHOME, ".config", "autostart"))
        CFunc.chown_recursive(os.path.join(USERHOME, ".config", ), USERNAMEVAR, USERGROUP)

    # Install software for VMs
    if vmstatus == "kvm":
        CFunc.dnfinstall("spice-vdagent qemu-guest-agent")
    if vmstatus == "vbox":
        CFunc.dnfinstall("virtualbox-guest-additions")
    if vmstatus == "vmware":
        CFunc.dnfinstall("open-vm-tools")
        if not args.nogui:
            CFunc.dnfinstall("open-vm-tools-desktop")

    # Install Desktop Software
    if args.desktop == "gnome":
        # Gnome
        CFunc.dnfinstall("--allowerasing @workstation-product @gnome-desktop")
        CFunc.sysctl_enable("-f gdm", error_on_fail=True)
        # Tilix
        CFunc.dnfinstall("tilix tilix-nautilus")
        # Some Gnome Extensions
        CFunc.dnfinstall("gnome-terminal-nautilus gnome-tweak-tool dconf-editor")
        CFunc.dnfinstall("gnome-shell-extension-gpaste gnome-shell-extension-topicons-plus")
        # Install gs installer script.
        gs_installer = CFunc.downloadfile("https://raw.githubusercontent.com/brunelli/gnome-shell-extension-installer/master/gnome-shell-extension-installer", os.path.join(os.sep, "usr", "local", "bin"), overwrite=True)
        os.chmod(gs_installer[0], 0o777)
        # Dash to panel
        CFunc.run_as_user(USERNAMEVAR, "{0} --yes 1160".format(gs_installer[0]))
        # https://github.com/kgshank/gse-sound-output-device-chooser
        CFunc.run_as_user(USERNAMEVAR, "{0} --yes 906".format(gs_installer[0]))
        # https://github.com/mymindstorm/gnome-volume-mixer
        CFunc.run_as_user(USERNAMEVAR, "{0} --yes 3499".format(gs_installer[0]))
        # Kstatusnotifier
        CFunc.run_as_user(USERNAMEVAR, "{0} --yes 615".format(gs_installer[0]))
        # Extensions app
        CFunc.flatpak_install("flathub", "org.gnome.Extensions")
    elif args.desktop == "kde":
        # KDE
        CFunc.dnfinstall("--allowerasing @kde-desktop-environment")
        CFunc.dnfinstall("ark")
        CFunc.sysctl_enable("-f sddm", error_on_fail=True)
    elif args.desktop == "mate":
        # MATE
        CFunc.dnfinstall("--allowerasing @mate-desktop @mate-applications")
        CFunc.sysctl_enable("-f lightdm", error_on_fail=True)
        # Tilix
        CFunc.dnfinstall("tilix tilix-nautilus")
        # Applications
        CFunc.dnfinstall("dconf-editor")
        # Brisk-menu
        subprocess.run("dnf copr enable -y rmkrishna/rpms", shell=True, check=True)
        CFunc.dnfinstall("brisk-menu")
        # Run MATE Configuration
        subprocess.run("{0}/DExtMate.py".format(SCRIPTDIR), shell=True, check=False)
    elif args.desktop == "xfce":
        CFunc.dnfinstall("--allowerasing @xfce-desktop-environment")
        CFunc.dnfinstall("xfce4-whiskermenu-plugin xfce4-systemload-plugin xfce4-diskperf-plugin xfce4-clipman-plugin")
        # Tilix
        CFunc.dnfinstall("tilix tilix-nautilus")
    elif args.desktop == "lxqt":
        CFunc.dnfinstall("--allowerasing @lxqt-desktop-environment")
    elif args.desktop == "cinnamon":
        CFunc.dnfinstall("--allowerasing @cinnamon-desktop-environment")

    if not args.nogui:
        # Numix
        CFunc.dnfinstall("numix-icon-theme-circle")
        # Update pixbuf cache after installing icons (for some reason doesn't do this automatically).
        subprocess.run("gdk-pixbuf-query-loaders-64 --update-cache", shell=True, check=True)
        # Enable graphical target
        subprocess.run("systemctl set-default graphical.target", shell=True, check=True)

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
    CFunc.AddUserToGroup("kvm")
    CFunc.AddUserToGroup("systemd-journal")
    CFunc.AddUserToGroup("systemd-network")
    CFunc.AddUserToGroup("systemd-resolve")
    CFunc.AddUserToGroup("systemd-timesync")
    CFunc.AddUserToGroup("pipewire")
    CFunc.AddUserToGroup("colord")
    CFunc.AddUserToGroup("nm-openconnect")
    CFunc.AddUserToGroup("vboxsf")

    # Sudoers changes
    CFuncExt.SudoersEnvSettings()
    # Edit sudoers to add dnf.
    fedora_sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("dnf")))
    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("podman")))

    # Hdparm
    CFunc.dnfinstall("smartmontools hdparm")

    if not args.nogui:
        # Flatpak setup
        CFunc.dnfinstall("flatpak xdg-desktop-portal")
        CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("flatpak")))

    # Plymouth and grub
    subprocess.run("plymouth-set-default-theme spinner -R", shell=True, check=True)
    grub_config = os.path.join(os.sep, "etc", "default", "grub")
    # Comment grub console
    subprocess.run("sed -i '/GRUB_CONSOLE/ s/^#*/#/' {0}".format(grub_config), shell=True, check=True)
    # Disable Selinux
    # To get selinux status: sestatus, getenforce
    CFuncExt.GrubEnvAdd(grub_config, "GRUB_CMDLINE_LINUX", "selinux=0")
    # Disable mitigations
    CFuncExt.GrubEnvAdd(grub_config, "GRUB_CMDLINE_LINUX", "mitigations=off")
    CFuncExt.GrubUpdate()

    # Extra scripts
    subprocess.run(os.path.join(SCRIPTDIR, "CCSClone.py"), shell=True, check=True)
    if not args.nogui:
        subprocess.run(os.path.join(SCRIPTDIR, "CFlatpakConfig.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Csshconfig.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CShellConfig.py") + " -f -z -d", shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CDisplayManagerConfig.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CVMGeneral.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Cxdgdirs.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Czram.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CSysConfig.sh"), shell=True, check=True)

    print("\nScript End")
