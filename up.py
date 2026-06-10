#!/usr/bin/env python3
"""Update script."""
import os
import shutil
import sys
import subprocess
# Custom includes
import CFunc


### Functions ###
def ensure_root():
    """Elevate to root if not running as root"""
    if not CFunc.is_windows() and CFunc.is_root(state_exit=False):
        # Re-run the script with sudo preserving argv
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

# Helper to run commands (list or str). Raises CalledProcessError on failure.
def run(cmd, check=True, shell=False):
    if isinstance(cmd, str) and not shell:
        cmd = cmd.split()
    return subprocess.run(cmd, check=check, shell=shell)

def nixos_rebuild_pull_if_applicable():
    """Pull latest nixos config."""
    if  shutil.which("nixos-rebuild") and os.geteuid() != 0 and os.path.isdir("/etc/nixos"):
        cwd = os.getcwd()
        try:
            os.chdir(os.path.join(os.sep, "etc", "nixos"))
            subprocess.run(["git", "pull"], check=True)
        finally:
            os.chdir(cwd)

def update_topgrade(args):
    # topgrade -y flatpak --disable firmware $@
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


### Begin Code ###
if __name__ == "__main__":
    # Ensure the script is running as root for commands that require it.
    # The original bash uses $SUDOCMD for some commands; here we run as root globally.
    ensure_root()

    # 1) The nixos-rebuild git pull case (note original required non-root uid)
    # Since we've elevated to root above, replicate the original behavior by
    # checking original real UID via environment if available; fallback to performing
    # the pull only when /etc/nixos exists and the original script was non-root.
    # We'll attempt to read SUDO_UID if run under sudo to detect original user.
    original_uid = os.environ.get("SUDO_UID")
    # If SUDO_UID is set then original user wasn't root; if not set and current uid==0 assume we started as root.
    if  shutil.which("nixos-rebuild") and original_uid is not None and os.path.isdir("/etc/nixos"):
        cwd = os.getcwd()
        try:
            os.chdir("/etc/nixos")
            subprocess.run(["git", "pull"])
        finally:
            os.chdir(cwd)

    # 2) System upgrade commands (follow same order/logic)
    # Accept additional args passed to the script and forward them to topgrade if used.
    args = sys.argv[1:]

    if  shutil.which("topgrade"):
        update_topgrade(args)
    elif  shutil.which("rpm-ostree"):
        update_rostree()
    elif  shutil.which("nala"):
        update_nala()
    elif  shutil.which("apt-get"):
        update_apt()
    elif  shutil.which("dnf"):
        update_dnf()
    elif  shutil.which("yay"):
        update_arch()
    elif  shutil.which("zypper"):
        update_zypper()
    elif  shutil.which("nix"):
        # Original condition: type nix &> /dev/null && ! [[ "$(which nix)" == *"$USER"* ]]
        # which nix should not contain the username; replicate that check:
        nix_path = shutil.which("nix") or ""
        user = os.environ.get("SUDO_USER") or os.environ.get("USER") or ""
        if user and user not in nix_path:
            update_nixos()

    # Non-root commands
    if not shutil.which("topgrade"):
        update_distrobox()
