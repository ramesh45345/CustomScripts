#!/usr/bin/env python3
"""Update script."""
import argparse
import os
import pathlib
import re
import shutil
import sys
import subprocess
# Custom includes
import CFunc


### Functions ###
def getenvfromfile(filepath: str):
    """ Read environment variables from a file."""
    envre = re.compile(r'''^(.+?)\s*=\s*(?:["']*)(.+?)(?:[\s"']*)$''')
    result = {}
    with open(filepath) as ins:
        for line in ins:
            match = envre.match(line)
            if match is not None:
                result[match.group(1)] = match.group(2)
    return result
def detect_update():
    update_list = []
    return update_list
def ensure_root():
    """Elevate to root if not running as root"""
    if not CFunc.is_windows() and CFunc.is_root(state_exit=False):
        # Re-run the script with sudo preserving argv
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
def nixos_config_pull():
    """Pull latest nixos config."""
    nixos_path = pathlib.Path(os.path.join(os.sep, "etc", "nixos"))
    if shutil.which("nixos-rebuild") and nixos_path.exists():
        # Run git pull
        CFunc.run_as_user(user_name=nixos_path.owner(), cmd=f"cd {nixos_path} && git pull")
def update_topgrade(args: list = []):
    cmd = ["topgrade", "-y", "flatpak", "--disable", "firmware"] + args
    subprocess.run(cmd, check=True)
def update_rostree():
    subprocess.run(["rpm-ostree", "upgrade"], check=True)
def update_nala():
    subprocess.run(["nala", "update"], check=True)
    subprocess.run(["nala", "upgrade"], check=True)
def update_apt():
    subprocess.run(["apt-get", "update"], check=True)
    subprocess.run(["apt-get", "dist-upgrade"], check=True)
def update_dnf():
    subprocess.run(["dnf", "update", "--refresh", "-y"], check=True)
def update_arch():
    if shutil.which("yay"):
        subprocess.run(["yay", "-Syu", "--needed", "--noconfirm"], check=True)
    else:
        subprocess.run(["pacman", "-Syu", "--needed", "--noconfirm"], check=True)
def update_zypper():
    subprocess.run(["zypper", "up", "-y"], check=True)
    subprocess.run(["zypper", "dup", "-y"], check=True)
def update_nixos():
    subprocess.run(["nixos-rebuild", "boot", "--upgrade"], check=True)
def update_distrobox():
    subprocess.run(["distrobox-upgrade", "--all"], check=True)
def update_flatpak():
    if shutil.which("flatpak"):
        subprocess.run(["flatpak", "update", "--system", "--assumeyes"], check=True)


### Begin Code ###
if __name__ == "__main__":

    # Get arguments
    parser = argparse.ArgumentParser(description='Update script.')
    parser.add_argument("-f", "--flatpak", help='Upgrade flatpak only.', action="store_true")
    args = parser.parse_args()

    if args.flatpak:
        update_flatpak()
        exit(0)

    # Ensure the script is running as root for commands that require it.
    # The original bash uses $SUDOCMD for some commands; here we run as root globally.
    ensure_root()
    nixos_config_pull()

    if shutil.which("topgrade"):
        update_topgrade()
    elif shutil.which("rpm-ostree"):
        update_rostree()
    elif shutil.which("nala"):
        update_nala()
    elif shutil.which("apt-get"):
        update_apt()
    elif shutil.which("dnf"):
        update_dnf()
    elif  shutil.which("yay"):
        update_arch()
    elif shutil.which("zypper"):
        update_zypper()
    elif shutil.which("nix"):
        # Original condition: type nix &> /dev/null && ! [[ "$(which nix)" == *"$USER"* ]]
        # which nix should not contain the username; replicate that check:
        nix_path = shutil.which("nix") or ""
        user = os.environ.get("SUDO_USER") or os.environ.get("USER") or ""
        if user and user not in nix_path:
            update_nixos()
    update_flatpak()

    # Non-root commands
    if not shutil.which("topgrade"):
        update_distrobox()
