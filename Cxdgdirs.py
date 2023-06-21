#!/usr/bin/env python3
"""Configure/remove xdg dirs."""

# Python includes.
import os
import subprocess
import shutil
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
# This folder is the above detected user's home folder if this script is run as root.
USERVARHOME = os.path.expanduser("~{0}".format(USERNAMEVAR))
# Figure out if we are really root.
rootstate = CFunc.is_root(checkstate=True, state_exit=False)

# Create xdg folders
if rootstate is True and shutil.which("xdg-user-dirs-update"):
    CFunc.run_as_user(USERNAMEVAR, "xdg-user-dirs-update", shutil.which("bash"))
elif rootstate is False and shutil.which("xdg-user-dirs-update"):
    subprocess.run('xdg-user-dirs-update', shell=True)
else:
    print("WARNING: xdg-user-dirs-update command not found")

# xdg dirs configuration
xdgdirs_file = os.path.join(USERVARHOME, ".config", "user-dirs.dirs")
if os.path.isfile(xdgdirs_file):
    CFunc.find_replace(os.path.join(USERVARHOME, ".config"), "Downloads", "", "user-dirs.dirs")
    if os.path.isdir(os.path.join(USERVARHOME, "Downloads")):
        shutil.rmtree(os.path.join(USERVARHOME, "Downloads"), ignore_errors=True)
    CFunc.find_replace(os.path.join(USERVARHOME, ".config"), "Templates", "", "user-dirs.dirs")
    if os.path.isdir(os.path.join(USERVARHOME, "Templates")):
        shutil.rmtree(os.path.join(USERVARHOME, "Templates"), ignore_errors=True)
    CFunc.find_replace(os.path.join(USERVARHOME, ".config"), "Public", "", "user-dirs.dirs")
    if os.path.isdir(os.path.join(USERVARHOME, "Public")):
        shutil.rmtree(os.path.join(USERVARHOME, "Public"), ignore_errors=True)
    CFunc.find_replace(os.path.join(USERVARHOME, ".config"), "Documents", "", "user-dirs.dirs")
    if os.path.isdir(os.path.join(USERVARHOME, "Documents")):
        shutil.rmtree(os.path.join(USERVARHOME, "Documents"), ignore_errors=True)
    CFunc.find_replace(os.path.join(USERVARHOME, ".config"), "Pictures", "", "user-dirs.dirs")
    if os.path.isdir(os.path.join(USERVARHOME, "Pictures")):
        shutil.rmtree(os.path.join(USERVARHOME, "Pictures"), ignore_errors=True)
    CFunc.find_replace(os.path.join(USERVARHOME, ".config"), "Music", "", "user-dirs.dirs")
    if os.path.isdir(os.path.join(USERVARHOME, "Music")):
        shutil.rmtree(os.path.join(USERVARHOME, "Music"), ignore_errors=True)
    CFunc.find_replace(os.path.join(USERVARHOME, ".config"), "Videos", "", "user-dirs.dirs")
    if os.path.isdir(os.path.join(USERVARHOME, "Videos")):
        shutil.rmtree(os.path.join(USERVARHOME, "Videos"), ignore_errors=True)

# Create ~/.local/share/applications folder, and set permissions.
app_folder = os.path.join(USERVARHOME, ".local", "share", "applications")
if not os.path.isdir(app_folder):
    os.makedirs(app_folder, exist_ok=True)
    subprocess.run("chown -R {0}:{1} {2}".format(USERNAMEVAR, USERGROUP, os.path.join(USERVARHOME, ".local")), shell=True)
