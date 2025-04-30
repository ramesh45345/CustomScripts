#!/usr/bin/env python3
"""Set Chromium/Brave and equivalent browser settings"""

import functools
import json
import os
import shutil
import subprocess
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
def codeconfig_writeconfiguration(json_data: list = dict, json_path=str, json_file: str = "GroupPolicy.json"):
    """Write the config.json"""
    if os.path.isdir(json_path):
        config_path = os.path.join(json_path, json_file)
        print("Writing {0}.".format(config_path))
        with open(config_path, 'w') as f:
            json.dump(json_data, f, indent=2)
    else:
        print("ERROR: {0} config path missing. Not writing config.".format(json_path))
def browser_isinstalled(browser_line: dict):
    """Test if the browser in the dictionary is present."""
    status = False
    return status


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
        data["TorDisabled"] = 1

    # Print the json data for debugging purposes.
    # print(json.dumps(data, indent=2))

    # Write json configuration
