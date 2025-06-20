#!/usr/bin/env python3
"""Install VS Code extensions and configuration."""

# Python includes.
import argparse
import functools
import json
import os
import shutil
import subprocess
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

print("Running {0}".format(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Install Visual Studio Code configuration.')
parser.add_argument("-t", "--type", help='''Type of configuration. Leave blank for autodetect.
    1: Native (Linux)
    2: VSCodium Windows
    3: VSCode Windows
    4: VSCodium
    5: VSCodium Flatpak
''', type=int, default=None)
args = parser.parse_args()

# Get user details.
usernamevar, usergroup, userhome = CFunc.getnormaluser()

########################## Functions ##########################
def cmd_silent(cmd=list):
    """Run a command silently"""
    status = subprocess.run(cmd, check=False, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    return status
def ce_ins(vscode_cmd=list, extension=str):
    """Install an extension"""
    subprocess.run(vscode_cmd + ["--install-extension", extension, "--force"], check=False, shell=False)
def ce_unins(vscode_cmd=list, extension=str):
    """Uninstall an extension"""
    subprocess.run(vscode_cmd + ["--uninstall-extension", extension, "--force"], check=False, shell=False)
def codeconfig_installext(vscode_cmd=list):
    """Install vscode extensions"""
    print("\nInstalling VS Code extensions.")
    ce_ins(vscode_cmd, "detachhead.basedpyright")
    ce_ins(vscode_cmd, "ms-azuretools.vscode-docker")
    ce_ins(vscode_cmd, "mikestead.dotenv")
    ce_ins(vscode_cmd, "timonwong.shellcheck")
    ce_ins(vscode_cmd, "eamodio.gitlens")
    ce_ins(vscode_cmd, "donjayamanne.githistory")
    ce_ins(vscode_cmd, "vscode-icons-team.vscode-icons")
    ce_ins(vscode_cmd, "yzhang.markdown-all-in-one")
    ce_ins(vscode_cmd, "davidanson.vscode-markdownlint")
    ce_ins(vscode_cmd, "dendron.dendron")
    ce_ins(vscode_cmd, "dendron.dendron-paste-image")
    ce_ins(vscode_cmd, "bbenoist.Nix")
    ce_ins(vscode_cmd, "danielroedl.meld-diff")
    ce_ins(vscode_cmd, "aaron-bond.better-comments")
    ce_ins(vscode_cmd, "ms-toolsai.jupyter")
    # Remove extensions
    ce_unins(vscode_cmd, "ms-python.vscode-pylance")
    ce_unins(vscode_cmd, "ms-pyright.pyright")
    ce_unins(vscode_cmd, "ms-python.flake8")
    ce_unins(vscode_cmd, "ms-python.python")


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
    if cmd_silent(code_array[1]["cmd"] + ["-h"]) == 0:
        if os.path.isdir(os.path.join(userhome, ".config", "Code - OSS", "User")):
            code_array[1]["path"] = os.path.join(userhome, ".config", "Code - OSS", "User")
        else:
            code_array[1]["path"] = os.path.join(userhome, ".config", "Code", "User")
else:
    code_array[1]["en"] = False

# VSCodium Windows
code_array[2]["cmd"] = [os.path.join("C:", os.sep, "Program Files", "VSCodium", "bin", "codium.cmd")]
# Since the command is in an array, index the 0th element to run which on it.
if CFunc.is_windows() and shutil.which(code_array[2]["cmd"][0]):
    code_array[2]["en"] = True
else:
    code_array[2]["en"] = False
code_array[2]["path"] = os.path.join(userhome, "AppData", "Roaming", "VSCodium", "User")

# VSCode Windows
code_array[3]["cmd"] = [os.path.join("C:", os.sep, "Program Files", "Microsoft VS Code", "bin", "code.cmd")]
# Since the command is in an array, index the 0th element to run which on it.
if CFunc.is_windows() and shutil.which(code_array[3]["cmd"][0]):
    code_array[3]["en"] = True
else:
    code_array[3]["en"] = False
code_array[3]["path"] = os.path.join(userhome, "AppData", "Roaming", "Code", "User")

# VSCodium
if shutil.which("vscodium") and not CFunc.is_windows():
    code_array[4]["cmd"] = ["vscodium"]
    code_array[4]["en"] = True
elif shutil.which("codium") and not CFunc.is_windows():
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

print(f"""Enabled choices:
1 (Native): {code_array[1]["en"]}
2 (VSCodium Windows): {code_array[2]["en"]}
3 (VSCode Windows): {code_array[3]["en"]}
4 (VSCodium): {code_array[4]["en"]}
5 (VSCodium Flatpak): {code_array[5]["en"]}
""")


########################## Begin Code ##########################
# Process options
for idx in range(1, 6):
    # Only process enabled options.
    if code_array[idx]["en"] is True:
        print("\nProcessing option {0}\n".format(idx))

        # Add marketplace for vscodium
        if idx == 2 or idx == 4 or idx == 5:
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
            # Dendron/markdown preview fixes
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
            },
            # Fix jupyter undo cells issue
            # https://stackoverflow.com/a/69421121
            {"key": "ctrl+z", "command": "-undo"},
            {"key": "ctrl+z", "command": "undo", "when": "!notebookEditorFocused || inputFocus"},
            {"key": "ctrl+shift+z", "command": "-redo"},
            {"key": "ctrl+shift+z", "command": "redo", "when": "!notebookEditorFocused || inputFocus"},
            {"key": "ctrl+y", "command": "-redo"},
            {"key": "ctrl+y", "command": "redo", "when": "!notebookEditorFocused || inputFocus"},
        ]
        CFunc.json_configwrite(kb_data, os.path.join(code_array[idx]["path"], "keybindings.json"))

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
        data["files.enableTrash"] = False
        data["security.workspace.trust.enabled"] = False
        data["telemetry.telemetryLevel"] = "error"
        data["workbench.iconTheme"] = "vscode-icons"
        data["workbench.colorTheme"] = "Visual Studio Dark"
        data["window.commandCenter"] = False
        data["vsicons.dontShowNewVersionMessage"] = True
        data["update.showReleaseNotes"] = False
        data["git.confirmSync"] = False
        data["git.autofetch"] = True
        data["git.discardUntrackedChangesToTrash"] = False
        data["[nix]"] = {"editor.tabSize": 2}
        data["markdown.extension.preview.autoShowPreviewToSide"] = False
        data["pasteImage.path"] = "${currentFileDir}/assets/images"
        data["gitlens.plusFeatures.enabled"] = False
        data["gitlens.showWhatsNewAfterUpgrades"] = False
        data["gitlens.telemetry.enabled"] = False
        data["window.commandCenter"] = False
        data["chat.commandCenter.enabled"] = False
        # Markdown lint config
        data["markdownlint.config"] = {
            "default": True,
            "MD033": False,
        }
        # Python Config
        data["flake8.args"] = ["--ignore=E501,E302,E266"]
        data["python.analysis.typeCheckingMode"] = "off"
        # basedpyright
        data["basedpyright.importStrategy"] = "useBundled"
        data["basedpyright.analysis.diagnosticSeverityOverrides"] = {
            # Disabled
            "reportAny": "none",
            "reportArgumentType": "none",
            "reportCallIssue": "none",
            "reportExplicitAny": "none",
            "reportMissingParameterType": "none",
            "reportMissingTypeArgument": "none",
            "reportOperatorIssue": "none",
            "reportUnknownArgumentType": "none",
            "reportUnknownMemberType": "none",
            "reportUnknownParameterType": "none",
            "reportUnknownVariableType": "none",
            "reportUnusedCallResult": "none",
            "reportCallInDefaultInitializer": "none",
            # Warning
            "reportPossiblyUnboundVariable": "warning",
            # Information
        }
        # File Associations
        data["files.associations"] = {
            ".env*": "properties",
            "compose-*.yaml": "dockercompose",
            "compose-*.yml": "dockercompose",
            "Containerfile-*": "dockerfile",
            "docker-compose*.yaml": "dockercompose",
            "docker-compose*.yml": "dockercompose",
            "Dockerfile-*": "dockerfile",
        }

        # Write json configuration
        CFunc.json_configwrite(data, os.path.join(code_array[idx]["path"], "settings.json"))
