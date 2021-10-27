#!/usr/bin/env python3
"""Install Flatpak Software"""

# Python includes.
import argparse
import sys
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]

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
    CFunc.flatpak_install("flathub", "net.cozic.joplin_desktop")
    # Media apps
    CFunc.flatpak_install("flathub", "org.videolan.VLC")
    CFunc.flatpak_install("flathub", "org.atheme.audacious")
    CFunc.flatpak_install("flathub", "io.github.quodlibet.QuodLibet")

    # Configure permissions for apps
    CFunc.flatpak_override("org.atheme.audacious", "--filesystem=host")
