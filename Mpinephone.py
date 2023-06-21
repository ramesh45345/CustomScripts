#!/usr/bin/env python3
"""Provision Pinephone (arch)."""

# Python includes.
import argparse
import os
import shutil
import subprocess
# Custom includes
import CFunc
import CFuncExt
import MArch

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

### Functions ###
def gsettings_set(schema: str, key: str, value: str):
    """Set dconf setting using gsettings."""
    status = subprocess.run(['gsettings', 'set', schema, key, value], check=False).returncode
    if status != 0:
        print("ERROR, failed to run: gsettings set {0} {1} {2}".format(schema, key, value))


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Install Pinephone Arch Software.')
    parser.add_argument("-s", "--stage", help='Stage of installation to run (1 or 2).', type=int, default=0)
    args = parser.parse_args()

    # Get non-root user information.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
    MACHINEARCH = CFunc.machinearch()
    print("Username is:", USERNAMEVAR)
    print("Group Name is:", USERGROUP)
    print("Stage:", args.stage)

    # Root code
    if args.stage == 1:
        print("Running Stage 1.")
        CFunc.is_root(True)
        CFunc.pacman_invoke("-Syu")

        # Install AUR dependencies
        CFunc.pacman_install("base-devel git")

        # Sudoers changes
        CFuncExt.SudoersEnvSettings()
        # Edit sudoers to add pacman.
        sudoersfile = os.path.join(os.sep, "etc", "sudoers.d", "pkmgt")
        CFunc.AddLineToSudoersFile(sudoersfile, "%wheel ALL=(ALL) ALL", overwrite=True)
        CFunc.AddLineToSudoersFile(sudoersfile, "{0} ALL=(ALL) NOPASSWD: {1}".format(USERNAMEVAR, shutil.which("pacman")))
        # Yay
        if not shutil.which("yay"):
            MArch.install_aur_pkg("yay-bin", USERNAMEVAR, USERGROUP)

        # Cli tools
        CFunc.pacman_install("zsh zsh-completions nano tmux iotop rsync p7zip zip unzip unrar xdg-utils xdg-user-dirs")

    if args.stage == 2:
        print("Running Stage 2.")
        CFunc.is_root(False)

        # Shell settings
        gsettings_set("org.gnome.desktop.interface", "clock-show-date", "true")
        gsettings_set("org.gnome.desktop.interface", "clock-format", "'12h'")
        gsettings_set("org.gnome.desktop.interface", "font-antialiasing", "'rgba'")
        gsettings_set("org.gnome.desktop.interface", "show-battery-percentage", "true")
        gsettings_set("org.gnome.desktop.screensaver", "lock-delay", "300")
        gsettings_set("org.gnome.desktop.session", "idle-delay", "60")
        gsettings_set("org.gnome.desktop.wm.preferences", "button-layout", "'appmenu:close'")
        gsettings_set("org.gnome.shell.weather", "automatic-location", "true")
