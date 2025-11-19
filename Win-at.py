#!/usr/bin/env python3
"""Perform post-install act of Windows."""

# Python includes.
import os
import re
import subprocess
import sys
# Custom Includes
import CFunc
import Wprovision

print("Running {0}".format(__file__))

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()

if CFunc.is_windows() is False:
    sys.exit("ERROR, not running under Windows. Exiting.")

kms_folder = os.path.join(USERHOME, "Documents")
kms_script = os.path.join(kms_folder, "MAS_AIO.cmd")

CFunc.downloadfile("https://raw.githubusercontent.com/massgravel/Microsoft-Activation-Scripts/refs/heads/master/MAS/All-In-One-Version-KL/MAS_AIO.cmd", kms_folder)

# Add exceptions for defender
Wprovision.pwsh_run(["Add-MpPreference", "-ExclusionPath", r"$env:windir\Temp\SppExtComObjHook.dll"])
Wprovision.pwsh_run(["Add-MpPreference", "-ExclusionPath", r"$env:LOCALAPPDATA\Temp\SppExtComObjHook.dll"])
Wprovision.pwsh_run(["Add-MpPreference", "-ExclusionPath", r"$env:ProgramFiles\Activation-Renewal"])
Wprovision.pwsh_run(["Add-MpPreference", "-ExclusionProcess", kms_script])

# Run script
subprocess.run(f"{kms_script} /K-WindowsOffice", shell=True, check=True)
