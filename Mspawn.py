#!/usr/bin/env python3
"""Install systemd-nspawn chroot."""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]

# Global variables
distro_options = ["arch", "ubuntu", "fedora"]
ubuntu_version = "hirsute"
fedora_version = "34"


### Functions ###
def check_cmds():
    """Ensure that certain commands exist."""
    cmdcheck = ["systemd-nspawn"]
    for cmd in cmdcheck:
        if not shutil.which(cmd):
            sys.exit("\nError, ensure command {0} is installed.".format(cmd))
def ctr_detect():
    """Detect if podman or docker is on machine."""
    cmd = None
    if shutil.which("podman"):
        cmd = "podman"
    elif shutil.which("docker"):
        cmd = "docker"
    else:
        sys.exit("\nError, ensure podman or docker is installed.")
    return cmd
def ctr_create(ctrimage: str, path: str, cmd: str):
    """Run a chroot create command using a container runtime."""
    ctr_cmd = ctr_detect()
    full_cmd = [ctr_cmd, "run", "--rm", "--privileged", "-it", "--volume={0}:/chrootfld".format(path), "--name=chrootsetup", ctrimage, "bash", "-c", cmd]
    print("Running {0}".format(full_cmd))
    subprocess.run(full_cmd, check=True)
def create_chroot(distro: str, path: str):
    """Create a chroot."""
    print("Creating {0} at {1}".format(distro, path))
    os.makedirs(path, exist_ok=False)
    # Arch
    if args.distro == distro_options[0]:
        ctr_create("docker.io/library/archlinux:latest", path, "sed -i 's/^#ParallelDownloads/ParallelDownloads/g' /etc/pacman.conf && pacman -Sy --noconfirm --needed arch-install-scripts && pacstrap -c /chrootfld base")
    # Ubuntu
    elif args.distro == distro_options[1]:
        ctr_create("docker.io/library/ubuntu:rolling", path, "apt-get update && apt-get install -y debootstrap && debootstrap --include=systemd-container --components=main,universe,restricted,multiverse --arch amd64 {0} /chrootfld".format(ubuntu_version))
    # Fedora
    elif args.distro == distro_options[2]:
        ctr_create("registry.fedoraproject.org/fedora", path, "dnf -y --releasever={0} --installroot=/chrootfld --disablerepo='*' --enablerepo=fedora --enablerepo=updates install systemd passwd dnf fedora-release vim-minimal".format(fedora_version))
def nspawn_cmd(path: str, cmd: str, error_on_fail: bool = True):
    """Run systemd-nspawn commands"""
    full_cmd = ["systemd-nspawn", "-D", path, "bash", "-c", cmd]
    print("Running command: ", full_cmd)
    subprocess.run(full_cmd, check=error_on_fail)
def nspawn_distro_cmd(dist_current: str, path: str, dist_select: str, cmd: str):
    """
    Run command if the distro matches the specified distro.
    dist_current: The distro selected by the script arguments.
    dist_select: Specify in text what distro this command should run on.
    """
    if dist_select == dist_current:
        nspawn_cmd(path, cmd)


# Check for commands.
check_cmds()

# Default variables
distro_default = "arch"
path_default = os.path.join(os.sep, "var", "lib", "machines", distro_default)

# Get arguments
parser = argparse.ArgumentParser(description='Install systemd-nspawn chroot.')
parser.add_argument("-n", "--noprompt", help='Do not prompt.', action="store_true")
parser.add_argument("-c", "--clean", help='Remove chroot folder and remake chroot.', action="store_true")
parser.add_argument("-d", "--distro", help='Distribution of Linux (default: %(default)s)', default=distro_default, choices=distro_options)
parser.add_argument("-p", "--path", help='Path to store chroot. This is the root of the chroot. (default: %(default)s)', default=path_default)

# Save arguments.
args = parser.parse_args()
print("Distro:", args.distro)
pathvar = os.path.abspath(args.path)
print("Path of chroot:", pathvar)
chroot_hostname = os.path.basename(path_default)
print("Hostname of chroot: {0}".format(chroot_hostname))

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
DISPLAY = os.getenv("DISPLAY")
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)
print("Display variable:", DISPLAY)
if args.clean is True:
    print("\nWARNING: Clean flag set, {0} will be removed! Ensure that this is desired before continuing.\n".format(pathvar))

if args.noprompt is False:
    input("Press Enter to continue.")


### Create chroot ###
# Clean folder if flag set.
if os.path.isdir(pathvar) and args.clean is True:
    shutil.rmtree(pathvar)
# Create the chroot if the folder is missing.
if not os.path.isdir(pathvar):
    create_chroot(args.distro, pathvar)

### Setup chroot ###
# Remove the resolv.conf symlink if it exists.
if os.path.islink(os.path.join(pathvar, "etc", "resolv.conf")):
    os.remove(os.path.join(pathvar, "etc", "resolv.conf"))
# Create user
nspawn_cmd(pathvar, "useradd -m -s /bin/bash {0}".format(USERNAMEVAR), error_on_fail=False)
# Install basic packages
nspawn_distro_cmd(args.distro, pathvar, "arch", "sed -i 's/^#ParallelDownloads/ParallelDownloads/g' /etc/pacman.conf")
nspawn_distro_cmd(args.distro, pathvar, "arch", "pacman -Syu --needed --noconfirm nano sudo which git zsh python base-devel reflector")
nspawn_distro_cmd(args.distro, pathvar, "arch", "reflector --country 'United States' --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist")
# Set hostname
nspawn_cmd(pathvar, 'echo "{0}" > /etc/hostname'.format(chroot_hostname))
nspawn_cmd(pathvar, 'grep -q -e "127.0.0.1 {0}" /etc/hosts || echo "127.0.0.1 {0}" >> /etc/hosts'.format(chroot_hostname))
# Locales
nspawn_cmd(pathvar, "echo 'en_US.UTF-8 UTF-8' > /etc/locale.gen")
nspawn_cmd(pathvar, """echo 'LANG="en_US.UTF-8"' | tee /etc/default/locale /etc/locale.conf""")
nspawn_cmd(pathvar, "locale-gen --purge en_US en_US.UTF-8")
# Groups
nspawn_distro_cmd(args.distro, pathvar, "arch", "usermod -aG wheel {0}".format(USERNAMEVAR))
nspawn_distro_cmd(args.distro, pathvar, "fedora", "usermod -aG wheel {0}".format(USERNAMEVAR))
nspawn_distro_cmd(args.distro, pathvar, "ubuntu", "usermod -aG sudo {0}".format(USERNAMEVAR))
# Scripts
nspawn_cmd(pathvar, 'chmod a+rwx /opt && git clone https://github.com/ramesh45345/CustomScripts /opt/CustomScripts && chown -R {0}:{0} /opt/CustomScripts'.format(USERNAMEVAR), error_on_fail=False)
nspawn_cmd(pathvar, '/opt/CustomScripts/CFuncExt.py --sudoenv')
nspawn_cmd(pathvar, '/opt/CustomScripts/CShellConfig.py -z -d')
nspawn_cmd(pathvar, 'chsh -s /bin/zsh {0}'.format(USERNAMEVAR))

# Sudoers file
nspawn_cmd(pathvar, r'echo -e "%wheel ALL=(ALL) NOPASSWD: ALL\n%sudo ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/custom && chmod 440 /etc/sudoers.d/custom && visudo -c')

# Gui apps
nspawn_distro_cmd(args.distro, pathvar, "arch", "pacman -Syu --needed --noconfirm xfce4-terminal noto-fonts ttf-ubuntu-font-family")
nspawn_distro_cmd(args.distro, pathvar, "arch", """cd /opt/CustomScripts; python -c 'import CFunc; USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser(); import MArch; MArch.install_aur_pkg("yay-bin", USERNAMEVAR, USERGROUP)'""")

chroot_cmd = "sudo systemd-nspawn -D {path} --user={user} --bind-ro=/tmp/.X11-unix/ --bind={homefld}:/tophomefld/ --setenv=DISPLAY={display} xfce4-terminal".format(path=pathvar, user=USERNAMEVAR, display=DISPLAY, homefld=USERHOME)
chroot_run_script = os.path.join(pathvar, "run.sh")
print("\nUse chroot with following command: ")
print(chroot_cmd)
with open(chroot_run_script, 'w') as f:
    f.write("#!/bin/bash\n" + chroot_cmd)
os.chmod(chroot_run_script, 0o777)
print("Wrote script to: {0}".format(chroot_run_script))

print("\nScript End")
