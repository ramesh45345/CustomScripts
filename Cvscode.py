#!/usr/bin/env python3
"""Install VS Code extensions and configuration."""

# Python includes.
import argparse
import json
import os
import shutil
import subprocess
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Install Visual Studio Code configuration.')
parser.add_argument("-t", "--type", help='''Type of configuration. Leave blank for autodetect.
    1: Native (Linux)
    2: Flatpak (OSS)
    3: Snap
    4: Windows
    5: VSCodium
''', type=int, default=None)
args = parser.parse_args()

# Get user details.
usernamevar, usergroup, userhome = CFunc.getnormaluser()

# Exit if root.
CFunc.is_root(False)

########################## Functions ##########################
def cmd_silent(cmd=list):
    """Run a command silently"""
    status = subprocess.run(cmd, check=False, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    return status

def cmd_distropkgs(cmd_type=int, enabled=bool):
    """Install distro specific packages"""
    if cmd_type == 1 or cmd_type == 3 or cmd_type == 5 and enabled is True:
        if shutil.which("dnf"):
            print("Install dnf dependencies.")
            CFunc.dnfinstall("python3-pip ShellCheck")
        elif shutil.which("apt-get"):
            print("Install apt dependencies.")
            CFunc.aptinstall("python3-pip shellcheck")

def cmd_pips(cmd_type=int, enabled=bool):
    """Install python pip packages"""
    pip_packages = "pylama pylama-pylint flake8"
    # Flatpak (OSS)
    if enabled is True and cmd_type == 2:
        subprocess.run("flatpak run --command=pip3 com.visualstudio.code-oss install {0} --user".format(pip_packages), shell=True, check=True)
    # Windows
    if enabled is True and cmd_type == 4 and shutil.which("pip"):
        subprocess.run("pip install {0}".format(pip_packages), shell=True, check=True)
    # Other Linux types
    if cmd_type == 1 or cmd_type == 3 or cmd_type == 5 and enabled is True and shutil.which("pip3"):
        subprocess.run("{0}pip3 install pylama pylama-pylint flake8".format(CFunc.sudocmd(True)), shell=True, check=True)
def ce_ins(vscode_cmd=list, extension=str):
    """Install an extension"""
    subprocess.run(vscode_cmd + ["--install-extension", extension, "--force"], check=True, shell=False)
def codeconfig_installext(vscode_cmd=list):
    """Install vscode extensions"""
    print("\nInstalling VS Code extensions.")
    ce_ins(vscode_cmd, "ms-python.python")
    ce_ins(vscode_cmd, "ms-azuretools.vscode-docker")
    ce_ins(vscode_cmd, "mikestead.dotenv")
    ce_ins(vscode_cmd, "timonwong.shellcheck")
    ce_ins(vscode_cmd, "eamodio.gitlens")
    ce_ins(vscode_cmd, "donjayamanne.githistory")
    ce_ins(vscode_cmd, "vscode-icons-team.vscode-icons")
    ce_ins(vscode_cmd, "yzhang.markdown-all-in-one")
    ce_ins(vscode_cmd, "danielroedl.meld-diff")
def codeconfig_writeconfiguration(json_data=dict, json_path=str):
    """Write the config.json"""
    if os.path.isdir(json_path):
        vscode_userconfig = os.path.join(json_path, "settings.json")
        print("Writing {0}.".format(vscode_userconfig))
        with open(vscode_userconfig, 'w') as f:
            json.dump(json_data, f, indent=2)
    else:
        print("ERROR: {0} config path missing. Not writing config.".format(json_path))


########################## Variables ##########################

# Build List
# List positions - en: Enabled
#                  cmd: Command
#                  path: settings.json path
code_array = {}
for idx in range(1, 6):
    code_array[idx] = {}
    code_array[idx]["en"] = [""]
    code_array[idx]["cmd"] = []
    code_array[idx]["path"] = [""]

# Native (Linux)
code_array[1]["cmd"] = ["code"]
if not CFunc.is_windows() and shutil.which("code"):
    code_array[1]["en"] = True
else:
    code_array[1]["en"] = False
if os.path.isdir(os.path.join(userhome, ".config", "Code - OSS", "User")):
    # Native code config path for Manjaro pkg.
    code_array[1]["path"] = os.path.join(userhome, ".config", "Code - OSS", "User")
else:
    code_array[1]["path"] = os.path.join(userhome, ".config", "Code", "User")

# Flatpak
code_array[2]["cmd"] = ["flatpak", "run", "--command=code-oss", "com.visualstudio.code-oss"]
if shutil.which("flatpak") and cmd_silent(code_array[2]["cmd"] + ["-h"]) == 0:
    code_array[2]["en"] = True
else:
    code_array[2]["en"] = False
code_array[2]["path"] = os.path.join(userhome, ".var", "app", "com.visualstudio.code-oss", "config", "Code - OSS", "User")

# Snap
code_array[3]["cmd"] = ["snap", "run", "vscode.code"]
if shutil.which("snap") and cmd_silent(code_array[3]["cmd"] + ["-h"]) == 0:
    code_array[3]["en"] = True
else:
    code_array[3]["en"] = False
code_array[3]["path"] = os.path.join(userhome, ".config", "Code", "User")

# Windows
code_array[4]["cmd"] = [os.path.join("C:", os.sep, "Program Files", "Microsoft VS Code", "bin", "code.cmd")]
# Since the command is in an array, index the 0th element to run which on it.
if CFunc.is_windows() and shutil.which(code_array[4]["cmd"][0]):
    code_array[4]["en"] = True
else:
    code_array[4]["en"] = False
code_array[4]["path"] = os.path.join(userhome, "AppData", "Roaming", "Code", "User")

# VSCodium
if shutil.which("vscodium"):
    code_array[5]["cmd"] = ["vscodium"]
elif shutil.which("codium"):
    code_array[5]["cmd"] = ["codium"]
else:
    code_array[5]["cmd"] = None
    code_array[5]["en"] = False
code_array[5]["path"] = os.path.join(userhome, ".config", "VSCodium", "User")

# Force config to use argument type if specified.
if args.type is not None:
    for idx in range(1, 5):
        if idx != args.type:
            code_array[idx]["en"] = False

print("""Enabled choices:
1 (Native): {0}
2 (Flatpak OSS): {1}
3 (Snap): {2}
4 (Windows): {3}
5 (VSCodium): {4}
""".format(code_array[1]["en"], code_array[2]["en"], code_array[3]["en"], code_array[4]["en"], code_array[5]["en"]))


########################## Begin Code ##########################
# Process options
for idx in range(1, 5):
    # Only process enabled options.
    if code_array[idx]["en"] is True:
        print("\nProcessing option {0}\n".format(idx))
        # Install OS based packages
        cmd_distropkgs(idx, code_array[idx]["en"])
        # Pip Commands
        cmd_pips(idx, code_array[idx]["en"])

        # Extensions
        codeconfig_installext(code_array[idx]["cmd"])

        # Json data
        data = {}
        data["workbench.startupEditor"] = "newUntitledFile"
        data["window.titleBarStyle"] = "custom"
        data["editor.renderWhitespace"] = "all"
        data["editor.wordWrap"] = "on"
        # Flatpak specific options
        if idx == 2:
            # Flatpak specific options
            data["terminal.integrated.profiles.linux"] = {
                "bash": {
                    "path": "bash"
                },
                "fphost": {
                    "path": "flatpak-spawn",
                    "args": ["--host", "bash"]
                },
            }
            data["terminal.integrated.defaultProfile.linux"] = "fphost"
        # Python Config
        if not CFunc.is_windows():
            data["python.pythonPath"] = "python3"
        data["python.linting.maxNumberOfProblems"] = 500
        data["python.linting.pylintArgs"] = ["--disable=C0301,C0103"]
        data["python.linting.pylamaEnabled"] = True
        data["python.linting.pylamaArgs"] = ["-i", "E501,E266,E302"]
        data["python.linting.flake8Enabled"] = True
        data["python.linting.flake8Args"] = ["--ignore=E501,E302,E266"]
        data["python.showStartPage"] = False
        data["workbench.iconTheme"] = "vscode-icons"
        data["security.workspace.trust.enabled"] = False
        # Print the json data for debugging purposes.
        # print(json.dumps(data, indent=2))

        # Write json configuration
        codeconfig_writeconfiguration(data, code_array[idx]["path"])
