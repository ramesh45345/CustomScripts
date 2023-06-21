#!/usr/bin/env python3
"""Install Appimage Software"""

# Python includes.
import argparse
import glob
import os
import subprocess
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Exit if root.
CFunc.is_root(False)

# Global variables
USERHOME = os.path.expanduser('~')
localapps_folder = os.path.join(USERHOME, ".local", "share", "applications")
appimageapp_folder = os.path.join(USERHOME, "Applications")

def Cleanup_appimaged():
    """Cleanup and remove appimaged."""
    subprocess.run("systemctl --user disable --now appimaged.service", shell=True, check=False)
    if os.path.isfile(os.path.join(USERHOME, ".config", "systemd", "user", "appimaged.service")):
        os.remove(os.path.join(USERHOME, ".config", "systemd", "user", "appimaged.service"))
    if os.path.isdir(localapps_folder):
        desktopfiles = glob.glob('{0}/appimagekit*.desktop'.format(localapps_folder), recursive=True)
        for x in desktopfiles:
            os.remove(x)
    else:
        print("{0} not found. Skipping delete.".format(localapps_folder))
    if os.path.isdir(appimageapp_folder):
        appimagesapps = glob.glob('{0}/appimaged-*-x86_64.AppImage'.format(appimageapp_folder), recursive=True)
        for x in appimagesapps:
            os.remove(x)
    else:
        print("{0} not found. Skipping delete.".format(appimageapp_folder))
def Setup_appimaged():
    """Setup appimaged for user."""
    # Create folders
    os.makedirs(localapps_folder, exist_ok=True)
    os.makedirs(appimageapp_folder, exist_ok=True)
    # Get release name
    appimage_release = CFunc.subpout('''wget -q https://github.com/probonopd/go-appimage/releases -O - | grep "appimaged-.*-x86_64.AppImage" | head -n 1 | cut -d '"' -f 2''')
    print(appimage_release)
    # Download release
    CFunc.downloadfile("https://github.com/{0}".format(appimage_release), appimageapp_folder)
    # Chmod executable the downloaded file.
    appimagesapps = glob.glob('{0}/appimaged-*-x86_64.AppImage'.format(appimageapp_folder), recursive=True)
    for x in appimagesapps:
        os.chmod(x, 0o777)
def Run_appimaged():
    """Run appimaged as the current user."""
    subprocess.run("~/Applications/appimaged-*.AppImage", shell=True, check=False)
def Setup_apps():
    """Setup common apps."""


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Install Appimage Software.')
    parser.add_argument("-c", "--cleanup", help='Only remove appimaged.', action="store_true")
    parser.add_argument("-a", "--apps", help='Also install apps.', action="store_true")
    args = parser.parse_args()

    # Cleanup appimaged
    Cleanup_appimaged()
    if args.cleanup:
        # Exit right after cleanup.
        exit()
    # Setup appimaged
    Setup_appimaged()
    Run_appimaged()
    # Setup apps
    if args.apps:
        Setup_apps()
