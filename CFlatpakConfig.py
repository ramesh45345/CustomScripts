#!/usr/bin/env python3
"""Install Flatpak Software"""

# Python includes.
import argparse
import os
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Install Flatpak Software.')
parser.add_argument("-r", "--configure_remotes", help='Add remotes only.', action="store_true")

# Save arguments.
args = parser.parse_args()

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)


# Remote configuration
CFunc.flatpak_addremote("flathub", "https://flathub.org/repo/flathub.flatpakrepo")

if args.configure_remotes is False:
    # Flatpak apps
    CFunc.flatpak_install("flathub", "com.calibre_ebook.calibre")
    CFunc.flatpak_install("flathub", "com.github.tchx84.Flatseal")
    CFunc.flatpak_install("flathub", "org.mozilla.Thunderbird")
    CFunc.flatpak_install("flathub", "com.borgbase.Vorta")
    CFunc.flatpak_install("flathub", "org.libreoffice.LibreOffice")
    # Media apps
    CFunc.flatpak_install("flathub", "org.videolan.VLC")
    CFunc.flatpak_install("flathub", "info.smplayer.SMPlayer")
    CFunc.flatpak_install("flathub", "org.atheme.audacious")
    CFunc.flatpak_install("flathub", "io.github.quodlibet.QuodLibet")
    CFunc.flatpak_install("flathub", "org.gnome.EasyTAG")
    # Meld
    if not CFunc.is_nixos():
        CFunc.flatpak_install("flathub", "org.gnome.meld")
        meld_bin_path = os.path.join(os.sep, "usr", "local", "bin", "meld")
        with open(meld_bin_path, 'w') as f:
            f.write("#!/bin/sh\nflatpak run org.gnome.meld $@")
        os.chmod(meld_bin_path, 0o755)

    # Configure permissions for apps
    CFunc.flatpak_override("org.atheme.audacious", "--filesystem=host")
    CFunc.flatpak_override("org.gnome.EasyTAG", "--filesystem=host")
