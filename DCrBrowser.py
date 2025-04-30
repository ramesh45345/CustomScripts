#!/usr/bin/env python3
"""Set Chromium/Brave and equivalent browser settings"""

import functools
import json
import os
import shutil
import subprocess
from pathlib import Path
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Home folder
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()


### Global Variables ###

cr_profiles_paths = [
    # Command to run, Command to check with Which, Path to profile
    # Brave native linux
    {"browser_type": "brave", "cmd_which": "brave", "cmd_test": None, "browser_installed": False, "profile_path": os.path.join(os.sep, "etc", "brave", "policies", "managed", "GroupPolicy.json")},
    # Brave flatpak
    # {"cmd_which": "brave", "cmd_test": None, "profile_path": os.path.join(os.sep, "etc", "brave", "policies", "managed", "GroupPolicy.json")},
    # Brave Windows
]

### Functions ###

# TODO: Move this to CFunc
def codeconfig_writeconfiguration(json_data: list, json_path: str):
    """Write the config.json"""
    dirname = os.path.abspath(os.path.dirname(json_path))
    if os.path.isdir(dirname):
        print(f"Writing {json_path}")
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
    else:
        print("ERROR: {0} config path missing. Not writing config.".format(json_path))


# Exit if not root.
CFunc.is_root(True)


### Begin Code ###

for br in cr_profiles_paths:
    # Detect if browser is installed
    if br['cmd_which'] and shutil.which(br['cmd_which']):
        br['browser_installed'] = True
    if br['cmd_test']:
        status_retcode = subprocess.run(br['cmd_test'], shell=True, check=False).returncode
        if status_retcode == 0:
            br['browser_installed'] = True

    # Json data
    data = {}
    if br['browser_type'] == "brave":
        data["TorDisabled"] = True
        data["BraveRewardsDisabled"] = True
        data["BraveWalletDisabled"] = True
        data["BraveAIChatEnabled"] = False
        data["BraveVPNDisabled"] = True

    # Print the json data for debugging purposes.
    # print(json.dumps(data, indent=2))

    # Write json configuration
    profile_dirname = Path(os.path.abspath(os.path.dirname(br['profile_path'])))
    profile_dirname.mkdir(parents=True, exist_ok=True)
    codeconfig_writeconfiguration(json_data=data, json_path=br['profile_path'])
