#!/usr/bin/env python3
"""Install systemd-nspawn chroot."""

# Python includes.
import argparse
import pwd
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
ubuntu_version = "impish"
fedora_version = "35"


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
        ctr_create("docker.io/library/archlinux:latest", path, "sed -i 's/^#ParallelDownloads/ParallelDownloads/g' /etc/pacman.conf && pacman -Sy --noconfirm --needed arch-install-scripts && pacstrap -c /chrootfld base python3")
    # Ubuntu
    elif args.distro == distro_options[1]:
        ctr_create("docker.io/library/ubuntu:rolling", path, "apt-get update && apt-get install -y debootstrap && debootstrap --include=systemd-container --components=main,universe,restricted,multiverse --arch amd64 {0} /chrootfld".format(ubuntu_version))
    # Fedora
    elif args.distro == distro_options[2]:
        ctr_create("registry.fedoraproject.org/fedora", path, "dnf -y --releasever={0} --installroot=/chrootfld --disablerepo='*' --enablerepo=fedora --enablerepo=updates install systemd passwd dnf fedora-release vim-minimal".format(fedora_version))
def sshauthkey_get():
    """Get the ssh public key from the host machine."""
    sshkey = ""
    if os.path.isfile(os.path.join(USERHOME, ".ssh", "id_ed25519.pub")) is True:
        with open(os.path.join(USERHOME, ".ssh", "id_ed25519.pub"), 'r') as sshfile:
            sshkey = sshfile.read().replace('\n', '')
    elif os.path.isfile(os.path.join(USERHOME, ".ssh", "id_rsa.pub")) is True:
        with open(os.path.join(USERHOME, ".ssh", "id_rsa.pub"), 'r') as sshfile:
            sshkey = sshfile.read().replace('\n', '')
    return sshkey


# Check for commands.
check_cmds()

# Default variables
distro_default = "arch"
basepath_default = os.path.join(os.sep, "var", "lib", "machines")
path_default = os.path.join(basepath_default, distro_default)

# Get arguments
parser = argparse.ArgumentParser(description='Install systemd-nspawn chroot.')
parser.add_argument("-n", "--noprompt", help='Do not prompt.', action="store_true")
parser.add_argument("-b", "--bootable", help='Provision for booting.', action="store_true")
parser.add_argument("-c", "--clean", help='Remove chroot folder and remake chroot.', action="store_true")
parser.add_argument("-d", "--distro", help='Distribution of Linux (default: %(default)s)', default=distro_default, choices=distro_options)
parser.add_argument("-p", "--hostname", help='Hostname of chroot. This is also the folder name of the chroot. (default: %(default)s)', default=distro_default)

# Save arguments.
args = parser.parse_args()
print("Distro:", args.distro)
pathvar = os.path.join(basepath_default, args.hostname)
print("Path of chroot:", pathvar)
chroot_hostname = args.hostname
print("Hostname of chroot: {0}".format(chroot_hostname))

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
CT_USERNAME = "user"
CT_USERID = pwd.getpwnam(USERNAMEVAR).pw_uid
CT_GROUPNAME = CT_USERNAME
CT_GROUPID = pwd.getpwnam(USERNAMEVAR).pw_gid
CT_HOME = os.path.join(os.sep, "home", CT_USERNAME)
DISPLAY = os.getenv("DISPLAY")
print("Username is:", CT_USERNAME)
print("Group Name is:", CT_GROUPNAME)
print("Display variable:", DISPLAY)
if args.clean is True:
    print("\nWARNING: Clean flag set, {0} will be removed! Ensure that this is desired before continuing.\n".format(pathvar))

if args.noprompt is False:
    input("Press Enter to continue.")


### Create chroot ###
# Clean folder if flag set.
if os.path.isdir(pathvar) and args.clean is True:
    shutil.rmtree(pathvar)
# Remove the nspawn file if it exists.
os.makedirs(os.path.join(os.sep, "etc", "systemd", "nspawn"), exist_ok=True)
nspawn_file = os.path.join(os.sep, "etc", "systemd", "nspawn", "{0}.nspawn".format(chroot_hostname))
if os.path.isfile(nspawn_file):
    os.remove(nspawn_file)
# Create the chroot if the folder is missing.
if not os.path.isdir(pathvar):
    create_chroot(args.distro, pathvar)

### Setup chroot ###
# Remove the resolv.conf symlink if it exists.
if os.path.islink(os.path.join(pathvar, "etc", "resolv.conf")):
    os.remove(os.path.join(pathvar, "etc", "resolv.conf"))

# Copy CustomScripts into chroot
cspath = os.path.join(pathvar, "opt", "CustomScripts")
if os.path.isdir(cspath):
    shutil.rmtree(cspath)
shutil.copytree(SCRIPTDIR, cspath)
# Rewrite origin remote url
currentpath = os.getcwd()
os.chdir(cspath)
subprocess.run(['git', 'config', 'remote.origin.url', "https://github.com/ramesh45345/CustomScripts"], check=True)
os.chdir(currentpath)

# Run provisioner script
provision_cmd = ["systemd-nspawn", "-D", pathvar, "/opt/CustomScripts/Mspawn_provision.py", "--distro", args.distro, "--user", CT_USERNAME, "--uid", str(CT_USERID), "--group", CT_GROUPNAME, "--gid", str(CT_GROUPID), "--password", "asdf", "--sshkey", sshauthkey_get(), "--hostname", chroot_hostname]
if args.bootable:
    provision_cmd.append("-b")
print(provision_cmd)
subprocess.run(provision_cmd, check=True)

# Create helper scripts
chroot_cmd = "sudo systemd-nspawn -D {path} --settings=0 --user={user} --bind-ro=/tmp/.X11-unix/ --bind={homefld}:/tophomefld/ --setenv=DISPLAY={display} xfce4-terminal".format(path=pathvar, user=CT_USERNAME, display=DISPLAY, homefld=USERHOME)
chroot_run_script = os.path.join(pathvar, "run.sh")
print("\nUse chroot with following command: ")
print(chroot_cmd)
with open(chroot_run_script, 'w') as f:
    f.write("#!/bin/bash\n" + chroot_cmd)
os.chmod(chroot_run_script, 0o777)
print("Wrote run script to: {0}".format(chroot_run_script))

if args.bootable:
    # Create nspawn file
    with open(nspawn_file, 'w') as f:
        f.write("""
[Exec]
User=root
PrivateUsers=no

[Files]
Bind={0}:/tophomefld/

[Network]
Bridge=virbr0
# Expose ports to host.
# Port=tcp:2222:22
""".format(USERHOME))
    print("Wrote nspawn file to: {0}".format(nspawn_file))
    print("Run systemd service with: sudo systemctl start systemd-nspawn@{0}.service".format(chroot_hostname))

print("\nScript End")
