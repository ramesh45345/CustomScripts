#!/usr/bin/env python3
"""Update script."""
import argparse
import functools
import os
import pathlib
import re
import shlex
import shutil
import sys
import subprocess
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

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
def osvars_get(printvars: bool = False):
    """Get variables from osrelease and lsbrelease."""
    file_osrelease = pathlib.Path(os.path.join(os.sep, "etc", "os-release"))
    vars_osrelease = {}
    if file_osrelease.exists():
        vars_osrelease = getenvfromfile(file_osrelease)
    file_lsbrelease = pathlib.Path(os.path.join(os.sep, "etc", "lsb-release"))
    vars_lsbrelease = {}
    if file_lsbrelease.exists():
        vars_lsbrelease = getenvfromfile(file_lsbrelease)
    if printvars:
        print("\nOS Release vars:")
        for key, val in vars_osrelease.items():
            print(f"{key}: {val}")
        print("\nLSB Release vars:")
        for key, val in vars_lsbrelease.items():
            print(f"{key}: {val}")
    # Merge dicts
    vars = {**vars_osrelease, **vars_lsbrelease}
    return vars
def detect_user():
    """Get the normal user to run commands as."""
    # Check SUDO_USER first. If that doesn't work, use CFunc to get the normal user.
    return os.environ.get("SUDO_USER", CFunc.getnormaluser()[0])
def detect_os(osid: list = [], osvars: dict = osvars_get()):
    """Check if the os string is detected in os variables."""
    detected = False
    for x in osid:
        for osvar_item in osvars.items():
            # 0 is key, 1 is value for dict items
            if x == osvar_item[1]:
                detected = True
    return detected
def detect_update():
    """Detect the os in use."""
    update_list = []
    update_cmd_list = []
    update_cmd_nonroot_list = []
    topgrade_disable_system = False
    # Get variables
    var_os= osvars_get()

    # Arch
    if detect_os(["arch"], var_os):
        update_list.append("arch")
        topgrade_disable_system = True
        if shutil.which("yay"):
            # Yay needs to run without root permissions
            update_cmd_nonroot_list.append(["yay", "-Syu", "--needed", "--noconfirm"])
        elif shutil.which("pacman"):
            update_cmd_list.append(["pacman", "-Syu", "--needed", "--noconfirm"])
        else:
            topgrade_disable_system = False
    # Nixos
    if detect_os(["nixos"], var_os) and shutil.which("nixos-rebuild"):
        update_list.append("nixos")
        topgrade_disable_system = True
        if shutil.which("nh"):
            update_cmd_list.append(["nh", "os", "boot", "--bypass-root-check", "-u"])
        elif shutil.which("nixos-rebuild"):
            update_cmd_list.append(["nixos-rebuild", "boot", "--upgrade"])
        else:
            topgrade_disable_system = False

    # Topgrade or other upgrades.
    if shutil.which("topgrade"):
        update_list.append("topgrade")
        update_cmd_nonroot_list.append(update_topgrade(dis_system=topgrade_disable_system))
    else:
        # Alpine
        if detect_os(["alpine"], var_os) and shutil.which("apk"):
            update_list.append("alpine")
            update_cmd_list.append(["apk", "update"])
            update_cmd_list.append(["apk", "upgrade"])
        # Debian/Ubuntu
        if detect_os(["debian", "ubuntu"], var_os):
            if shutil.which("nala"):
                subprocess.run(["nala", "update"], check=True)
                subprocess.run(["nala", "upgrade"], check=True)
            elif shutil.which("apt"):
                subprocess.run(["apt", "update", "-y"], check=True)
                subprocess.run(["apt", "dist-upgrade", "-y"], check=True)
        # Fedora/RHEL bootc or rpm-ostree
        if detect_os(["fedora"], var_os) and shutil.which("dnf") and shutil.which("rpm-ostree"):
            update_list.append("fedora-rpmostree")
            update_cmd_list.append(["rpm-ostree", "upgrade"])
        # Fedora/RHEL
        if detect_os(["fedora"], var_os) and shutil.which("dnf") and not shutil.which("rpm-ostree"):
            update_list.append("fedora")
            update_cmd_list.append(["dnf", "update", "--refresh", "-y"])
        # Opensuse
        if detect_os(["opensuse"], var_os) and shutil.which("zypper"):
            update_list.append("opensuse")
            update_cmd_list.append(["zypper", "up", "-y"])
            update_cmd_list.append(["zypper", "dup", "-y"])
        # If topgrade is not available, or for exceptions, add OS updates to the list.
        if shutil.which("flatpak"):
            update_list.append("flatpak")
            update_cmd_list.append(update_flatpak())
            update_cmd_nonroot_list.append(update_flatpak_user())
        # Distrobox user
        if shutil.which("distrobox"):
            update_list.append("distrobox-user")
            update_cmd_nonroot_list.append(["distrobox", "upgrade", "--all"])

    # Distrobox root
    # TODO: Disable this for now, always errors out.
    # if shutil.which("distrobox"):
    #     update_list.append("distrobox-root")
    #     # Distrobox root expects to run as non-root first.
    #     update_cmd_nonroot_list.append(["distrobox", "upgrade", "--root", "--all"])

    return update_list, update_cmd_list, update_cmd_nonroot_list
def ensure_root():
    """Elevate to root if not running as root"""
    if not CFunc.is_windows() and CFunc.is_root(checkstate=False, state_exit=False):
        # Re-run the script with sudo preserving argv
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)
def nixos_config_pull():
    """Pull latest nixos config."""
    nixos_path = pathlib.Path(os.path.join(os.sep, "etc", "nixos"))
    if shutil.which("nixos-rebuild") and nixos_path.exists():
        # Run git pull
        CFunc.run_as_user(user_name=nixos_path.owner(), cmd=f"cd {nixos_path} && git pull")
def update_topgrade(dis_system: bool = False):
    """Build and run topgrade command."""
    # Topgrade command
    topgrade_cmd_array = ["topgrade", "-y", "--disable=firmware"]
    # Remove home-manager, it always fails if nh is present, and should be upgraded separately.
    topgrade_cmd_array += ["--disable=home_manager"]
    # Exclude system if option is set
    if dis_system:
        topgrade_cmd_array += ["--disable=system"]
    return topgrade_cmd_array
def update_flatpak():
    return ["flatpak", "update", "--system", "--assumeyes"]
def update_flatpak_user():
    return ["flatpak", "update", "--user", "--assumeyes"]


### Begin Code ###
if __name__ == "__main__":

    # Get arguments
    parser = argparse.ArgumentParser(description='Update script.')
    parser.add_argument("-f", "--flatpak", help='Upgrade flatpak only.', action="store_true")
    parser.add_argument("-d", "--dryrun", help='Print commands to run only.', action="store_true")
    args = parser.parse_args()

    upgrade_list, upgrade_cmd_list, update_cmd_nonroot_list = detect_update()
    if args.dryrun:
        print("\nUpgrade List:")
        print(*upgrade_list, sep='\n')
        print("\nUpgrade commands (root):")
        print(*upgrade_cmd_list, sep='\n')
        print("\nUpgrade commands (nonroot):")
        print(*update_cmd_nonroot_list, sep='\n')
        exit(0)

    if args.flatpak and "flatpak" in upgrade_list:
        subprocess.run(update_flatpak(), check=True)
        exit(0)

    # Require root before proceeding
    ensure_root()
    # Get sudo user
    normal_user = detect_user()
    # Update nixos config
    nixos_config_pull()

    # Run root upgrade commands
    for cmd in upgrade_cmd_list:
        print(f"Running {shlex.join(cmd)}")
        subprocess.run(cmd, check=True)

    # Non-root commands
    for cmd in update_cmd_nonroot_list:
        CFunc.run_as_user(user_name=normal_user, cmd_list=cmd, error_on_fail=True)
