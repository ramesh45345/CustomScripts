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
    """
    Read environment variables from a file.
    https://stackoverflow.com/a/50456924
    """
    envre = re.compile(r'''^(.+?)\s*=\s*(?:["']*)(.+?)(?:[\s"']*)$''')
    result = {}
    with open(filepath) as ins:
        for line in ins:
            match = envre.match(line)
            if match is not None:
                result[match.group(1)] = match.group(2)
    return result
def detect_update():
    """Detect the os in use."""
    update_list = []
    update_cmd_list = []
    # Get variables
    file_osrelease = pathlib.Path(os.path.join(os.sep, "etc", "os-release"))
    vars_osrelease = {}
    if file_osrelease.exists():
        vars_osrelease = getenvfromfile(file_osrelease)
    file_lsbrelease = pathlib.Path(os.path.join(os.sep, "etc", "lsb-release"))
    vars_lsbrelease = {}
    if file_lsbrelease.exists():
        vars_lsbrelease = getenvfromfile(file_lsbrelease)
    # print(vars_osrelease, vars_lsbrelease)

    # Nixos
    if "ID" in vars_osrelease and vars_osrelease["ID"] == "nixos" and shutil.which("nixos-rebuild"):
        update_list.append("nixos")
        update_cmd_list.append(update_nixos())

    # Topgrade or other upgrades.
    if shutil.which("topgrade"):
        update_list.append("topgrade")
        update_cmd_list.append(update_topgrade(update_list))
    else:
        # If topgrade is not available, or for exceptions, add OS updates to the list.
        if shutil.which("flatpak"):
            update_list.append("flatpak")
            update_cmd_list.append(update_flatpak())
    
    return update_list, update_cmd_list
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
def update_topgrade(oslist: list = []):
    """Build and run topgrade command."""
    # TODO: Run topgrade as user?
    # Topgrade command
    topgrade_cmd_array = ["topgrade", "-y", "--disable=firmware"]
    # Check if topgrade config exists
    topgrade_config_file = os.path.join(os.sep, "etc", "topgrade.toml")
    if not os.path.exists(topgrade_config_file):
        # If nixos, exclude system
        if "nixos" in oslist:
            topgrade_cmd_array += ["--disable=system"]
    return topgrade_cmd_array
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
    cmd = ["nixos-rebuild", "boot", "--upgrade"]
    if shutil.which("nh"):
        cmd = ["nh", "os", "boot", "-u"]
    return cmd
def update_distrobox():
    subprocess.run(["distrobox-upgrade", "--all"], check=True)
def update_distrobox_user():
    return
def update_flatpak():
    return ["flatpak", "update", "--system", "--assumeyes"]


### Begin Code ###
if __name__ == "__main__":

    # Get arguments
    parser = argparse.ArgumentParser(description='Update script.')
    parser.add_argument("-f", "--flatpak", help='Upgrade flatpak only.', action="store_true")
    parser.add_argument("-d", "--dryrun", help='Print commands to run only.', action="store_true")
    args = parser.parse_args()

    upgrade_list, upgrade_cmd_list = detect_update()
    if args.dryrun:
        print("\nUpgrade List:")
        print(*upgrade_list, sep='\n')
        print("\nUpgrade commands:")
        print(*upgrade_cmd_list, sep='\n')
        exit(0)

    if args.flatpak and "flatpak" in upgrade_list:
        subprocess.run(update_flatpak(), check=True)
        exit(0)

    # Require root before proceeding
    ensure_root()
    # Update nixos config
    nixos_config_pull()

    # Run root upgrade commands
    for cmd in upgrade_cmd_list:
        subprocess.run(cmd, check=True)

    # Non-root commands
