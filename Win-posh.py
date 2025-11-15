#!/usr/bin/env python3
"""Powershell configuration."""

# Python includes.
import argparse
import json
import os
import shutil
import subprocess
import tempfile
# Custom includes
import CFunc
import Wprovision

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
# Get powershell command
powershell_cmd = "pwsh.exe"
powershell_cmd_fullpath = shutil.which(powershell_cmd)

# Get arguments
parser = argparse.ArgumentParser(description='Install Windows shell configuration.')
args = parser.parse_args()


### Functions ###
def GetJsonFromFile(filePath):
    """
    Strip comments from json.
    https://stackoverflow.com/a/57814048
    """
    contents = ""
    fh = open(filePath)
    for line in fh:
        if len(line) > 0 and line.endswith("\n") and "\n" not in line:
            line += "\n"
        contents += line
    fh.close()
    while "/*" in contents:
        preComment, postComment = contents.split("/*", 1)
        contents = preComment + postComment.split("*/", 1)[1]
    return contents


### Powershell Configuration ###
# Remove profile
# subprocess.run([powershell_cmd_fullpath, "-c", "Remove-Item", "$PROFILE"], check=False)
Wprovision.pwsh_run(["Remove-Item", "$PROFILE"], error_on_fail=False)
# Install powershell modules
print("Install powershell modules.")
Wprovision.pwsh_run(["Set-PSRepository", "-Name", "PSGallery", "-InstallationPolicy", "Trusted"])
Wprovision.pwsh_run(["Install-Module", "-Name", 'posh-git', "-AllowClobber"])
Wprovision.pwsh_run(["Install-Module", "-Name", "'Get-ChildItemColor'", "-AllowClobber"])
Wprovision.pwsh_run(["Install-Module", "-Name", "'PSReadLine'", "-AllowClobber", "-Force"])
Wprovision.pwsh_run(["Set-ExecutionPolicy", "Bypass", "-Scope", "Process", "-Force"])
# https://ohmyposh.dev/docs/installation/windows
Wprovision.pwsh_run(["winget install --disable-interactivity --uninstall-previous --force JanDeDobbeleer.OhMyPosh -s winget"])
# Powershell font
subprocess.run("choco upgrade -y cascadiacodepl", shell=True, check=False)


# Install powershell profile
powershell_profile_script = CFunc.subpout('{0} -c "echo $PROFILE"'.format(powershell_cmd))
powershell_profile_folder = os.path.dirname(powershell_profile_script)

powershell_profile_text = """<#
.SYNOPSIS
  Powershell Profile.
#>

# Ensure that Get-ChildItemColor is loaded
Import-Module Get-ChildItemColor

# Ensure posh-git is loaded
Import-Module -Name posh-git

# Ensure oh-my-posh is loaded
oh-my-posh init pwsh --config "agnosterplus" | Invoke-Expression


### Functions ###
Function Format-FileSize() {
    Param ([int]$size)
    If     ($size -gt 1TB) {[string]::Format("{0:0.00} TB", $size / 1TB)}
    ElseIf ($size -gt 1GB) {[string]::Format("{0:0.00} GB", $size / 1GB)}
    ElseIf ($size -gt 1MB) {[string]::Format("{0:0.00} MB", $size / 1MB)}
    ElseIf ($size -gt 1KB) {[string]::Format("{0:0.00} kB", $size / 1KB)}
    ElseIf ($size -gt 0)   {[string]::Format("{0:0.00} B", $size)}
    Else                   {""}
}
Function Fcn-List-All {
    Get-ChildItemColor | Select-Object Mode, @{Name="Size";Expression={Format-FileSize($_.Length)}}, LastWriteTime, Name
}


### Aliases ###
# Set la and ls alias to use the new Get-ChildItemColor cmdlets
# Set-Alias -Name la -Value Fcn-List-All
Set-Alias l Get-ChildItemColor -option AllScope
Set-Alias la Get-ChildItemColor -option AllScope
Set-Alias ls Get-ChildItemColorFormatWide -Option AllScope
# which
function which($name) {
    Get-Command $name | Select-Object -ExpandProperty Definition
}
# topgrade
Set-Alias up topgrade

"""
os.makedirs(powershell_profile_folder, exist_ok=True)
with open(powershell_profile_script, 'w') as powershell_profile_script_handle:
    powershell_profile_script_handle.write(powershell_profile_text)

# Set Windows Terminal font
winterminal_json_file = os.path.join(USERHOME, "AppData", "Local", "Packages", "Microsoft.WindowsTerminal_8wekyb3d8bbwe", "LocalState", "settings.json")
if os.path.isfile(winterminal_json_file):
    winterminal_json_raw = GetJsonFromFile(winterminal_json_file)
    # Print the preprocessed json file, for debugging purposes.
    # print(winterminal_json_raw)
    data = json.loads(winterminal_json_raw)
    # Print the json loaded into python, for debugging purposes.
    # print(json.dumps(data['profiles']['list'][0], indent=4))
    for val in data['profiles']['list']:
        if "fontFace" not in val:
            if val['name'] == "Windows PowerShell" or val['name'] == "PowerShell":
                val["fontFace"] = "Cascadia Code PL"
    # Create temporary json
    temp_json_file = os.path.join(tempfile.gettempdir(), os.path.basename("temp.json"))
    with open(temp_json_file, 'w') as f:
        json.dump(data, f, indent=4)
    # Replace old settings.json with new.
    os.replace(temp_json_file, winterminal_json_file)
else:
    print("ERROR: {0} not found. Please load Windows Terminal at least once to create settings.json file.".format(winterminal_json_file))


### Cygwin ###
# Check if cygwin is installed already.
cygwin_bash_cmd = os.path.join("c:", os.sep, "cygwin64", "bin", "bash.exe")
if os.path.isfile(cygwin_bash_cmd):
    # Install apt-cyg
    documents_folder = os.path.join(USERHOME, "Documents")
    aptcyg_folder = os.path.join(documents_folder, "apt-cyg")
    cwd = os.getcwd()
    if os.path.isdir(aptcyg_folder):
        os.chdir(aptcyg_folder)
        subprocess.run("git checkout -f", shell=True, check=True)
        subprocess.run("git pull", shell=True, check=True)
    else:
        subprocess.run("git clone {0} {1}".format("https://github.com/resistancelion/apt-cyg", os.path.join(documents_folder, "apt-cyg")), shell=True, check=True)
    os.chdir(documents_folder)

    subprocess.run([cygwin_bash_cmd, "-c", '/usr/bin/ln -sf "$(/usr/bin/realpath apt-cyg/apt-cyg)" /usr/local/bin/'], cwd=documents_folder, check=True)
    subprocess.run([cygwin_bash_cmd, "-c", '/usr/bin/ln -sf "$(/usr/bin/realpath apt-cyg/apt-cyg)" /usr/local/bin/apt'], cwd=documents_folder, check=True)

    # Install required packages
    subprocess.run([cygwin_bash_cmd, '-c', '. /etc/profile; /usr/local/bin/apt-cyg -X install wget ca-certificates gnupg'], check=True)
