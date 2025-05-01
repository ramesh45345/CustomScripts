#!/usr/bin/env python3
"""Set Chromium/Brave and equivalent browser settings"""

import functools
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
]

### Functions ###


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
    # Chrome policies: https://chromeenterprise.google/policies/
    data = {}
    # Brave specific policies: https://support.brave.com/hc/en-us/articles/360039248271-Group-Policy
    if br['browser_type'] == "brave":
        data["TorDisabled"] = True
        data["BraveRewardsDisabled"] = True
        data["BraveWalletDisabled"] = True
        data["BraveAIChatEnabled"] = False
        data["BraveVPNDisabled"] = True
    data["ShoppingListEnabled"] = False
    data["SideSearchEnabled"] = False
    data["AccessCodeCastEnabled"] = False
    data["LensDesktopNTPSearchEnabled"] = False
    data["GoogleSearchSidePanelEnabled"] = False
    data["PasswordManagerEnabled"] = False
    data["AutofillCreditCardEnabled"] = False
    data["BackgroundModeEnabled"] = False
    data["SafeBrowsingDeepScanningEnabled"] = False
    data["SafeBrowsingSurveysEnabled"] = False
    data["SafeBrowsingExtendedReportingEnabled"] = False
    data["PasswordLeakDetectionEnabled"] = False
    data["PasswordSharingEnabled"] = False
    data["AutoplayAllowed"] = False
    data["BookmarkBarEnabled"] = True
    data["RestoreOnStartup"] = 1
    data["PromptForDownloadLocation"] = True
    data["HomepageIsNewTabPage"] = True
    data["HardwareAccelerationModeEnabled"] = True
    data["HighEfficiencyModeEnabled"] = True
    data["MemorySaverModeSavings"] = 0
    dlfolder = CFunc.storage_path_detect(["DLs"])
    if dlfolder:
        data["DownloadDirectory"] = dlfolder
    data["ExtensionInstallForcelist"] = [
        "bnomihfieiccainjcjblhegjgglakjdd",  # Improve YouTube
        "cjpalhdlnbpafiamejdnhcphjbkeiagm",  # uBlock Origin
        "fnaicdffflnofjppbagibeoednhnbjhg",  # floccus
        "gebbhagfogifgggkldgodflihgfeippi",  # Return YouTube Dislike
        "iaiomicjabeggjcfkbimgmglanimpnae",  # Tab Session Manager
        "mnjggcdmjocbbbhaepdhchncahnbgone",  # Sponsorblock
        "nkgllhigpcljnhoakjkgaieabnkmgdkb",  # Don't F*** With Paste
        "nngceckbapebfimnlniiiahkandclblb",  # Bitwarden
    ]
    data["TabDiscardingExceptions"] = [
        "google.com",
        "youtube.com",
    ]

    # Write json configuration
    profile_dirname = Path(os.path.abspath(os.path.dirname(br['profile_path'])))
    profile_dirname.mkdir(parents=True, exist_ok=True)
    CFunc.json_configwrite(json_data=data, json_path=br['profile_path'], print_json=False)
