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
    3: Windows
    4: VSCodium
    5: VSCodium Flatpak
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

def cmd_pips(cmd_type=int, enabled=bool):
    """Install python pip packages"""
    pip_packages = "pylama pylama-pylint flake8"
    # Flatpak (OSS)
    if enabled is True and cmd_type == 2:
        subprocess.run("flatpak run --command=pip3 com.visualstudio.code-oss install {0} --user".format(pip_packages), shell=True, check=True)
    # Windows
    if enabled is True and cmd_type == 3 and shutil.which("pip"):
        subprocess.run("pip install {0}".format(pip_packages), shell=True, check=True)
    # Other Linux types
    if cmd_type == 1 or cmd_type == 3 or cmd_type == 5 and enabled is True and shutil.which("pip3") and not CFunc.is_nixos():
        subprocess.run("pip3 install pylama pylama-pylint flake8", shell=True, check=True)
def ce_ins(vscode_cmd=list, extension=str):
    """Install an extension"""
    subprocess.run(vscode_cmd + ["--install-extension", extension, "--force"], check=False, shell=False)
def ce_unins(vscode_cmd=list, extension=str):
    """Uninstall an extension"""
    subprocess.run(vscode_cmd + ["--uninstall-extension", extension, "--force"], check=False, shell=False)
def codeconfig_installext(vscode_cmd=list):
    """Install vscode extensions"""
    print("\nInstalling VS Code extensions.")
    ce_ins(vscode_cmd, "ms-pyright.pyright")
    ce_ins(vscode_cmd, "ms-python.python")
    ce_unins(vscode_cmd, "ms-python.vscode-pylance")
    ce_ins(vscode_cmd, "ms-azuretools.vscode-docker")
    ce_ins(vscode_cmd, "mikestead.dotenv")
    ce_ins(vscode_cmd, "timonwong.shellcheck")
    ce_ins(vscode_cmd, "huizhou.githd")
    ce_ins(vscode_cmd, "donjayamanne.githistory")
    ce_ins(vscode_cmd, "vscode-icons-team.vscode-icons")
    ce_ins(vscode_cmd, "yzhang.markdown-all-in-one")
    ce_ins(vscode_cmd, "davidanson.vscode-markdownlint")
    ce_ins(vscode_cmd, "dendron.dendron")
    ce_ins(vscode_cmd, "dendron.dendron-paste-image")
    ce_ins(vscode_cmd, "bbenoist.Nix")
    ce_ins(vscode_cmd, "danielroedl.meld-diff")
    ce_ins(vscode_cmd, "aaron-bond.better-comments")
def codeconfig_writeconfiguration(json_data=dict, json_path=str, json_file: str = "settings.json"):
    """Write the config.json"""
    if os.path.isdir(json_path):
        vscode_userconfig = os.path.join(json_path, json_file)
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

# Windows
code_array[3]["cmd"] = [os.path.join("C:", os.sep, "Program Files", "Microsoft VS Code", "bin", "code.cmd")]
# Since the command is in an array, index the 0th element to run which on it.
if CFunc.is_windows() and shutil.which(code_array[3]["cmd"][0]):
    code_array[3]["en"] = True
else:
    code_array[3]["en"] = False
code_array[3]["path"] = os.path.join(userhome, "AppData", "Roaming", "Code", "User")

# VSCodium
if shutil.which("vscodium"):
    code_array[4]["cmd"] = ["vscodium"]
    code_array[4]["en"] = True
elif shutil.which("codium"):
    code_array[4]["cmd"] = ["codium"]
    code_array[4]["en"] = True
else:
    code_array[4]["cmd"] = None
    code_array[4]["en"] = False
code_array[4]["path"] = os.path.join(userhome, ".config", "VSCodium", "User")

# VSCodium Flatpak
code_array[5]["cmd"] = ["flatpak", "run", "--command=codium", "com.vscodium.codium"]
if shutil.which("flatpak") and cmd_silent(code_array[5]["cmd"] + ["-h"]) == 0:
    code_array[5]["en"] = True
else:
    code_array[5]["en"] = False
code_array[5]["path"] = os.path.join(userhome, ".var", "app", "com.vscodium.codium", "config", "VSCodium", "User")

# Force config to use argument type if specified.
if args.type is not None:
    for idx in range(1, 6):
        if idx != args.type:
            code_array[idx]["en"] = False

print("""Enabled choices:
1 (Native): {0}
2 (Flatpak OSS): {1}
3 (Windows): {2}
4 (VSCodium): {3}
5 (VSCodium Flatpak): {4}
""".format(code_array[1]["en"], code_array[2]["en"], code_array[3]["en"], code_array[4]["en"], code_array[5]["en"]))


########################## Begin Code ##########################
# Process options
for idx in range(1, 6):
    # Only process enabled options.
    if code_array[idx]["en"] is True:
        print("\nProcessing option {0}\n".format(idx))
        # Pip Commands
        cmd_pips(idx, code_array[idx]["en"])

        # Add marketplace for vscodium
        if idx == 4 or idx == 5:
            os.makedirs(os.path.dirname(code_array[idx]["path"]), exist_ok=True)
            product_json_path = os.path.join(os.path.dirname(code_array[idx]["path"]), "product.json")
            # Json data
            productjson = {}
            # Uncomment if issues with extensions not being enabled.
            # productjson["nameShort"] = "Visual Studio Code"
            # productjson["nameLong"] = "Visual Studio Code"
            productjson["extensionsGallery"] = {
                "serviceUrl": "https://marketplace.visualstudio.com/_apis/public/gallery",
                "cacheUrl": "https://vscode.blob.core.windows.net/gallery/index",
                "itemUrl": "https://marketplace.visualstudio.com/items",
                "controlUrl": "",
                "recommendationsUrl": ""
            }
            with open(product_json_path, 'w') as f:
                json.dump(productjson, f, indent=2)

        # Extensions
        codeconfig_installext(code_array[idx]["cmd"])

        # Keyboard bindings
        kb_data = [
            {
                "key": "ctrl+shift+v",
                "command": "markdown.showPreviewToSide"
            },
            {
                "key": "ctrl+k v",
                "command": "-markdown.showPreviewToSide",
                "when": "!notebookEditorFocused && editorLangId == 'markdown'"
            },
            {
                "key": "ctrl+k v",
                "command": "markdown.showPreview",
                "when": "!notebookEditorFocused && editorLangId == 'markdown'"
            },
            {
                "key": "ctrl+shift+v",
                "command": "-markdown.showPreview",
                "when": "!notebookEditorFocused && editorLangId == 'markdown'"
            },
            {
                "key": "ctrl+shift+b",
                "command": "dendron.togglePreview",
                "when": "dendron:pluginActive"
            },
            {
                "key": "ctrl+k v",
                "command": "-dendron.togglePreview",
                "when": "dendron:pluginActive"
            }
        ]
        # print(json.dumps(kb_data, indent=4))
        codeconfig_writeconfiguration(kb_data, code_array[idx]["path"], "keybindings.json")

        # Json data
        data = {}
        data["workbench.startupEditor"] = "newUntitledFile"
        data["window.titleBarStyle"] = "custom"
        data["editor.renderWhitespace"] = "all"
        data["editor.wordWrap"] = "on"
        # Flatpak specific options
        if idx == 2 or idx == 5:
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
        data["security.workspace.trust.enabled"] = False
        data["telemetry.telemetryLevel"] = "error"
        data["workbench.iconTheme"] = "vscode-icons"
        data["workbench.colorTheme"] = "Visual Studio Dark"
        data["vsicons.dontShowNewVersionMessage"] = True
        data["git.confirmSync"] = False
        data["git.autofetch"] = True
        data["[nix]"] = {"editor.tabSize": 2}
        data["markdown.extension.preview.autoShowPreviewToSide"] = False
        data["pasteImage.path"] = "${currentFileDir}/assets/images"
        # Markdown lint config
        data["markdownlint.config"] = {
            "default": True,
            "MD033": False,
        }
        # Python Config
        data["python.linting.maxNumberOfProblems"] = 500
        data["python.linting.pylintArgs"] = ["--disable=C0301,C0103"]
        data["python.linting.pylamaEnabled"] = True
        data["python.linting.pylamaArgs"] = ["-i", "E501,E266,E302"]
        data["python.linting.flake8Enabled"] = True
        data["python.linting.flake8Args"] = ["--ignore=E501,E302,E266"]
        data["python.analysis.typeCheckingMode"] = "off"

        # Print the json data for debugging purposes.
        # print(json.dumps(data, indent=2))

        # Write json configuration
        codeconfig_writeconfiguration(data, code_array[idx]["path"])
