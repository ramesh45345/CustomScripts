#!/usr/bin/env python3
"""Provision a new Windows install."""

# Python includes.
import argparse
import functools
import os
import re
import shutil
import subprocess
import tempfile
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))


### Global Variables ###
# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
# Get powershell command
powershell_cmd = "pwsh.exe"
powershell_cmd_fullpath = shutil.which(powershell_cmd)
# Urls


### Utility Functions ###
def pwsh_run(cmd: list = [], error_on_fail: bool = True):
    """Run a command with powershell."""
    subprocess.run([powershell_cmd_fullpath, "-c", cmd], check=error_on_fail)
def pwsh_subpout(cmd: str):
    """Run a command with powershell and get its output."""
    output = subprocess.run([powershell_cmd_fullpath, "-c", cmd], stdout=subprocess.PIPE, check=False, universal_newlines=True).stdout.strip()
    return output
def win_add_path(cmd: str, path: str):
    """"""
    if not shutil.which(cmd) and os.path.isdir(path):
        os.environ['PATH'] += f';{path}'
    return
def win_vmtype() -> int:
    """
    Return the VM type.
    0: Not a VM
    1: virtualbox
    2: qemu
    """
    out_model = pwsh_subpout("(Get-CimInstance -ClassName Win32_ComputerSystem).Model")
    out_manufacturer = pwsh_subpout("(Get-CimInstance -ClassName Win32_ComputerSystem).Manufacturer")
    if "virtualbox" in out_model.lower():
        vmtype = 1
    elif "qemu" in out_manufacturer.lower():
        vmtype = 2
    else:
        vmtype = 0
    return vmtype
def win_ostype() -> int:
    """
    Return the OS type.
    1: Windows 11
    2: LTSC
    3: Server
    """
    ostype = 1
    out = pwsh_subpout("(systeminfo /fo csv | ConvertFrom-Csv).'OS Name'")
    if "Enterprise LTSC" in out:
        ostype = 2
    elif "Windows Server" in out:
        ostype = 3
    return ostype


# Utility Variables
vmtype = win_vmtype()
ostype = win_ostype()


### Code Functions ###
def SoftwareInstall():
    """Install software."""

    return


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Provision a new Windows install.')
    parser.add_argument("-n", "--noprompt", help="No prompt")
    args = parser.parse_args()

    ### Begin Code ###
    win_add_path("git", r"C:\Program Files\Git\cmd")
    SoftwareInstall()
