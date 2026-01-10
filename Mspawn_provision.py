#!/usr/bin/env python3
"""Provision systemd-nspawn chroot."""

# Python includes.
import argparse
import os
import shutil
import subprocess
# Custom includes
import CFunc
import CFuncExt

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Global variables
distro_options = ["arch", "ubuntu", "fedora"]
distro_default = "arch"

# Get arguments
parser = argparse.ArgumentParser(description='Provision systemd-nspawn chroot.')
parser.add_argument("-b", "--bootable", help='Provision for booting.', action="store_true")
parser.add_argument("-d", "--distro", help='Distribution of Linux (default: %(default)s)', default=distro_default, choices=distro_options)
parser.add_argument("--hostname", help='Hostname of machine. (default: %(default)s)', default="chroot")
parser.add_argument("--user", help='Username (default: %(default)s)', default="user", type=str)
parser.add_argument("--group", help='Group name (default: %(default)s)', default="user", type=str)
parser.add_argument("--uid", help='Username (default: %(default)s)', default=1000, type=int)
parser.add_argument("--gid", help='Group name (default: %(default)s)', default=1000, type=int)
parser.add_argument("--password", help='Username (default: %(default)s)', default="asdf", type=str)
parser.add_argument("--sshkey", help='SSH authorization key.', type=str)

# Save arguments.
args = parser.parse_args()

# Exit if not root.
CFunc.is_root(True)

# Print details
print("Distro:", args.distro)
print("Hostname of chroot: {0}".format(args.hostname))
print("Username is:", args.user)
print("Group Name is:", args.group)


### Begin Code ###

# Import support libs
if args.distro == "arch":
    import MArch
    CFunc.commands_check(["pacman"])
if args.distro == "ubuntu":
    import MDebian
    import MUbuntu
    CFunc.commands_check(["apt-get"])
if args.distro == "fedora":
    import MFedora
    CFunc.commands_check(["dnf"])

# Create group and user
subprocess.run(["groupadd", args.group, "-g", str(args.gid), "-f"], check=False)
subprocess.run(["useradd", "-m", "--shell=/bin/bash", args.user, "-u", str(args.uid), "-g", str(args.gid)], check=False)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()

# Install basic packages
if args.distro == "arch":
    subprocess.run("sed -i 's/^#ParallelDownloads/ParallelDownloads/g' /etc/pacman.conf", shell=True, check=True)
    CFunc.pacman_install("nano sudo which git zsh python python-pip base-devel")
    MArch.pacman_update()
if args.distro == "ubuntu":
    # Get Ubuntu Release
    CFunc.aptupdate()
    CFunc.aptinstall("lsb-release software-properties-common apt-transport-https")
    # Detect OS information
    distro, debrelease = CFunc.detectdistro()
    # Setup ubuntu repos
    MUbuntu.ubuntu_repos_setup(distrorelease=debrelease)
    CFunc.aptupdate()
    CFunc.aptdistupg()
    CFunc.aptinstall("sudo passwd libcap2-bin zsh git nano python3 iproute2 iputils-ping wget curl build-essential")
if args.distro == "fedora":
    CFunc.dnfupdate()
    CFunc.dnfinstall("sudo bash zsh nano git util-linux-user passwd binutils wget iputils dbus-tools glibc-langpack-en")
    MFedora.repo_rpmfusion()

# Add nopasswd entry for sudo.
sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "custom")
CFunc.AddLineToSudoersFile(sudoersfile, r"%wheel ALL=(ALL) NOPASSWD: ALL", overwrite=True)
CFunc.AddLineToSudoersFile(sudoersfile, r"%sudo ALL=(ALL) NOPASSWD: ALL")
CFuncExt.SudoersEnvSettings()

# Set hostname
with open("/etc/hostname", 'w') as f:
    f.write(args.hostname)
subprocess.run('grep -q -e "127.0.0.1 {0}" /etc/hosts || echo "127.0.0.1 {0}" >> /etc/hosts'.format(args.hostname), shell=True, check=True)

# Locales
with open("/etc/locale.gen", 'w') as f:
    f.write("en_US.UTF-8 UTF-8\n")
subprocess.run("""echo 'LANG="en_US.UTF-8"' | tee /etc/default/locale /etc/locale.conf""", shell=True, check=True)
if args.distro == "arch" or args.distro == "ubuntu":
    subprocess.run(["locale-gen", "--purge", "en_US", "en_US.UTF-8"], check=True)
if args.distro == "ubuntu":
    subprocess.run("dpkg-reconfigure --frontend=noninteractive locales && update-locale", shell=True, check=True)

# Groups
CFunc.AddUserToGroup("wheel", USERNAMEVAR)
CFunc.AddUserToGroup("sudo", USERNAMEVAR)
# Scripts
if not os.path.isdir(os.path.join(os.sep, "opt", "CustomScripts")):
    subprocess.run("chmod a+rwx /opt && git clone https://github.com/ramesh45345/CustomScripts /opt/CustomScripts", check=True, shell=True)
else:
    subprocess.run("cd /opt/CustomScripts && git pull", check=True, shell=True)
subprocess.run("chown -R {0}:{1} /opt/CustomScripts".format(USERNAMEVAR, USERGROUP), check=True, shell=True)
subprocess.run(['/opt/CustomScripts/CShellConfig.py', '-z', '-d'], check=True)
subprocess.run("""echo 'cd $HOME' | tee -a ~{0}/.zshrc ~{0}/.bashrc""".format(USERNAMEVAR), shell=True, check=True)

# Create ssh authorized_keys
os.makedirs("/root/.ssh/", exist_ok=True)
os.makedirs(os.path.join(USERHOME, ".ssh"), exist_ok=True)
with open("/root/.ssh/authorized_keys", 'w') as f:
    f.write(args.sshkey)
with open(os.path.join(USERHOME, ".ssh", "authorized_keys"), 'w') as f:
    f.write(args.sshkey)
CFunc.chown_recursive(os.path.join(USERHOME, ".ssh"), USERNAMEVAR, USERGROUP)

# Gui apps
if args.distro == "arch":
    CFunc.pacman_install("xfce4-terminal noto-fonts ttf-ubuntu-font-family")
    # Yay
    if not shutil.which("yay"):
        MArch.install_aur_pkg("yay-bin", USERNAMEVAR, USERGROUP)
if args.distro == "ubuntu":
    CFunc.aptinstall("xserver-xorg fonts-powerline fonts-liberation fonts-liberation2 fonts-dejavu xfce4-terminal")
if args.distro == "fedora":
    CFunc.dnfinstall("--allowerasing @fonts @base-x xdg-utils xterm powerline-fonts xfce4-terminal")

# Set password
subprocess.run(['chpasswd'], input=bytes("{0}:{1}".format(USERNAMEVAR, args.password), 'utf-8'), check=True)
subprocess.run(['chpasswd'], input=bytes("root:{0}".format(args.password), 'utf-8'), check=True)

# Bootable logic
if args.bootable:
    # Network tools
    if args.distro == "arch":
        CFunc.pacman_install("networkmanager openssh avahi")
        CFunc.sysctl_enable("NetworkManager avahi-daemon sshd")
    if args.distro == "ubuntu":
        CFunc.aptinstall("ssh avahi-daemon avahi-discover libnss-mdns binutils util-linux iputils-ping iproute2 network-manager network-manager-ssh resolvconf")
        subprocess.run("sed -i 's/managed=.*/managed=true/g' /etc/NetworkManager/NetworkManager.conf", shell=True, check=True)
        with open('/etc/NetworkManager/conf.d/10-globally-managed-devices.conf', 'w') as writefile:
            writefile.write("""[keyfile]
unmanaged-devices=none""")
    if args.distro == "fedora":
        CFunc.dnfinstall("@networkmanager-submodules avahi nss-mdns openssh openssh-clients openssh-server passwd binutils util-linux-user tigervnc-server dnf-plugins-core iputils iproute xrdp xorgxrdp")

    # Install GUI
    if args.distro == "arch":
        CFunc.pacman_install("mate-panel mate-session-manager mate-control-center marco xdg-utils dconf-editor epiphany pluma caja caja-open-terminal ptyxis mate-terminal mate-themes mate-polkit xdg-user-dirs ttf-roboto noto-fonts ttf-liberation tigervnc")
        MArch.yay_install(USERNAMEVAR, "xrdp xorgxrdp brisk-menu numix-circle-icon-theme-git")
    if args.distro == "ubuntu":
        held_pkgs = "gnome-shell gdm3 gnome-session gnome-session-bin ubuntu-session gnome-control-center cheese"
        CFunc.aptmark(held_pkgs)
        CFunc.aptinstall("mate-desktop-environment marco mate-polkit mate-menus mate-terminal mate-applet-appmenu mate-applet-brisk-menu mate-tweak xdg-utils dconf-editor epiphany pluma caja caja-open-terminal mate-terminal mate-themes fonts-roboto fonts-noto-extra fonts-noto-ui-extra fonts-liberation2 numix-icon-theme numix-icon-theme-circle gnome-icon-theme network-manager-gnome tigervnc-viewer tigervnc-standalone-server tigervnc-xorg-extension xrdp xorgxrdp")
        MDebian.vscode_deb()
    if args.distro == "fedora":
        CFunc.dnfinstall("mate-panel mate-session-manager mate-control-center marco")
        MFedora.repo_vscode()
        subprocess.run("dnf copr enable -y rmkrishna/rpms", shell=True, check=True)
        CFunc.dnfupdate()
        CFunc.dnfinstall("xdg-utils dconf-editor brisk-menu epiphany pluma caja caja-open-terminal mate-terminal mate-themes google-roboto-fonts google-noto-sans-fonts liberation-mono-fonts numix-icon-theme numix-icon-theme-circle codium")
    subprocess.run(["/opt/CustomScripts/DExtMate.py"], check=True)
    # vscode setup
    if args.distro == "ubuntu" or args.distro == "fedora":
        CFunc.run_as_user(USERNAMEVAR, os.path.join(SCRIPTDIR, "Cvscode.py"), shutil.which("bash"), error_on_fail=True)

    # Desktop configuration
    with open("/etc/xdg/autostart/mate-dset.desktop", 'w') as f:
        f.write(r"""[Desktop Entry]
Name=Dset
Exec=/opt/CustomScripts/Dset.py -p
Terminal=false
Type=Application""")
    with open("/etc/xdg/autostart/csupdate.desktop", 'w') as f:
        f.write(r"""[Desktop Entry]
Name=csupdate
Exec=/bin/bash -c "cd /opt/CustomScripts; git pull"
Terminal=false
Type=Application""")
    subprocess.run(["/opt/CustomScripts/Cxdgdirs.py"], check=True)

    # VNC Config
    subprocess.run("mkdir -p {2}/.vnc && chown {0}:{1} -R {2} && echo 'asdf' | vncpasswd -f | tee /etc/vncpasswd".format(USERNAMEVAR, USERGROUP, USERHOME), shell=True, check=True)
    with open("/etc/tigervnc/vncserver.users", 'w') as f:
        f.write(":1={0}\n".format(USERNAMEVAR))
    with open(os.path.join(USERHOME, ".vnc", "config"), 'w') as f:
        f.write("""session=mate
securitytypes=none
desktop=ct-desktop
geometry=1600x900
# localhost
alwaysshared
auth=~/.Xauthority
rfbport=5901""")
    with open(os.path.join(USERHOME, ".xsession"), 'w') as f:
        f.write("exec mate-session\n")
    CFunc.chown_recursive(os.path.join(USERHOME, ".xsession"), USERNAMEVAR, USERGROUP)
    subprocess.run("chmod 700 {0}/.xsession".format(USERHOME), shell=True, check=True)
    if args.distro == "arch" or args.distro == "fedora":
        CFunc.sysctl_enable(r"vncserver@:1")
    if args.distro == "ubuntu":
        CFunc.sysctl_enable(r"tigervncserver@:1")

print("\nScript End")
