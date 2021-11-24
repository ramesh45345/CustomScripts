#!/usr/bin/env python3
"""Create toolbox images."""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]

# Global variables
distro_options = ["all", "arch", "ubuntu", "fedora"]


### Functions ###
def check_cmds(cmdcheck: list):
    """Ensure that certain commands exist."""
    for cmd in cmdcheck:
        if not shutil.which(cmd):
            sys.exit("\nError, ensure command {0} is installed.".format(cmd))
def addtext(ct_text: str, distro: str = "all"):
    """Add text to containerfiles."""
    global containerfile_arch
    global containerfile_fedora
    global containerfile_ubuntu
    if distro == "all" or distro == "arch":
        containerfile_arch += "\n" + ct_text
    if distro == "all" or distro == "fedora":
        containerfile_fedora += "\n" + ct_text
    if distro == "all" or distro == "ubuntu":
        containerfile_ubuntu += "\n" + ct_text


# Get arguments
parser = argparse.ArgumentParser(description='Create toolbox images.')
parser.add_argument("-d", "--distro", help='Distro for image creation (choices: %(choices)s) (default: %(default)s)', default="all", choices=distro_options)
parser.add_argument("-p", "--prune", help='Remove all existing images.', action="store_true")

# Save arguments.
args = parser.parse_args()

# Exit if root.
CFunc.is_root(False)

# Print details
print("Distro:", args.distro)


### Prune ###
if args.prune:
    if args.distro == "all" or args.distro == "arch":
        subprocess.run("podman rmi --force arch-shared", check=False, shell=True)
    if args.distro == "all" or args.distro == "fedora":
        subprocess.run("podman rmi --force fedora-shared", check=False, shell=True)
    if args.distro == "all" or args.distro == "ubuntu":
        subprocess.run("podman rmi --force ubuntu-shared", check=False, shell=True)


### Create containerfile ###
containerfile_arch = """
FROM docker.io/library/archlinux:base-devel
ENV NAME=arch-shared
"""
containerfile_fedora = """
FROM registry.fedoraproject.org/fedora:latest
ENV NAME=fedora-shared
"""
containerfile_ubuntu = """
FROM docker.io/library/ubuntu:rolling
ENV NAME=ubuntu-shared
"""

addtext(r"""
LABEL com.github.containers.toolbox="true" \
      com.github.debarshiray.toolbox="true" \
      com.redhat.component="$NAME" \
      name="$NAME"
""")

# Software
addtext(r"""
# Setup mirrors
RUN pacman -Syu --needed --noconfirm reflector
RUN reflector --country 'United States' --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist
RUN pacman -Syy
# Software setup
RUN pacman -Syu --needed --noconfirm nano sudo git zsh python3 shadow
RUN pacman -Syu --needed --noconfirm ttf-dejavu ttf-liberation powerline-fonts
# Enable multilib
RUN echo -e '\n[multilib]\nInclude = /etc/pacman.d/mirrorlist' >> /etc/pacman.conf ; pacman -Syu --needed --noconfirm
# Wine
RUN pacman -Syu --needed --noconfirm wine wine-mono wine-gecko zenity winetricks

# User Setup
RUN echo "root:asdf" | chpasswd && \
    echo -e "nobody ALL=(ALL) NOPASSWD: /usr/sbin/pacman" > /etc/sudoers.d/nopw && \
    chmod 0440 /etc/sudoers.d/nopw
# Install AUR helper
RUN git clone https://aur.archlinux.org/yay-bin.git /tmp/yay-bin && \
    chmod a+rw -R /tmp/yay-bin && cd /tmp/yay-bin && \
    sudo -u nobody makepkg -si --noconfirm && \
    cd / && rm -rf /tmp/yay-bin
""", "arch")
addtext(r"""
# From stock image.
RUN sed -i '/tsflags=nodocs/d' /etc/dnf/dnf.conf
RUN dnf -y reinstall acl bash curl gawk grep gzip libcap openssl p11-kit pam python3 rpm sed systemd tar
RUN dnf -y install bash-completion bzip2 diffutils dnf-plugins-core findutils flatpak-spawn fpaste git gnupg gnupg2-smime gvfs-client hostname iputils jwhois keyutils krb5-libs less lsof man-db man-pages mlocate mtr nano-default-editor nss-mdns openssh-clients passwd pigz procps-ng rsync shadow-utils sudo tcpdump time traceroute tree unzip vte-profile wget which words xorg-x11-xauth xz zip

# Custom stuff
RUN dnf -y install zsh
RUN dnf -y install wine winetricks
""", "fedora")
addtext(r"""
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update; apt-get -y upgrade
RUN apt-get install -y sudo libcap2-bin bash zsh fish nano p7zip-full p7zip-rar unrar wget curl rsync less python-is-python3 git lsb-release software-properties-common apt-transport-https gnupg

# Install locales
RUN apt-get install -y locales && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    echo 'LANG="en_US.UTF-8"'>/etc/default/locale && \
    echo "LANG=en_US.UTF-8" > /etc/locale.conf && \
    locale-gen --purge en_US en_US.UTF-8 && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale

# Wine
RUN dpkg --add-architecture i386 && \
    wget -nc https://dl.winehq.org/wine-builds/winehq.key -O /tmp/winehq.key && \
    apt-key add /tmp/winehq.key && rm /tmp/winehq.key && \
    add-apt-repository "deb https://dl.winehq.org/wine-builds/ubuntu/ $(lsb_release -sc) main" && \
    apt-get update && apt install -y --install-recommends winehq-devel
""", "ubuntu")

# Sudoers
addtext(r"""
RUN echo '%wheel ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/user-group && \
    echo '%sudo ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers.d/user-group && \
    chmod 440 /etc/sudoers.d/user-group
""")
# Scripts setup
addtext("RUN git clone https://github.com/ramesh45345/CustomScripts /opt/CustomScripts && chown 1000:1000 -R /opt/CustomScripts")
# Timezone
addtext("RUN ln -sf /usr/share/zoneinfo/US/Eastern /etc/localtime")

# Cleanup
addtext("RUN pacman -Scc --noconfirm", "arch")
addtext("RUN dnf clean all", "fedora")
addtext("RUN apt-get clean", "ubuntu")
# Command
addtext('CMD ["zsh"]')

# Write containerfiles
tempfolder_arch = os.path.join(tempfile.gettempdir(), "ct_tb_arch")
tempfolder_fedora = os.path.join(tempfile.gettempdir(), "ct_tb_fedora")
tempfolder_ubuntu = os.path.join(tempfile.gettempdir(), "ct_tb_ubuntu")
tempfile_arch = os.path.join(tempfolder_arch, "Containerfile_arch")
tempfile_fedora = os.path.join(tempfolder_fedora, "Containerfile_fedora")
tempfile_ubuntu = os.path.join(tempfolder_ubuntu, "Containerfile_ubuntu")
if args.distro == "all" or args.distro == "arch":
    # Remove old folder if it exists.
    if os.path.isdir(tempfolder_arch):
        shutil.rmtree(tempfolder_arch)
    # Make temp folder
    os.makedirs(tempfolder_arch, exist_ok=True)
    # Write containerfile
    with open(tempfile_arch, 'w') as f:
        f.write(containerfile_arch)
    print("File written to {0}".format(tempfile_arch))
if args.distro == "all" or args.distro == "fedora":
    # Remove old folder if it exists.
    if os.path.isdir(tempfolder_fedora):
        shutil.rmtree(tempfolder_fedora)
    # Make temp folder
    os.makedirs(tempfolder_fedora, exist_ok=True)
    # Write containerfile
    with open(tempfile_fedora, 'w') as f:
        f.write(containerfile_fedora)
    print("File written to {0}".format(tempfile_fedora))
if args.distro == "all" or args.distro == "ubuntu":
    # Remove old folder if it exists.
    if os.path.isdir(tempfolder_ubuntu):
        shutil.rmtree(tempfolder_ubuntu)
    # Make temp folder
    os.makedirs(tempfolder_ubuntu, exist_ok=True)
    # Write containerfile
    with open(tempfile_ubuntu, 'w') as f:
        f.write(containerfile_ubuntu)
    print("File written to {0}".format(tempfile_ubuntu))

### Build ###
currentpath = os.getcwd()
if args.distro == "all" or args.distro == "arch":
    os.chdir(tempfolder_arch)
    subprocess.run(["podman", "build", "-t", "arch-shared", "-f", os.path.basename(tempfile_arch)], check=True)
    print('Run "toolbox create -i arch-shared ; toolbox enter arch-shared" to create and run a container.')
if args.distro == "all" or args.distro == "fedora":
    os.chdir(tempfolder_fedora)
    subprocess.run(["podman", "build", "-t", "fedora-shared", "-f", os.path.basename(tempfile_fedora)], check=True)
    print('Run "toolbox create -i fedora-shared ; toolbox enter fedora-shared" to create and run a container.')
if args.distro == "all" or args.distro == "ubuntu":
    os.chdir(tempfolder_ubuntu)
    subprocess.run(["podman", "build", "-t", "ubuntu-shared", "-f", os.path.basename(tempfile_ubuntu)], check=True)
    print('Run "toolbox create -i ubuntu-shared ; toolbox enter ubuntu-shared" to create and run a container.')
os.chdir(currentpath)

if args.distro == "all":
    print("""
The following commands can be used to create and run containers:
toolbox create -i arch-shared ; toolbox enter arch-shared
toolbox create -i fedora-shared ; toolbox enter fedora-shared
toolbox create -i ubuntu-shared ; toolbox enter ubuntu-shared
""")

print("\nScript End")
