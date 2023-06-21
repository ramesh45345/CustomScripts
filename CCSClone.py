#!/usr/bin/env python3
"""Clone and update CustomScripts."""

# Python includes.
import argparse
import json
import os
import shutil
import subprocess
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()

# Get arguments
parser = argparse.ArgumentParser(description='Update and set info for CustomScripts.')
parser.add_argument("-v", "--variablefile", help='Run Extra Scripts', default=os.path.join(USERHOME, "privateconfig.json"))

# Save arguments.
args = parser.parse_args()

# Get external variables from bash file.
variablefile = args.variablefile
if os.path.isfile(args.variablefile):
    variablefile = os.path.abspath(args.variablefile)
    print("Variable File {0} will be used.".format(variablefile))

# Save the repo name (after the slash) and the user (before the slash).
fullrepo = "ramesh45345/CustomScripts"
repouser = fullrepo.split("/")[0]
reponame = fullrepo.split("/")[1]

# Name of this repo
clonepath = SCRIPTDIR

# Cron variables
cron_hourly_folder = os.path.join(os.sep, "etc", "cron.hourly")
cron_hourly_file = os.path.join(cron_hourly_folder, reponame)

### Begin Code ###
# Git config
subprocess.run("git config --global pull.rebase false", shell=True, check=True)
CFunc.run_as_user(USERNAMEVAR, "git config --global pull.rebase false", error_on_fail=True)

# Git pull.
os.chdir(clonepath)
subprocess.run(['git', 'config', 'remote.origin.url', "https://github.com/{0}.git".format(fullrepo)], check=True)
subprocess.run(['git', 'pull'], check=True)

# If variables were sourced, set remote details for comitting.
if os.path.isfile(variablefile):
    print("Adding commit information for {0} github account.".format(reponame))
    with open(variablefile, 'r') as variablefile_handle:
        json_privdata = json.load(variablefile_handle)
    os.chdir(clonepath)
    subprocess.run(['git', 'config', 'remote.origin.url', "git@github.com:{0}.git".format(fullrepo)], check=True)
    subprocess.run(['git', 'config', 'push.default', 'simple'], check=True)
    subprocess.run(['git', 'config', 'user.name', json_privdata['GITHUBCOMMITNAME']], check=True)
    subprocess.run(['git', 'config', 'user.email', json_privdata['GITHUBCOMMITEMAIL']], check=True)

# Update scripts folder every hour.
# Make systemd service and timer if available
if shutil.which("systemctl") and not CFunc.is_nixos():
    # Systemd service
    CSUpdate_SystemUnitText = """[Unit]
Description=Service for CSUpdate
After=network-online.target

[Service]
Type=simple
User={username}
ExecStart=/bin/sh -c "cd {clonepath}; git pull"
Restart=on-failure
RestartSec=60s
StartLimitBurst=4""".format(username=USERNAMEVAR, clonepath=clonepath)
    CFunc.systemd_createsystemunit("csupdate.service", CSUpdate_SystemUnitText)
    # Systemd timer
    CSUpdate_SystemTimerText = """[Unit]
Description=Timer for CSupdate

[Timer]
OnBootSec=15sec
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
"""
    SystemdSystemUnitPath = os.path.join(os.sep, "etc", "systemd", "system")
    fullunitpath = os.path.join(SystemdSystemUnitPath, "csupdate.timer")
    # Write the unit file.
    print("Creating {0}.".format(fullunitpath))
    with open(fullunitpath, 'w') as fullunitpath_write:
        fullunitpath_write.write(CSUpdate_SystemTimerText)
    # Enable the timer
    subprocess.run("systemctl daemon-reload", shell=True, check=False)
    CFunc.sysctl_enable("csupdate.timer")
    # Remove the cron script if it exists.
    if os.path.isfile("/etc/cron.hourly/{0}".format(reponame)):
        os.remove("/etc/cron.hourly/{0}".format(reponame))
# Fall-back to cron script if systemd is not available.
elif os.path.isdir(cron_hourly_folder):
    with open(cron_hourly_file, 'w') as file:
        file.write('''#!{2}
echo "Executing \$0"
su {0} -s /bin/sh <<'EOL'
    cd {1}
    git pull
EOL
'''.format(USERNAMEVAR, clonepath, shutil.which("bash")))
    # Make script executable
    os.chmod(cron_hourly_file, 0o777)

# Set permissions of cloned folder
if CFunc.is_windows() is False:
    subprocess.run("chown -R {0}:{1} {2}".format(USERNAMEVAR, USERGROUP, clonepath), shell=True, check=False)
    os.chmod(clonepath, 0o777)
