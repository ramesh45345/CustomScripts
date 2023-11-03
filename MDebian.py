#!/usr/bin/env python3
"""Install Debian Software"""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
# Custom includes
import CFunc
import CFuncExt

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Exit if not root.
CFunc.is_root(True)


### Functions ###
def vscode_deb():
    """Install vscode deb and repository."""
    subprocess.run("""curl https://gitlab.com/paulcarroty/vscodium-deb-rpm-repo/raw/master/pub.gpg | gpg --dearmor > /tmp/vscodium-archive-keyring.gpg
    mv /tmp/vscodium-archive-keyring.gpg /etc/apt/trusted.gpg.d/vscodium-archive-keyring.gpg""", shell=True, check=True)
    # Install repo
    subprocess.run('echo "deb [ signed-by=/etc/apt/trusted.gpg.d/vscodium-archive-keyring.gpg ] https://paulcarroty.gitlab.io/vscodium-deb-rpm-repo/debs vscodium main" > /etc/apt/sources.list.d/vscodium.list', shell=True, check=True)
    CFunc.aptupdate()
    CFunc.aptinstall("codium")
def kernel_liquorix():
    """Install liquorix kernel."""
    tempfolder = tempfile.gettempdir()
    liquorix_script_file = CFunc.downloadfile("https://liquorix.net/install-liquorix.sh", tempfolder)[0]
    os.chmod(liquorix_script_file, 0o777)
    subprocess.run(liquorix_script_file, shell=True, check=True, executable=shutil.which("bash"))
def mpr_install(normaluser: str):
    """Install mpr and mist tool."""
    # Install makedeb
    subprocess.run("wget -qO - 'https://proget.makedeb.org/debian-feeds/makedeb.pub' | gpg --dearmor | sudo tee /usr/share/keyrings/makedeb-archive-keyring.gpg 1> /dev/null", shell=True, check=True)
    subprocess.run("echo 'deb [signed-by=/usr/share/keyrings/makedeb-archive-keyring.gpg arch=all] https://proget.makedeb.org/ makedeb main' | sudo tee /etc/apt/sources.list.d/makedeb.list", shell=True, check=True)
    CFunc.aptupdate()
    CFunc.aptinstall("makedeb")
    # # Install rustup (for mist)
    # print("Installing rustup")
    # subprocess.run("curl -sSf https://sh.rustup.rs | sh -s -- -y", shell=True, check=True)
    # # Install mist
    # tempfolder = tempfile.gettempdir()
    # CFunc.gitclone("https://mpr.makedeb.org/mist.git", os.path.join(tempfolder, "mist"))
    # CFunc.chmod_recursive(os.path.join(tempfolder, "mist"), 0o777)
    # CFunc.run_as_user_su(normaluser, "cd {0}; makedeb -si -H 'MPR-Package: yes' --no-confirm".format(os.path.join(tempfolder, "mist")), error_on_fail=True)


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Install Debian Software.')
    parser.add_argument("-d", "--desktop", help='Desktop Environment (i.e. gnome, kde, mate, etc)')
    parser.add_argument("-u", "--unstable", help='Upgrade to unstable.', action="store_true")
    parser.add_argument("-x", "--nogui", help='Configure script to disable GUI.', action="store_true")

    # Save arguments.
    args = parser.parse_args()
    print("Desktop Environment:", args.desktop)
    print("Unstable Mode:", args.unstable)
    print("No GUI:", args.nogui)

    # Get non-root user information.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
    MACHINEARCH = CFunc.machinearch()
    print("Username is:", USERNAMEVAR)
    print("Group Name is:", USERGROUP)

    # Check if root password is set.
    rootacctstatus = CFunc.subpout("passwd -S root | awk '{{print $2}}'")
    if "P" not in rootacctstatus:
        print("Please set the root password.")
        subprocess.run("passwd root", shell=True, check=False)
        print("Please rerun this script now that the root account is unlocked.")
        sys.exit(1)

    # Select debian url
    URL = "http://http.us.debian.org/debian"
    print("Debian Mirror URL is {0}".format(URL))

    # Get VM State
    vmstatus = CFunc.getvmstate()

    # Set non-interactive flag
    os.environ['DEBIAN_FRONTEND'] = "noninteractive"

    ### Begin Code ###
    # Get Debian Release
    CFunc.aptupdate()
    CFunc.aptinstall("lsb-release software-properties-common apt-transport-https gnupg")
    # Needed for add-apt-repositories
    CFunc.aptinstall("python3-lazr.restfulclient python3-lazr.uri")
    # Detect OS information
    distro, debrelease = CFunc.detectdistro()
    print("Distro is {0}.".format(distro))
    print("Release is {0}.".format(debrelease))

    ### Set up Debian Repos ###
    # Change to unstable.
    if args.unstable:
        debrelease = "sid"
        print("\n Enable unstable repositories.")
        with open('/etc/apt/sources.list', 'w') as writefile:
            writefile.write('deb {0} sid main contrib non-free'.format(URL))
        CFunc.aptupdate()
    # Main, Contrib, Non-Free for Debian.
    subprocess.run("""
add-apt-repository -y main
add-apt-repository -y contrib
add-apt-repository -y non-free
    """, shell=True, check=True)
    # Make non-free-firmware unconditional when stable becomes bookworm.
    if debrelease != "bullseye":
        subprocess.run("add-apt-repository -y non-free-firmware", shell=True, check=True)

    # Comment out lines containing httpredir.
    subprocess.run("sed -i '/httpredir/ s/^#*/#/' /etc/apt/sources.list", shell=True, check=True)

    # Add timeouts for repository connections
    with open('/etc/apt/apt.conf.d/99timeout', 'w') as writefile:
        writefile.write('''Acquire::http::Timeout "5";
Acquire::https::Timeout "5";
Acquire::ftp::Timeout "5";''')

    # Update and upgrade with new base repositories
    CFunc.aptupdate()
    CFunc.aptdistupg()

    ### Software ###
    # Debian Multimedia
    # Write sources list
    if args.unstable:
        multimedia_release = "sid"
    else:
        multimedia_release = debrelease
    with open('/etc/apt/sources.list.d/debian-multimedia.list', 'w') as stapt_writefile:
        stapt_writefile.write("deb https://www.deb-multimedia.org {0} main non-free".format(multimedia_release))
    subprocess.run("apt-get update -oAcquire::AllowInsecureRepositories=true", shell=True, check=True)
    subprocess.run("apt-get install -y --allow-unauthenticated deb-multimedia-keyring -oAcquire::AllowInsecureRepositories=true", shell=True, check=True)

    # Update and upgrade with new repositories
    CFunc.aptupdate()
    CFunc.aptdistupg()

    # Cli Software
    CFunc.aptinstall("ssh tmux zsh fish btrfs-progs f2fs-tools xfsprogs dmraid mdadm nano p7zip-full p7zip-rar unrar curl wget rsync less iotop sshfs sudo python-is-python3 nala")
    # Firmware
    CFunc.aptinstall("firmware-linux")
    subprocess.run("""echo "firmware-ipw2x00 firmware-ipw2x00/license/accepted boolean true" | debconf-set-selections
echo "firmware-ivtv firmware-ivtv/license/accepted boolean true" | debconf-set-selections""", shell=True, check=True)
    subprocess.run("""DEBIAN_FRONTEND=noninteractive apt install -y bluez-firmware firmware-amd-graphics firmware-atheros firmware-brcm80211 firmware-intel-sound firmware-ipw2x00 firmware-iwlwifi firmware-libertas firmware-misc-nonfree firmware-realtek firmware-zd1211""", shell=True, check=True)
    # Needed for systemd user sessions.
    CFunc.aptinstall("dbus-user-session")
    # Samba
    CFunc.aptinstall("samba cifs-utils")
    # NTP
    CFunc.aptinstall("systemd-timesyncd")
    CFunc.sysctl_enable("systemd-timesyncd")
    subprocess.run(["timedatectl", "set-local-rtc", "false"], check=True)
    subprocess.run(["timedatectl", "set-ntp", "1"], check=True)
    subprocess.run(["timedatectl", "set-timezone", "US/Eastern"], check=True)
    # Avahi
    CFunc.aptinstall("avahi-daemon avahi-discover libnss-mdns")
    # Firewalld
    CFunc.aptinstall("firewalld")
    CFunc.sysctl_enable("firewalld", now=True, error_on_fail=True)
    CFuncExt.FirewalldConfig()
    # Container stuff
    CFunc.aptinstall("podman")

    # Install nix
    CFuncExt.nix_standalone_install(USERNAMEVAR, """
    # Media tools
    mpv""")

    # Sudoers changes
    CFuncExt.SudoersEnvSettings()
    # Edit sudoers to add apt.
    sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
    CFunc.AddLineToSudoersFile(sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
    CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("apt")))
    CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("apt-get")))
    CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("podman")))
    CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("nala")))

    # General GUI software
    if args.nogui is False:
        CFunc.aptinstall("synaptic gnome-disk-utility gdebi gparted xdg-utils")
        CFunc.aptinstall("dconf-cli dconf-editor")
        # Cups-pdf
        CFunc.aptinstall("printer-driver-cups-pdf")
        # Media Playback
        CFunc.aptinstall("ffmpeg")
        CFuncExt.ytdlp_install()
        CFunc.aptinstall("alsa-utils pavucontrol pulseaudio-module-zeroconf pulseaudio-module-bluetooth swh-plugins")
        CFunc.aptinstall("paprefs")
        CFunc.aptinstall("gstreamer1.0-vaapi")
        CFunc.aptinstall("fonts-powerline fonts-noto fonts-roboto")
        # Tilix
        CFunc.aptinstall("tilix")
        # VSCodium
        vscode_deb()
        # Flatpak
        CFunc.aptinstall("flatpak")
        CFunc.flatpak_addremote("flathub", "https://flathub.org/repo/flathub.flatpakrepo")
        CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("flatpak")))
        subprocess.run(os.path.join(SCRIPTDIR, "CFlatpakConfig.py"), shell=True, check=True)
        # Firefox
        CFunc.flatpak_install("flathub", "org.mozilla.firefox")
        CFunc.flatpak_override("org.mozilla.firefox", "--filesystem=host")

    # Network Manager
    CFunc.aptinstall("network-manager network-manager-ssh")
    CFunc.aptinstall("network-manager-config-connectivity-debian")
    subprocess.run("sed -i 's/managed=.*/managed=true/g' /etc/NetworkManager/NetworkManager.conf", shell=True, check=True)
    # https://askubuntu.com/questions/882806/ethernet-device-not-managed
    with open('/etc/NetworkManager/conf.d/10-globally-managed-devices.conf', 'w') as writefile:
        writefile.write("""[keyfile]
    unmanaged-devices=none""")
    # Remove interfaces from /etc/network/interfaces
    with open(os.path.join(os.sep, "etc", "network", "interfaces"), 'w') as writefile:
        writefile.write("""source /etc/network/interfaces.d/*

# The loopback network interface
auto lo
iface lo net loopback
""")
    # Add dns server after installing network manager.
    with open(os.path.join(os.sep, "etc", "resolv.conf"), 'a') as writefile:
        writefile.write("\nnameserver 1.0.0.1\nnameserver 1.1.1.1\nnameserver 2606:4700:4700::1111\nnameserver 2606:4700:4700::1001")

    # Install Desktop Software
    if args.desktop == "gnome":
        print("\n Installing gnome desktop")
        CFunc.aptinstall("task-gnome-desktop")
        CFunc.aptinstall("gnome-clocks")
        CFunc.aptinstall("gnome-shell-extensions gnome-shell-extension-gpaste")
        # Install gs installer script.
        gs_installer = CFunc.downloadfile("https://raw.githubusercontent.com/brunelli/gnome-shell-extension-installer/master/gnome-shell-extension-installer", os.path.join(os.sep, "usr", "local", "bin"), overwrite=True)
        os.chmod(gs_installer[0], 0o777)
        # Dash to panel
        CFunc.run_as_user_su(USERNAMEVAR, "{0} --yes 1160".format(gs_installer[0]))
        # Kstatusnotifier
        CFunc.run_as_user_su(USERNAMEVAR, "{0} --yes 615".format(gs_installer[0]))
    elif args.desktop == "mate":
        print("\n Installing mate desktop")
        CFunc.aptinstall("task-mate-desktop mate-tweak dconf-cli")
        CFunc.aptinstall("mate-applet-brisk-menu")
        # Run MATE Configuration
        subprocess.run("{0}/DExtMate.py".format(SCRIPTDIR), shell=True, check=True)
    elif args.desktop == "kde":
        print("\n Installing kde desktop")
        CFunc.aptinstall("task-kde-desktop")
    elif args.desktop == "xfce":
        print("\n Installing xfce desktop")
        CFunc.aptinstall("task-xfce-desktop")
    elif args.desktop == "lxqt":
        print("\n INstalling lxqt desktop")
        CFunc.aptinstall("task-lxqt-desktop")

    # Post DE install stuff.
    if args.nogui is False:
        # Numix Icon Theme
        CFuncExt.numix_icons(os.path.join(os.sep, "usr", "local", "share", "icons"))

    # Install guest software for VMs
    if vmstatus == "kvm":
        CFunc.aptinstall("spice-vdagent qemu-guest-agent")
    if vmstatus == "vbox":
        CFunc.aptinstall("virtualbox-guest-utils virtualbox-guest-dkms dkms")
        if not args.nogui:
            CFunc.aptinstall("virtualbox-guest-x11")
        subprocess.run("gpasswd -a {0} vboxsf".format(USERNAMEVAR), shell=True, check=True)
        CFunc.sysctl_enable("virtualbox-guest-utils", error_on_fail=True)
    if vmstatus == "vmware":
        CFunc.aptinstall("open-vm-tools open-vm-tools-dkms")
        if not args.nogui:
            CFunc.aptinstall("open-vm-tools-desktop")

    # Disable automatic unattended upgrades
    if os.path.isfile("/etc/apt/apt.conf.d/20auto-upgrades"):
        os.remove("/etc/apt/apt.conf.d/20auto-upgrades")

    # Ensure sbin is in path for grub
    pathvar = os.environ.get('PATH')
    pathvar = pathvar + ":/sbin:/usr/sbin"
    os.environ['PATH'] = pathvar
    # Disable mitigations
    CFuncExt.GrubEnvAdd(os.path.join(os.sep, "etc", "default", "grub"), "GRUB_CMDLINE_LINUX_DEFAULT", "mitigations=off")
    CFuncExt.GrubUpdate()
    # Install liquorix
    kernel_liquorix()

    # Add normal user to all reasonable groups
    CFunc.AddUserToGroup("disk")
    CFunc.AddUserToGroup("lp")
    CFunc.AddUserToGroup("sudo")
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

    # Modify system path
    # https://serverfault.com/questions/166383/how-set-path-for-all-users-in-debian
    logindefs_file = os.path.join("/", "etc", "login.defs")
    if os.path.isfile(logindefs_file):
        print("Modifying {0}".format(logindefs_file))
        if CFunc.find_pattern_infile(logindefs_file, "ENV_PATH.*PATH.*sbin") is False:
            subprocess.run("""sed -i '/^ENV_PATH.*PATH.*/ s@$@:/sbin:/usr/sbin:/usr/local/sbin@' {0}""".format(logindefs_file), shell=True, check=True)

    # Extra scripts
    subprocess.run(os.path.join(SCRIPTDIR, "CShellConfig.py") + " -f -z -d", shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CCSClone.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Csshconfig.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CDisplayManagerConfig.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CVMGeneral.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Cxdgdirs.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "Czram.py"), shell=True, check=True)
    subprocess.run(os.path.join(SCRIPTDIR, "CSysConfig.sh"), shell=True, check=True)

    print("\nScript End")
