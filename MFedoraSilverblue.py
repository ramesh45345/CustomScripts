#!/usr/bin/env python3
"""Install Fedora Software"""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
import time
# Custom includes
import CFunc
import CFuncExt

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]


### Functions ###
def rostreeupdate():
    """Update system"""
    print("\nPerforming system update.")
    subprocess.run("rpm-ostree upgrade", shell=True, check=True)
def rostreeinstall(apps):
    """Install application(s) using rpm-ostree"""
    status = None
    print("\nInstalling {0} using rpm-ostree.".format(apps))
    status = subprocess.run("rpm-ostree install --idempotent --allow-inactive {0}".format(apps), shell=True, check=True).returncode
    return status
def systemd_resostreed():
    """Restart the rpm-ostreed service. This is needed in case it is doing something during this script operation, which would prevent the script from running. Restart the service before rpm-ostree operations."""
    subprocess.run("systemctl restart rpm-ostreed", shell=True, check=True)
    time.sleep(1)
def group_addtosystem(group: str):
    """If a group is in /usr/lib/group, and not in /etc/group, add it to /etc/group."""
    group_path_libgroup = os.path.join(os.sep, "usr", "lib", "group")
    group_path_etcgroup = os.path.join(os.sep, "etc", "group")
    group_exists_libgroup = False
    group_exists_etcgroup = False
    # Check if group exists in /usr/lib/group.
    with open(group_path_libgroup, 'r') as f:
        libgroup_lines = f.readlines()
        for line in libgroup_lines:
            if line.startswith(group + ":"):
                group_exists_libgroup = True
    # Check if group exists in /etc/group.
    with open(group_path_etcgroup, 'r') as f:
        etcgroup_lines = f.readlines()
        for line in etcgroup_lines:
            if line.startswith(group + ":"):
                group_exists_etcgroup = True
    # If group is in /usr/lib/group, and not in /etc/group, add it to /etc/group.
    if group_exists_libgroup is True and group_exists_etcgroup is False:
        print("Adding group {0} to {1}.".format(group, group_path_etcgroup))
        subprocess.run("grep -E '^{0}:' {1} >> {2}".format(group, group_path_libgroup, group_path_etcgroup), shell=True, check=True)
    elif group_exists_libgroup is True and group_exists_etcgroup is True:
        print("Group {0} already added to {1}. Skipping.".format(group, group_path_etcgroup))
    elif group_exists_libgroup is False:
        print("WARNING: Group {0} not in {1}. Skipping.".format(group, group_path_libgroup))
def group_silverblueadd(group: str):
    """Add group to /etc/group, and add user to group."""
    group_addtosystem(group)
    CFunc.AddUserToGroup(group)


# Get arguments
parser = argparse.ArgumentParser(description='Install Fedora Silverblue Software.')
parser.add_argument("-s", "--stage", help='Stage of installation to run (1 or 2).', type=int, default=0)

# Save arguments.
args = parser.parse_args()
print("Stage:", args.stage)

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)

# Get VM State
vmstatus = CFunc.getvmstate()


### Begin Code ###
fedora_sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
if args.stage == 0:
    print("Please select a stage.")
if args.stage == 1:
    print("Stage 1")
    systemd_resostreed()

    ### Fedora Repos ###
    # RPMFusion
    rostreeinstall("https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm")

    # Update system.
    rostreeupdate()

    ### OSTree Apps ###
    # Cli tools
    rostreeinstall("fish zsh tmux iotop p7zip p7zip-plugins util-linux-user fuse-sshfs redhat-lsb-core powerline-fonts google-roboto-fonts google-noto-sans-fonts samba smartmontools hdparm cups-pdf pulseaudio-module-zeroconf paprefs tilix tilix-nautilus syncthing numix-icon-theme numix-icon-theme-circle")
    subprocess.run("systemctl enable sshd", shell=True, check=True)
    # NTP Configuration
    subprocess.run("systemctl enable systemd-timesyncd; timedatectl set-local-rtc false; timedatectl set-ntp 1", shell=True, check=True)

    # Install software for VMs
    if vmstatus == "vbox":
        rostreeinstall("virtualbox-guest-additions virtualbox-guest-additions-ogl")
    if vmstatus == "vmware":
        rostreeinstall("open-vm-tools open-vm-tools-desktop")

    # Some Gnome Extensions
    rostreeinstall("gnome-tweak-tool dconf-editor")
    rostreeinstall("gnome-shell-extension-gpaste gnome-shell-extension-topicons-plus")

    # Sudoers changes
    CFuncExt.SudoersEnvSettings()
    # Edit sudoers to add dnf.
    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("rpm-ostree")))
    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("podman")))

    # Install snapd
    rostreeinstall("snapd")

    # Flatpak setup
    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("flatpak")))
    subprocess.run('chmod -R "ugo=rwX" /var/lib/flatpak/', shell=True, check=True)

    # Disable Selinux
    # To get selinux status: sestatus, getenforce
    subprocess.run("rpm-ostree kargs --append=selinux=0", shell=True, check=True)

    # firewalld
    CFunc.sysctl_enable("firewalld", now=True, error_on_fail=True)
    CFuncExt.FirewalldConfig()

    # Disable mitigations
    subprocess.run("rpm-ostree kargs --append=mitigations=off", shell=True, check=True)
    print("Stage 1 Complete! Please reboot and run Stage 2.")
if args.stage == 2:
    print("Stage 2")
    systemd_resostreed()
    rostreeinstall("rpmfusion-nonfree-appstream-data rpmfusion-free-appstream-data")
    rostreeinstall("rpmfusion-free-release-tainted rpmfusion-nonfree-release-tainted")
    subprocess.run("systemctl enable smb", shell=True, check=True)

    # Media apps
    rostreeinstall("youtube-dl mpv smplayer")

    # VSCode
    with open("/etc/yum.repos.d/vscode.repo", 'w') as f:
        f.write("""[code]
name=Visual Studio Code
baseurl=https://packages.microsoft.com/yumrepos/vscode
enabled=1
gpgcheck=0""")
    rostreeinstall("code")

    # Install gs installer script.
    gs_installer = CFunc.downloadfile("https://raw.githubusercontent.com/brunelli/gnome-shell-extension-installer/master/gnome-shell-extension-installer", os.path.join(os.sep, "usr", "local", "bin"), overwrite=True)
    os.chmod(gs_installer[0], 0o777)
    # Install volume extension
    CFunc.run_as_user(USERNAMEVAR, "{0} --yes 858".format(gs_installer[0]))
    # Install dashtodock extension
    CFunc.run_as_user(USERNAMEVAR, "{0} --yes 307".format(gs_installer[0]))

    CFunc.AddLineToSudoersFile(fedora_sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("snap")))

    # Add normal user to all reasonable groups
    group_silverblueadd("disk")
    group_silverblueadd("lp")
    group_silverblueadd("wheel")
    group_silverblueadd("cdrom")
    group_silverblueadd("man")
    group_silverblueadd("dialout")
    group_silverblueadd("floppy")
    group_silverblueadd("games")
    group_silverblueadd("tape")
    group_silverblueadd("video")
    group_silverblueadd("audio")
    group_silverblueadd("input")
    group_silverblueadd("kvm")
    group_silverblueadd("systemd-journal")
    group_silverblueadd("systemd-network")
    group_silverblueadd("systemd-resolve")
    group_silverblueadd("systemd-timesync")
    group_silverblueadd("pipewire")
    group_silverblueadd("colord")
    group_silverblueadd("nm-openconnect")
    group_silverblueadd("vboxsf")

    # Flatpak apps
    subprocess.run(os.path.join(SCRIPTDIR, "CFlatpakConfig.py"), shell=True, check=True)
    # Flameshot
    CFunc.flatpak_install("flathub", "org.flameshot.Flameshot")
    os.makedirs(os.path.join(USERHOME, ".config", "autostart"), exist_ok=True)
    # Start flameshot on user login.
    shutil.copy("/var/lib/flatpak/app/org.flameshot.Flameshot/current/active/export/share/applications/org.flameshot.Flameshot.desktop", os.path.join(USERHOME, ".config", "autostart"))
    CFunc.chown_recursive(os.path.join(USERHOME, ".config", ), USERNAMEVAR, USERGROUP)

    # Extra scripts
    subprocess.run("{0}/CCSClone.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/Csshconfig.sh".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/CShellConfig.py -f -z -d".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/CDisplayManagerConfig.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/CVMGeneral.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/Cxdgdirs.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/Czram.py".format(SCRIPTDIR), shell=True, check=True)
    subprocess.run("{0}/CSysConfig.sh".format(SCRIPTDIR), shell=True, check=True)
    print("Stage 2 complete! Please reboot.")

print("\nScript End")
