#!/usr/bin/env python3
"""Install VS Code extensions and configuration."""

# Python includes.
import json
import os
import shutil
import subprocess
import sys
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Get user details.
usernamevar, usergroup, userhome = CFunc.getnormaluser()

# Exit if root.
CFunc.is_root(False)

### Variables ###
vscode_userconfigfolder = os.path.join(userhome, ".config", "Code", "User")
vscode_userconfig = os.path.join(vscode_userconfigfolder, "settings.json")
# Check for code command.
vscode_native = ["code"]
vscode_flatpak = ["flatpak", "run", "--command=code", "com.visualstudio.code"]
vscode_flatpak_oss = ["flatpak", "run", "--command=code-oss", "com.visualstudio.code.oss"]
vscode_windows = os.path.join("C:", os.sep, "Program Files", "Microsoft VS Code", "bin", "code.cmd")
vscode_snap = ["snap", "run", "vscode.code"]
if shutil.which("code") and not CFunc.is_windows():
    print("Detected native code command.")
    vscode_cmd = vscode_native
elif shutil.which("snap") and subprocess.run(vscode_snap).returncode is 0:
    print("Detected snap code command.")
    vscode_cmd = vscode_snap
elif shutil.which("flatpak") and subprocess.run(vscode_flatpak + ["-h"]).returncode is 0:
    print("Detected flatpak code command.")
    vscode_cmd = vscode_flatpak
    vscode_userconfigfolder = os.path.join(userhome, ".var", "app", "com.visualstudio.code", "data")
    vscode_userconfig = os.path.join(vscode_userconfigfolder, "settings.json")
elif shutil.which("flatpak") and subprocess.run(vscode_flatpak_oss + ["-h"]).returncode is 0:
    print("Detected flatpak code-oss command.")
    vscode_cmd = vscode_flatpak_oss
    vscode_userconfigfolder = os.path.join(userhome, ".var", "app", "com.visualstudio.code.oss", "data")
    vscode_userconfig = os.path.join(vscode_userconfigfolder, "settings.json")
elif CFunc.is_windows() and os.path.exists(vscode_windows) and subprocess.run([vscode_windows, "-h"]).returncode is 0:
    print("Detected Windows code command.")
    vscode_cmd = [vscode_windows]
    vscode_userconfig = os.path.join(userhome, "AppData", "Roaming", "Code", "User", "settings.json")
else:
    sys.exit("\nERROR: code command not found. Exiting.")


### Functions ###
def ce_ins(extension):
    """Install an extension"""
    subprocess.run(vscode_cmd + ["--install-extension", extension, "--force"])


### Distro Specific Packages ###
if shutil.which("dnf"):
    print("Install dnf dependencies.")
    CFunc.dnfinstall("python3-pip ShellCheck")
elif shutil.which("apt-get"):
    print("Install apt dependencies.")
    CFunc.aptinstall("python3-pip shellcheck")
elif shutil.which("zypper"):
    print("Install zypper dependencies.")

### Detect Windows Commands ###
if CFunc.is_windows() is True:
    pipcmd = "pip"
else:
    pipcmd = "pip3"

### Language Specific packages ###
if shutil.which(pipcmd):
    print("Installing python dependencies.")
    subprocess.run("{0}{1} install pylama pylama-pylint flake8".format(CFunc.sudocmd(True), pipcmd), shell=True)
else:
    print("{0} not found. Not install python packages.".format(pipcmd))


### Extensions ###
print("\nInstalling VS Code extensions.")
ce_ins("ms-python.python")
ce_ins("ms-vscode.cpptools")
ce_ins("ms-azuretools.vscode-docker")
ce_ins("mikestead.dotenv")
ce_ins("timonwong.shellcheck")
ce_ins("eamodio.gitlens")


### Configuration ###
data = {}
data["workbench.startupEditor"] = "newUntitledFile"
data["window.titleBarStyle"] = "custom"
data["editor.renderWhitespace"] = "all"
data["editor.wordWrap"] = "on"
# Python Config
if not CFunc.is_windows():
    data["python.pythonPath"] = "python3"
data["python.linting.maxNumberOfProblems"] = 500
data["python.linting.pylintArgs"] = ["--disable=C0301,C0103"]
data["python.linting.pylamaEnabled"] = True
data["python.linting.pylamaArgs"] = ["-i", "E501,E266,E302"]
data["python.linting.flake8Enabled"] = True
data["python.linting.flake8Args"] = ["--ignore=E501,E302,E266"]

# Print the json data for debugging purposes.
# print(json.dumps(data, indent=2))

# Write json file.
print("Writing {0}.".format(vscode_userconfig))
with open(vscode_userconfig, 'w') as file_json_wr:
    json.dump(data, file_json_wr, indent=2)
