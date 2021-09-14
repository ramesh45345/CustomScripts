#!/usr/bin/env python3
"""Set Mime Types"""

# Python includes.
import argparse
import fnmatch
import glob
import os
import re
import shutil
import sys
import subprocess

# Folder of this script
SCRIPTDIR = sys.path[0]

# Global variables
types_archive = "application/x-7z-compressed,application/x-xz-compressed-tar,application/zip,application/x-compressed-tar,application/x-bzip-compressed-tar,application/x-tar,application/x-xz"
types_audio = "application/octet-stream,audio/flac,audio/mpeg,audio/ogg,audio/x-m4a"
types_text = "text/plain"

### Functions ###
def Mime_CheckCmds():
    """Check for required utilities."""
    cmdcheck = ["xdg-mime"]
    for cmd in cmdcheck:
        if not shutil.which(cmd):
            sys.exit("\nError, ensure command {0} is installed.".format(cmd))
def Mime_Set(mimetype: str, app: str):
    """Set mime-type."""
    subprocess.run(["xdg-mime", "default", app, mimetype], check=False)
def Mime_Query(mimetype: str):
    """Query currently set mime-type."""
    output = subprocess.run(["xdg-mime", "query", "default", mimetype], stdout=subprocess.PIPE, universal_newlines=True, check=False).stdout.strip()
    print("Mime: {0}\tSetting: {1}".format(mimetype, output))
def Mime_Set_All(mimes: str, app: str):
    """
    Set all mime-types.
    mimes should be comma delimited.
    """
    if FindDesktopFile(app) is False:
        print("ERROR: desktop file {0} not found.".format(app))
    split_mimes = mimes.split(",")
    for mime in split_mimes:
        Mime_Set(mime, app)
def Mime_Query_All(mimes):
    """
    Query all mime-types.
    mimes should be comma delimited.
    """
    split_mimes = mimes.split(",")
    for mime in split_mimes:
        Mime_Query(mime)
def HandlePredefines(predefines, app):
    """Query or set pre-defined types."""
    selecteddefine = None
    if predefines == "archive":
        selecteddefine = types_archive
    elif predefines == "text":
        selecteddefine = types_text
    elif predefines == "audio":
        selecteddefine = types_audio
    # Set types if app is defined
    if app:
        Mime_Set_All(selecteddefine, app)
    # Query types
    Mime_Query_All(selecteddefine)
def LocateDesktopFile(desktop_search_term: str):
    """Search for a desktop file."""
    desktopref = []
    XDG_DATA_DIRS = os.environ.get('XDG_DATA_DIRS').split(":")
    for xdg_folder in XDG_DATA_DIRS:
        xdg_app_folder = os.path.join(xdg_folder, "applications")
        if os.path.isdir(xdg_app_folder):
            list_path = [i for i in os.listdir(xdg_app_folder) if os.path.isfile(os.path.join(xdg_app_folder, i))]
            desktopref += [os.path.join(xdg_app_folder, j) for j in list_path if re.match(fnmatch.translate("*{0}*".format(desktop_search_term)), j, re.IGNORECASE)]
    return desktopref
def FindDesktopFile(desktop_ref: str):
    """Find out if a desktop file exists."""
    desktopref_exists = False
    XDG_DATA_DIRS = os.environ.get('XDG_DATA_DIRS').split(":")
    for xdg_folder in XDG_DATA_DIRS:
        xdg_app_folder = os.path.join(xdg_folder, "applications")
        if os.path.isdir(xdg_app_folder):
            if glob.glob(os.path.join(xdg_app_folder, desktop_ref)):
                desktopref_exists = True
    return desktopref_exists


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Enter a chroot.')
    parser.add_argument("-s", "--set", help='Set mimetypes. (i.e. application/"x-7z-compressed,application/x-xz-compressed-tar". Must set app with this option.')
    parser.add_argument("-a", "--application", help='Application to set mimetype to (i.e. "org.kde.ark.desktop". Must be used with set options.')
    parser.add_argument("-q", "--query", help='Query mimetypes. (i.e. "application/x-7z-compressed,application/x-xz-compressed-tar")')
    parser.add_argument("-p", "--predefines", help='Set or query predefines. Set when combined with -a flag. Options: archive,text,audio')
    args = parser.parse_args()

    # Ensure proper commands are on system.
    Mime_CheckCmds()

    # Query command
    if args.query:
        Mime_Query_All(args.query)
    # Passed set command
    elif args.set:
        Mime_Set_All(args.set, args.application)
        # Confirm settings
        Mime_Query_All(args.set)
    elif args.predefines:
        HandlePredefines(args.predefines, args.application)
