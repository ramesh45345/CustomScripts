#!/usr/bin/env python3
"""Create toolbox images."""

# Python includes.
import argparse
import os
import shutil
import subprocess
import tempfile
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Global variables
distro_options = ["all", "arch", "ubuntu", "fedora", "alma"]


### Functions ###
def addtext(ct_text: str, distro: str = "all"):
    """Add text to containerfiles."""
    global containerfile_alma
    global containerfile_arch
    global containerfile_fedora
    global containerfile_ubuntu
    if distro == "all" or distro == "alma":
        containerfile_alma += "\n" + ct_text
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
rootstate = CFunc.is_root(checkstate=True, state_exit=False)
if rootstate is True:
    print("WARNING: Running as root.")

# Print details
print("Distro:", args.distro)


### Prune ###
if args.prune:
    if args.distro == "all" or args.distro == "alma":
        subprocess.run("podman rmi --force alma-img", check=False, shell=True)
    if args.distro == "all" or args.distro == "arch":
        subprocess.run("podman rmi --force arch-img", check=False, shell=True)
    if args.distro == "all" or args.distro == "fedora":
        subprocess.run("podman rmi --force fedora-img", check=False, shell=True)
    if args.distro == "all" or args.distro == "ubuntu":
        subprocess.run("podman rmi --force ubuntu-img", check=False, shell=True)


### Create containerfile ###
containerfile_alma = """
FROM quay.io/almalinuxorg/almalinux:latest
ENV NAME=alma-img
"""
containerfile_arch = """
FROM docker.io/library/archlinux:base-devel
ENV NAME=arch-img
"""
containerfile_fedora = """
FROM registry.fedoraproject.org/fedora:latest
ENV NAME=fedora-img
"""
containerfile_ubuntu = """
FROM docker.io/library/ubuntu:latest
ENV NAME=ubuntu-img
"""

addtext(r"""
LABEL com.github.containers.toolbox="true" \
      name="$NAME"
""")

# Software
addtext(r"""
# Setup mirrors
RUN pacman -Syu --needed --noconfirm reflector
RUN reflector --country 'United States' --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist
RUN pacman -Syy
# Software setup
RUN pacman -Syu --needed --noconfirm nano sudo git zsh fish python3 shadow tmux
RUN pacman -Syu --needed --noconfirm ttf-dejavu ttf-liberation powerline-fonts
# Enable multilib
RUN echo -e '\n[multilib]\nInclude = /etc/pacman.d/mirrorlist' >> /etc/pacman.conf ; pacman -Syu --needed --noconfirm
# Wine
RUN pacman -Syu --needed --noconfirm wine wine-mono wine-gecko zenity winetricks

# Locales
ENV LANG=en_US.UTF-8
RUN echo "LANG=en_US.UTF-8" > "/etc/locale.conf"
RUN sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/g' "/etc/locale.gen"
RUN locale-gen

# User Setup
RUN echo "root:asdf" | chpasswd && \
    echo -e "nobody ALL=(ALL) NOPASSWD: /usr/sbin/pacman" > /etc/sudoers.d/nopw && \
    chmod 0440 /etc/sudoers.d/nopw
# Setup nobody account for use to install AUR helper
RUN chage -E -1 -M -1 -I -1 -m 0 nobody
# Install AUR helper
RUN git clone https://aur.archlinux.org/yay-bin.git /tmp/yay-bin && \
    chmod a+rw -R /tmp/yay-bin && cd /tmp/yay-bin && \
    sudo -u nobody makepkg -si --noconfirm && \
    cd / && rm -rf /tmp/yay-bin
""", "arch")
addtext(r"""
# From stock image.
RUN sed -i '/tsflags=nodocs/d' /etc/dnf/dnf.conf
RUN dnf -y install acl bash curl gawk grep gzip libcap openssl p11-kit pam python3 rpm sed systemd tar
RUN dnf -y install bash-completion bzip2 diffutils dnf-plugins-core findutils flatpak-spawn fpaste fuse fuse-libs git gnupg gnupg2-smime gvfs-client hostname iputils jwhois keyutils krb5-libs less lsof man-db man-pages mtr nano-default-editor nss-mdns openssh-clients passwd pigz procps-ng rsync shadow-utils sudo tcpdump time tmux traceroute tree unzip vte-profile wget which words xorg-x11-xauth xz zip

# Shell Tools
RUN dnf -y install zsh fish powerline-fonts
# Build tools
RUN dnf -y install make gcc automake autoconf ninja-build
# Wine
RUN dnf -y install wine winetricks
""", "fedora")
addtext(r"""
# From stock image.
RUN sed -i '/tsflags=nodocs/d' /etc/dnf/dnf.conf
RUN dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm https://dl.fedoraproject.org/pub/epel/epel-next-release-latest-9.noarch.rpm
RUN dnf install -y https://download1.rpmfusion.org/free/el/rpmfusion-free-release-9.noarch.rpm https://download1.rpmfusion.org/nonfree/el/rpmfusion-nonfree-release-9.noarch.rpm
RUN dnf -y install --allowerasing acl bash nano curl gawk grep gzip libcap openssl p11-kit pam python3 rpm sed systemd tar xorg-x11-server-Xorg xorg-x11-xauth xorg-x11-server-utils
RUN dnf -y install bash-completion bzip2 diffutils dnf-plugins-core findutils flatpak-spawn fuse fuse-libs git gnupg gnupg2-smime gvfs-client hostname iputils keyutils krb5-libs less lsof man-db man-pages mtr openssh-clients passwd pigz procps-ng rsync shadow-utils sudo tcpdump time tmux traceroute tree unzip vte-profile wget which words xorg-x11-xauth xz zip

# Shell Tools
RUN dnf -y install zsh powerline-fonts
# Build tools
RUN dnf -y install make gcc automake autoconf
""", "alma")
addtext(r"""
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update; apt-get -y upgrade
RUN apt-get install -y sudo libcap2-bin bash zsh fish nano p7zip-full p7zip-rar unrar wget curl rsync less python-is-python3 python3-pip git lsb-release software-properties-common apt-transport-https gnupg tmux

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
    mkdir -pm755 /etc/apt/keyrings && \
    wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key && \
    wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/$(lsb_release -sc)/winehq-$(lsb_release -sc).sources && \
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
# Run shell config when zsh loads for the first time.
addtext("RUN echo '/opt/CustomScripts/CShellConfig.py -z' > /etc/skel/.zshrc")
addtext("RUN /opt/CustomScripts/CFuncExt.py -s")
# Timezone
addtext("RUN ln -sf /usr/share/zoneinfo/US/Eastern /etc/localtime")

# Cleanup
addtext("RUN pacman -Scc --noconfirm", "arch")
addtext("RUN dnf clean all", "fedora")
addtext("RUN dnf clean all", "alma")
addtext("RUN apt-get clean", "ubuntu")
# Command
addtext('CMD ["zsh"]')

# Write containerfiles
tempfolder_alma = os.path.join(tempfile.gettempdir(), "ct_tb_alma")
tempfolder_arch = os.path.join(tempfile.gettempdir(), "ct_tb_arch")
tempfolder_fedora = os.path.join(tempfile.gettempdir(), "ct_tb_fedora")
tempfolder_ubuntu = os.path.join(tempfile.gettempdir(), "ct_tb_ubuntu")
tempfile_alma = os.path.join(tempfolder_alma, "Containerfile_alma")
tempfile_arch = os.path.join(tempfolder_arch, "Containerfile_arch")
tempfile_fedora = os.path.join(tempfolder_fedora, "Containerfile_fedora")
tempfile_ubuntu = os.path.join(tempfolder_ubuntu, "Containerfile_ubuntu")
if args.distro == "all" or args.distro == "alma":
    # Remove old folder if it exists.
    if os.path.isdir(tempfolder_alma):
        shutil.rmtree(tempfolder_alma)
    # Make temp folder
    os.makedirs(tempfolder_alma, exist_ok=True)
    # Write containerfile
    with open(tempfile_alma, 'w') as f:
        f.write(containerfile_alma)
    os.chmod(tempfile_alma, 0o666)
    print("File written to {0}".format(tempfile_alma))
if args.distro == "all" or args.distro == "arch":
    # Remove old folder if it exists.
    if os.path.isdir(tempfolder_arch):
        shutil.rmtree(tempfolder_arch)
    # Make temp folder
    os.makedirs(tempfolder_arch, exist_ok=True)
    # Write containerfile
    with open(tempfile_arch, 'w') as f:
        f.write(containerfile_arch)
    os.chmod(tempfile_arch, 0o666)
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
    os.chmod(tempfile_fedora, 0o666)
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
    os.chmod(tempfile_ubuntu, 0o666)
    print("File written to {0}".format(tempfile_ubuntu))

### Build ###
currentpath = os.getcwd()
if args.distro == "all" or args.distro == "alma":
    os.chdir(tempfolder_alma)
    subprocess.run(["podman", "build", "--pull=true", "-t", "alma-img", "-f", os.path.basename(tempfile_alma)], check=True)
if args.distro == "all" or args.distro == "arch":
    os.chdir(tempfolder_arch)
    subprocess.run(["podman", "build", "--pull=true", "-t", "arch-img", "-f", os.path.basename(tempfile_arch)], check=True)
if args.distro == "all" or args.distro == "fedora":
    os.chdir(tempfolder_fedora)
    subprocess.run(["podman", "build", "--pull=true", "-t", "fedora-img", "-f", os.path.basename(tempfile_fedora)], check=True)
if args.distro == "all" or args.distro == "ubuntu":
    os.chdir(tempfolder_ubuntu)
    subprocess.run(["podman", "build", "--pull=true", "-t", "ubuntu-img", "-f", os.path.basename(tempfile_ubuntu)], check=True)
os.chdir(currentpath)

print("""
The following commands can be used to create and run containers:

Distrobox:
distrobox create -n alma-ct -i alma-img ; distrobox enter alma-ct
distrobox create -n arch-ct -i arch-img ; distrobox enter arch-ct
distrobox create -n fedora-ct -i fedora-img ; distrobox enter fedora-ct
distrobox create -n ubuntu-ct -i ubuntu-img ; distrobox enter ubuntu-ct

Distrobox (non-shared home):
distrobox create -n alma-ct -i alma-img -H /mnt/Storage/VMs/alma-ct-home ; distrobox enter alma-ct
distrobox create -n arch-ct -i arch-img -H /mnt/Storage/VMs/arch-ct-home ; distrobox enter arch-ct
distrobox create -n fedora-ct -i fedora-img -H /mnt/Storage/VMs/fedora-ct-home ; distrobox enter fedora-ct
distrobox create -n ubuntu-ct -i ubuntu-img -H /mnt/Storage/VMs/ubuntu-ct-home ; distrobox enter ubuntu-ct

Add --root to both create and run container to use as root.
""")

print("\nScript End")
