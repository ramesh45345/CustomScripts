#!/usr/bin/env python3
"""Create a Windows install ISO."""

# Python includes.
import argparse
from datetime import datetime
import functools
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import traceback
# Custom includes
import CFunc
import Wprovision

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

### Global Variables ###
url_vclib = "https://aka.ms/Microsoft.VCLibs.x64.14.00.Desktop.appx"
url_winget_msix = "https://github.com/microsoft/winget-cli/releases/download/v1.11.400/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
url_winget_lic = "https://github.com/microsoft/winget-cli/releases/download/v1.11.400/e53e159d00e04f729cc2180cffd1c02e_License1.xml"
oscdimg_folder = os.path.join("C:", os.sep, "Program Files (x86)", "Windows Kits", "10", "Assessment and Deployment Kit", "Deployment Tools", "amd64", "Oscdimg")
# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
root_files_path = os.path.join(USERHOME, "Downloads")


### Utility Functions ###
def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal"""
    os.chmod(path, stat.S_IWRITE)
    func(path)
def ISO_Mount(isopath):
    """Mount an ISO."""
    Wprovision.pwsh_run(["Mount-DiskImage", "-ImagePath", isopath])
    return
def ISO_Dismount(isopath):
    """Dismount an ISO"""
    Wprovision.pwsh_run(["Dismount-DiskImage", "-ImagePath", isopath])
    return
def ISO_Create(oscdimg_folder: str, iso_files_path: str, iso_out_file: str, debug: bool = False):
    cmd_list = ['oscdimg', '-m', '-o', '-u2', '-udfver102', f'-bootdata:2#p0,e,b{os.path.join(oscdimg_folder, "etfsboot.com")}#pEF,e,b{os.path.join(oscdimg_folder, "efisys.bin")}', iso_files_path, iso_out_file]
    if debug is True:
        print(f"Command: {cmd_list}")
    subprocess.run(cmd_list, check=True)
    return
def WIM_Mount(mountdir: str, wimfile: str, debug: bool = False):
    """Mount a wim file."""
    if not os.path.isdir(mountdir):
        os.makedirs(mountdir, exist_ok=True)
    cmd_list = ["dism", "/Mount-Wim", f'/WimFile:{wimfile}', "/Index:1", f'/MountDir:{mountdir}']
    if debug is True:
        print(f"Command: {cmd_list}")
    subprocess.run(cmd_list, check=True)
    return
def WIM_Dismount(mountdir: str, discard: bool = False, debug: bool = False):
    """Dismount a wim file."""
    unmount_type = "/commit"
    error_on_fail = True
    if discard is True:
        unmount_type = "/discard"
        error_on_fail = False
    cmd_list = ["dism", "/unmount-wim", f'/mountdir:{mountdir}', unmount_type]
    if debug is True:
        print(f"Command: {cmd_list}")
    subprocess.run(cmd_list, check=error_on_fail)
    return


### Code Functions ###
def ADK_Install():
    fullpath, filename = CFunc.downloadfile("https://go.microsoft.com/fwlink/?linkid=2289980", os.path.join(root_files_path, "adksetup.exe"))
    subprocess.run([fullpath, "/q", "/ceip", "off", "/norestart"])
    return
def DISM_Integrate_winget(mountdir: str, debug: bool = False):
    try:
        file_vclib = CFunc.downloadfile(url_vclib, root_files_path)
        file_winget_msix = CFunc.downloadfile(url_winget_msix, root_files_path)
        file_winget_lic = CFunc.downloadfile(url_winget_lic, root_files_path)
        cmd_list = ['dism', f'/Image:{mountdir}', '/Add-ProvisionedAppxPackage', f'/PackagePath:{file_winget_msix[0]}', f'/DependencyPackagePath:{file_vclib[0]}', f'/LicensePath:{file_winget_lic[0]}', '/region=all']
        if debug is True:
            print(f"Command: {cmd_list}")
        subprocess.run(cmd_list, check=True)
    finally:
        # Cleanup
        if not args.debug:
            os.remove(file_vclib[0])
            os.remove(file_winget_msix[0])
            os.remove(file_winget_lic[0])
    return


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Create a Windows install ISO.')
    parser.add_argument("-a", "--adk", help="Install adk.")
    parser.add_argument("-d", "--debug", help="Don't clean up files.", action="store_true")
    parser.add_argument("-i", "--input", help="ISO source")
    parser.add_argument("-n", "--noprompt", help="No prompt")
    parser.add_argument("-o", "--output", help="Output ISO (default: %(default)s)", default=root_files_path)
    args = parser.parse_args()

    # Validate Inputs
    if not os.path.isfile(args.input):
        print("ERROR, {args.input} not found.")
        sys.exit(1)
    iso_fullpath = os.path.abspath(args.input)

    ### Begin Code ###
    iso_files_path = os.path.join(root_files_path, "isofiles")

    # adkinstall
    if args.adk:
        ADK_Install()
    # oscimg path
    Wprovision.win_add_path("oscdimg", oscdimg_folder)
    if not shutil.which("oscdimg"):
        print(f"ERROR: oscdimg tool or path {oscdimg_folder} not found. Exiting.")
        sys.exit(1)

    # iso processing
    if not args.debug and not os.path.isdir(iso_files_path):
        try:
            # Mount the iso
            ISO_Mount(args.input)
            iso_drive = Wprovision.pwsh_subpout(f'(Get-DiskImage -ImagePath "{args.input}" | Get-Volume).DriveLetter') + ":"
            # Clean files if it exists
            if os.path.isdir(iso_files_path):
                shutil.rmtree(iso_files_path, onexc=remove_readonly)
            # Copy files
            print(f"Copying files from {iso_drive} to {iso_files_path}. May take some time.")
            shutil.copytree(os.path.join(iso_drive), iso_files_path)
            # Set files as read-write
            subprocess.run(['attrib', '-s', '-h', '-r', f'{iso_files_path}\\*.*', '/s', '/d'], check=True)
        except:
            print(traceback.format_exc())
        finally:
            ISO_Dismount(args.input)

    # Validate Wim path
    wim_path = os.path.join(iso_files_path, "sources", "install.wim")
    wim_mount_path = os.path.join(root_files_path, "wim_mount")

    if not os.path.isfile(wim_path):
        raise Exception(f"ERROR: {wim_path} does not exist.")
    WIM_Mount(mountdir=wim_mount_path, wimfile=wim_path, debug=args.debug)

    try:
        # Modify Wim
        DISM_Integrate_winget(mountdir=wim_mount_path, debug=args.debug)
        # Save the wim
        WIM_Dismount(mountdir=wim_mount_path, discard=False, debug=args.debug)
        # Create ISO
        current_time = datetime.now().strftime("%Y-%m-%dT%H.%M.%SZ")
        iso_filename = Path(iso_fullpath).stem + f"_custom_{current_time}.iso"
        ISO_Create(oscdimg_folder, iso_files_path, iso_out_file=os.path.join(args.output, iso_filename), debug=args.debug)
    except:
        print(traceback.format_exc())
        WIM_Dismount(mountdir=wim_mount_path, discard=True, debug=args.debug)
    finally:
        if os.path.isdir(iso_files_path) and not args.debug:
            shutil.rmtree(iso_files_path, onexc=remove_readonly)
        if os.path.isdir(wim_mount_path) and not args.debug:
            shutil.rmtree(wim_mount_path, onexc=remove_readonly)
