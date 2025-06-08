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
url_vclib = "https://aka.ms/Microsoft.VCLibs.x64.14.00.Desktop.appx"
url_uixaml = "https://www.nuget.org/api/v2/package/Microsoft.UI.Xaml"
url_winget_msix = "https://github.com/microsoft/winget-cli/releases/download/v1.10.390/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle"
url_winget_lic = "https://github.com/microsoft/winget-cli/releases/download/v1.10.390/e53e159d00e04f729cc2180cffd1c02e_License1.xml"
url_msstore_giturl = "https://github.com/QuangVNMC/Add-Microsoft-Store"


### Utility Functions ###
def pwsh_run(cmd: list = [], error_on_fail: bool = True):
    """Run a command with powershell."""
    subprocess.run([powershell_cmd_fullpath, "-c", cmd], check=error_on_fail)
def pwsh_subpout(cmd: str):
    """Run a command with poershell and get its output."""
    output = subprocess.run([powershell_cmd_fullpath, "-c", cmd], stdout=subprocess.PIPE, check=False, universal_newlines=True).stdout.strip()
    return output
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
def Util_WingetInstall():
    """
    Install winget
    https://learn.microsoft.com/en-us/windows/iot/iot-enterprise/deployment/install-winget-windows-iot
    """
    tempfolder = tempfile.gettempdir()
    # Download VCLib
    file_vclib = CFunc.downloadfile(url_vclib, tempfolder)
    # Install VCLib
    pwsh_run(cmd=f"Add-AppxPackage {file_vclib[0]}", error_on_fail=False)
    # Download UI Xaml
    file_zip_uixaml = CFunc.downloadfile(url_uixaml, tempfolder)
    uixaml_folder = os.path.join(tempfolder, "uixaml")
    os.makedirs(uixaml_folder, exist_ok=True)
    subprocess.run([r"C:\Program Files\7-Zip\7z.exe", "x", "-aoa", file_zip_uixaml[0], f"-o{uixaml_folder}"], check=True)
    # Install UI Xaml
    file_uixaml_appx = None
    regex = re.compile('(.*appx$)')
    for root, dirs, files in os.walk(os.path.join(uixaml_folder, "tools", "AppX", "x64", "Release")):
        for file in files:
            if regex.match(file):
                file_uixaml_appx = os.path.join(uixaml_folder, "tools", "AppX", "x64", "Release", file)
    pwsh_run(cmd=f"Add-AppxPackage {file_uixaml_appx}", error_on_fail=False)
    # Download winget
    file_winget_msix = CFunc.downloadfile(url_winget_msix, tempfolder)
    file_winget_lic = CFunc.downloadfile(url_winget_lic, tempfolder)
    # Install winget
    pwsh_run(cmd=f"Add-AppxPackage {file_winget_msix[0]}", error_on_fail=False)
    # Configure the WinGet client with the correct license
    pwsh_run(cmd=f"Add-AppxProvisionedPackage -Online -PackagePath {file_winget_msix[0]} -LicensePath {file_winget_lic[0]}", error_on_fail=False)
    pwsh_run(cmd="Repair-WinGetPackageManager -AllUsers -Force -Latest")
    # Cleanup
    os.remove(file_vclib[0])
    shutil.rmtree(uixaml_folder, ignore_errors=True)
    shutil.rmtree(file_zip_uixaml[0], ignore_errors=True)
    os.remove(file_winget_msix[0])
    os.remove(file_winget_lic[0])
    return
def Util_MSStore():
    """Install Microsoft Store"""
    mst_folder = os.path.join(USERHOME, "Documents", "Add-Microsoft-Store")
    mst_script = os.path.join(mst_folder, "Add-Store.cmd")
    # Clone the repo
    CFunc.gitclone(url_msstore_giturl, mst_folder)
    # Remove the pause after running
    CFunc.find_replace(mst_folder, 'pause >nul', '', "Add-Store.cmd")
    # Run script
    subprocess.run(mst_script)
    return
def Util_WinTerminalInstall():
    """Install Windows Terminal"""
    pwsh_run("winget install --accept-package-agreements --accept-source-agreements --disable-interactivity --id Microsoft.WindowsTerminal -e", error_on_fail=False)
    TargetPath = r"shell:AppsFolder\Microsoft.WindowsTerminal_8wekyb3d8bbwe!App"
    shortcutfile = os.path.join(os.getenv("PUBLIC"), "Desktop", "Windows Terminal.lnk")
    pwsh_run(f"""
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{shortcutfile}")
$Shortcut.TargetPath = "{TargetPath}"
$Shortcut.Save()
""")
    return

# Utility Variables
vmtype = win_vmtype()
ostype = win_ostype()


### Code Functions ###
def SoftwareInstall():
    """Install software"""
    if ostype == 2:
        Util_MSStore()
    # Windows Terminal
    Util_WinTerminalInstall()
    return


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Provision a new Windows install.')
    parser.add_argument("-n", "--noprompt", help="No prompt")
    args = parser.parse_args()

    ### Begin Code ###
    SoftwareInstall()
