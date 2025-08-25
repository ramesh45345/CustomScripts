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

kms_folder = os.path.join(USERHOME, "Documents", "KMS_VL_ALL_AIO")
kms_script = os.path.join(kms_folder, "KMS_VL_ALL_AIO.cmd")

# Clone the repo
CFunc.gitclone("https://github.com/abbodi1406/KMS_VL_ALL_AIO", kms_folder)

# Add exceptions for defender
Wprovision.RunWithPwsh(["Add-MpPreference", "-ExclusionPath", r"$env:windir\Temp\SppExtComObjHook.dll"])
Wprovision.RunWithPwsh(["Add-MpPreference", "-ExclusionPath", r"$env:LOCALAPPDATA\Temp\SppExtComObjHook.dll"])
Wprovision.RunWithPwsh(["Add-MpPreference", "-ExclusionPath", r"$env:windir\AutoKMS"])
Wprovision.RunWithPwsh(["Add-MpPreference", "-ExclusionPath", kms_folder])
Wprovision.RunWithPwsh(["Add-MpPreference", "-ExclusionProcess", kms_script])

# Set auto-act
with open(kms_script) as f:
    s = f.read()
snew = ""
for line in s.splitlines():
    snew += re.sub(r"^set uAutoRenewal=0$", "set uAutoRenewal=1", line) + "\n"
with open(kms_script, "w") as f:
    f.write(snew)

# Run script
subprocess.run(kms_script, shell=True, check=True)
