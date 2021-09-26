#!/usr/bin/env python3
"""Set Mime Types"""

# Python includes.
import argparse
import fnmatch
import glob
import mimetypes
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
types_text = "text/plain,application/x-sh,text/x-python,text/markdown"
predefine_types = ["archive", "text", "audio"]

### Functions ###
def Retrieve_XdgDataDir():
    """Get or create XDG_DATA_DIRS variable."""
    xdg_datadir_var = os.environ.get('XDG_DATA_DIRS')
    if not xdg_datadir_var:
        xdg_datadir_var = "/var/lib/flatpak/exports/share:/usr/local/share:/usr/share:/var/lib/snapd/desktop"
    xdg_datadir_var = xdg_datadir_var.split(":")
    return xdg_datadir_var
def Mime_CheckCmds():
    """Check for required utilities."""
    status = True
    cmdcheck = ["xdg-mime"]
    for cmd in cmdcheck:
        if not shutil.which(cmd):
            print("\nError, ensure command {0} is installed.".format(cmd))
            status = False
    return status
def Mime_Set(mimetype: str, app: str):
    """Set mime-type."""
    if Mime_CheckCmds():
        subprocess.run(["xdg-mime", "default", app, mimetype], check=False)
def Mime_Query(mimetype: str):
    """Query currently set mime-type."""
    if Mime_CheckCmds():
        output = subprocess.run(["xdg-mime", "query", "default", mimetype], stdout=subprocess.PIPE, universal_newlines=True, check=False).stdout.strip()
        print("Mime: {0}\tSetting: {1}".format(mimetype, output))
def Mime_Set_All(mimes: str, app: str):
    """
    Set all mime-types.
    mimes should be comma delimited.
    """
    if FindDesktopFile(app) is False:
        print("ERROR: desktop file {0} not found.".format(app))
    else:
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
    XDG_DATA_DIRS = Retrieve_XdgDataDir()
    for xdg_folder in XDG_DATA_DIRS:
        xdg_app_folder = os.path.join(xdg_folder, "applications")
        if os.path.isdir(xdg_app_folder):
            list_path = [i for i in os.listdir(xdg_app_folder) if os.path.isfile(os.path.join(xdg_app_folder, i))]
            desktopref += [os.path.join(xdg_app_folder, j) for j in list_path if re.match(fnmatch.translate("*{0}*".format(desktop_search_term)), j, re.IGNORECASE)]
    return desktopref
def LocateDesktopFileName(desktop_search_term: str):
    """Return either the basename of the desktop file searched, or None."""
    desktop_basename = None
    desktoplist = LocateDesktopFile(desktop_search_term)
    if len(desktoplist) >= 1:
        desktop_basename = os.path.basename(desktoplist[0])
    return desktop_basename
def FindDesktopFile(desktop_ref: str):
    """Find out if a desktop file exists."""
    desktopref_exists = False
    XDG_DATA_DIRS = Retrieve_XdgDataDir()
    for xdg_folder in XDG_DATA_DIRS:
        xdg_app_folder = os.path.join(xdg_folder, "applications")
        if os.path.isdir(xdg_app_folder):
            if glob.glob(os.path.join(xdg_app_folder, desktop_ref)):
                desktopref_exists = True
    return desktopref_exists
def FindMimeTypes(folder: str = os.getcwd()):
    mimes = []
    if os.path.isdir(folder):
        files = os.listdir(folder)
        for f in files:
            if os.path.isfile(os.path.join(folder, f)):
                f_mime = mimetypes.guess_type(f)[0]
                print(f, "\t", f_mime)
                mimes += [f_mime]
    # Remove duplicates by converting to set and then list. Also, filter out None entries.
    mimes = ",".join(list(filter(None, set(mimes))))
    print("\nMime List:", mimes)
    # Check mime associations
    print("\nAssociations for mimes:")
    Mime_Query_All(mimes)


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Set or query mime types.')
    parser.add_argument("-l", "--locate", help='Search for a .desktop file to serve as a mime handler.')
    parser.add_argument("-s", "--set", help='Set mimetypes. (i.e. application/"x-7z-compressed,application/x-xz-compressed-tar". Must set app with this option.')
    parser.add_argument("-a", "--application", help='Application to set mimetype to (i.e. "org.kde.ark.desktop". Must be used with set options.')
    parser.add_argument("-q", "--query", help='Query mimetypes. (i.e. "application/x-7z-compressed,application/x-xz-compressed-tar")')
    parser.add_argument("-m", "--mimes", help='Check Mimetypes of specified folder.')
    parser.add_argument("-p", "--predefines", help='Set or query predefines. Set when combined with -a flag.', choices=predefine_types)
    args = parser.parse_args()

    # Ensure proper commands are on system.
    if not Mime_CheckCmds():
        sys.exit(0)

    # Query command
    if args.query:
        Mime_Query_All(args.query)
    elif args.locate:
        locatedfiles = LocateDesktopFile(args.locate)
        for f in locatedfiles:
            print(f)
    elif args.mimes:
        FindMimeTypes(args.mimes)
    # Passed set command
    elif args.set:
        Mime_Set_All(args.set, args.application)
        # Confirm settings
        Mime_Query_All(args.set)
    elif args.predefines:
        HandlePredefines(args.predefines, args.application)
