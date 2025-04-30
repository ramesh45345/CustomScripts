#!/usr/bin/env python3
"""Setup NixOS."""

# Python includes.
import argparse
import os
import subprocess
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

CFunc.is_root(checkstate=True)

### Functions ###
def cli_scripts():
    """"""
    subprocess.run(['{0}/CShellConfig.py'.format(SCRIPTDIR), '-f', '-z', '-d'], check=True)
    subprocess.run(['{0}/CCSClone.py'.format(SCRIPTDIR)], check=True)
def gui_scripts(user: str):
    """"""
    subprocess.run(['{0}/Cxdgdirs.py'.format(SCRIPTDIR)], check=True)
    CFunc.run_as_user(user, "{0}/Cvscode.py".format(SCRIPTDIR), error_on_fail=True)
    CFunc.run_as_user(user, "{0}/CMediaPlayerConfig.py".format(SCRIPTDIR), error_on_fail=True)

### Begin Code ###
if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get non-root user.
    USERNAMEVAR = CFunc.getnormaluser()[0]

    # Get arguments
    parser = argparse.ArgumentParser(description='Setup nix.')
    parser.add_argument("-u", "--user", help='Normal user to set up nix as.', default=USERNAMEVAR)
    parser.add_argument("-c", "--clionly", help='Do not run GUI scripts.', action="store_true")
    args = parser.parse_args()

    # Get non-root user information for specified user.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser(args.user)

    # Chown /etc/nixos
    CFunc.chown_recursive("/etc/nixos", USERNAMEVAR, USERGROUP)

    cli_scripts()
    if not args.clionly:
        gui_scripts(USERNAMEVAR)
