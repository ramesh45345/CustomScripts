#!/usr/bin/env python3
"""Create immutable root configuration. Must run as root."""

# Python includes.
import argparse
import os
import shutil
import subprocess
import sys
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = sys.path[0]

CFunc.is_root(checkstate=True)

### Functions ###
def immutable_root_detect():
    """Detect if the OS has an immutable root."""
    detected = False
    if shutil.which("rpm-ostree"):
        detected = True
    return detected
def immutable_root(user: str):
    """Install service for immutable operating system. All commands here require root."""
    if immutable_root_detect() is True:
        # Create /nix for immutable fs OS
        nix_service_text = """
[Unit]
Description=Prepare nix mount points

[Service]
Type=oneshot
ExecStartPre=chattr -i /
ExecStart=/bin/sh -c "mkdir -p /nix"
ExecStart=/bin/sh -c "mkdir -p /var/lib/nix"
ExecStart=/bin/sh -c "mount --bind /var/lib/nix /nix"
ExecStopPost=chattr +i /

[Install]
WantedBy=local-fs.target
"""
        CFunc.systemd_createsystemunit("mount-nix-prepare.service", nix_service_text, sysenable=True)
        subprocess.run(["systemctl", "restart", "mount-nix-prepare.service"], check=True)
        shutil.chown(os.path.join(os.sep, "nix"), user)
def install_profile_config():
    """Install system profile script."""
    with open(os.path.join(os.sep, "etc", "profile.d", "rcustom_nix.sh"), 'w') as f:
        f.write(r"""
[ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ] && . $HOME/.nix-profile/etc/profile.d/nix.sh
[ -e "$HOME/.nix-profile/etc/profile.d/hm-session-vars.sh" ] && . $HOME/.nix-profile/etc/profile.d/hm-session-vars.sh

if [ -d "$HOME/.nix-profile/share" ] && [[ ":$XDG_DATA_DIRS:" != *":$HOME/.nix-profile/share:"* ]]; then
    XDG_DATA_DIRS="${XDG_DATA_DIRS:+"$XDG_DATA_DIRS:"}$HOME/.nix-profile/share"
fi
""")
def call_install_script(user: str):
    """Run the installation script as a normal user."""
    CFunc.run_as_user(user, "{0}/CNixUserSetup.py -n".format(SCRIPTDIR), error_on_fail=True)


### Begin Code ###
if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get non-root user.
    USERNAMEVAR = CFunc.getnormaluser()[0]

    # Get arguments
    parser = argparse.ArgumentParser(description='Setup nix.')
    parser.add_argument("-u", "--user", help='User to set up nix as.', default=USERNAMEVAR)
    parser.add_argument("-i", "--install", help="Execute non-root install.", action="store_true")

    # Save arguments.
    args = parser.parse_args()

    # Get non-root user information for specified user.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser(args.user)

    # Install immutable root services.
    immutable_root(USERNAMEVAR)
    # Install profile modifications.
    install_profile_config()
    # Perform install for user if requested.
    if args.install is True:
        call_install_script(USERNAMEVAR)
