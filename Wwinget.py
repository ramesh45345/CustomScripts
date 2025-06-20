#!/usr/bin/env python3
"""Provision winget related Windows software."""

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
import Wprovision

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
url_msstore_giturl = "https://github.com/R-YaTian/LTSC-Add-MicrosoftStore-2021_2024"


### Utility Functions ###
def Util_WingetInstall():
    """
    Install winget
    https://learn.microsoft.com/en-us/windows/iot/iot-enterprise/deployment/install-winget-windows-iot
    """
    tempfolder = tempfile.gettempdir()
    # Download VCLib
    file_vclib = CFunc.downloadfile(url_vclib, tempfolder)
    # Install VCLib
    Wprovision.pwsh_run(cmd=f"Add-AppxPackage {file_vclib[0]}", error_on_fail=False)
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
    Wprovision.pwsh_run(cmd=f"Add-AppxPackage {file_uixaml_appx}", error_on_fail=False)
    # Download winget
    file_winget_msix = CFunc.downloadfile(url_winget_msix, tempfolder)
    file_winget_lic = CFunc.downloadfile(url_winget_lic, tempfolder)
    # Install winget
    Wprovision.pwsh_run(cmd=f"Add-AppxPackage {file_winget_msix[0]}", error_on_fail=False)
    # Configure the WinGet client with the correct license
    Wprovision.pwsh_run(cmd=f"Add-AppxProvisionedPackage -Online -PackagePath {file_winget_msix[0]} -LicensePath {file_winget_lic[0]}", error_on_fail=False)
    Wprovision.pwsh_run(cmd="Repair-WinGetPackageManager -AllUsers -Force -Latest")
    # Cleanup
    os.remove(file_vclib[0])
    shutil.rmtree(uixaml_folder, ignore_errors=True)
    shutil.rmtree(file_zip_uixaml[0], ignore_errors=True)
    os.remove(file_winget_msix[0])
    os.remove(file_winget_lic[0])
    return
def Util_MSStore():
    """Install Microsoft Store"""
    mst_folder = os.path.join(USERHOME, "Documents", "LTSC-Add-MicrosoftStore-2021_2024")
    mst_script = os.path.join(mst_folder, "Add-Store.cmd")
    # Clone the repo
    try:
        CFunc.gitclone(url_msstore_giturl, mst_folder)
    except:
        if not os.path.isfile(mst_script):
            raise Exception(f"ERROR: {mst_folder} was not cloned successfully.")
    # Remove the pause after running
    CFunc.find_replace(mst_folder, '''set /p choice="Do you want to install latest DesktopAppInstaller with winget included? This may take a while.(Y/N): "''', '', "Add-Store.cmd")
    CFunc.find_replace(mst_folder, '''set choice=%choice:~0,1%''', 'set choice=Y', "Add-Store.cmd")
    CFunc.find_replace(mst_folder, 'pause >nul', '', "Add-Store.cmd")
    # Run script
    subprocess.run(mst_script)
    return
def Util_WinTerminalInstall():
    """Install Windows Terminal"""
    print("Install Windows Terminal")
    Wprovision.pwsh_run("winget install --accept-package-agreements --accept-source-agreements --disable-interactivity --id Microsoft.WindowsTerminal -e", error_on_fail=False)
    TargetPath = r"shell:AppsFolder\Microsoft.WindowsTerminal_8wekyb3d8bbwe!App"
    shortcutfile = os.path.join(os.getenv("PUBLIC"), "Desktop", "Windows Terminal.lnk")
    Wprovision.pwsh_run(f"""
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{shortcutfile}")
$Shortcut.TargetPath = "{TargetPath}"
$Shortcut.Save()
""")
    return

# Utility Variables
vmtype = Wprovision.win_vmtype()
ostype = Wprovision.win_ostype()


### Code Functions ###
def WingetSoftwareInstall():
    """Install software depending on MSStore/winget."""
    if ostype == 2:
        Util_MSStore()
    if CFunc.commands_check(["winget"], exit_if_fail=False):
        # Windows Terminal
        Util_WinTerminalInstall()
    else:
        print("ERROR: Winget not found. Skipping provision.")
    return


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Provision a new Windows install using commands that rely on winget.')
    parser.add_argument("-n", "--noprompt", help="No prompt")
    args = parser.parse_args()

    ### Begin Code ###
    Wprovision.win_add_path("git", r"C:\Program Files\Git\cmd")
    WingetSoftwareInstall()
