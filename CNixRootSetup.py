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
def create_nix_root_immutable(user: str, path: str = "/var/lib"):
    """
    Create /nix root with correct ownership.
    Install service which creates /nix for immutable operating system.
    Path must not use "nix" in the name. Example: /var/lib, /mnt/Storage/VMs
    """
    if os.path.isdir(path):
        # Create /nix for immutable fs OS
        nix_service_text = """
[Unit]
Description=Prepare nix mount points

[Service]
Type=oneshot
RequiresMountsFor={0}
ExecStartPre=chattr -i /
ExecStart=/bin/sh -c "mkdir -p /nix"
ExecStart=/bin/sh -c "mkdir -p {0}/nix"
ExecStart=/bin/sh -c "mount --bind {0}/nix /nix"
ExecStopPost=chattr +i /

[Install]
WantedBy=local-fs.target
    """.format(path)
        CFunc.systemd_createsystemunit("mount-nix-prepare.service", nix_service_text, sysenable=True)
        subprocess.run(["systemctl", "restart", "mount-nix-prepare.service"], check=True)
        shutil.chown(os.path.join(os.sep, "nix"), user)
def create_nix_root_mutable_bind(user: str, path: str):
    """Create bind mount for /nix on mutable os."""

def create_nix_root_mutable_nobind(user: str):
    """Create /nix on local filesystem."""
    # Just using /nix on local filesystem.
    os.makedirs("/nix", exist_ok=True)
    shutil.chown("/nix", user)
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
    parser.add_argument("-p", "--nixpath", help='Specify custom path to bind mount /nix at.', type=str)
    parser.add_argument("-i", "--install", help="Execute non-root install.", action="store_true")

    # Save arguments.
    args = parser.parse_args()

    # Get non-root user information for specified user.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser(args.user)

    # Create nix root.
    immutable_root = immutable_root_detect()
    if os.path.isdir(args.nixpath) and immutable_root is True:
        create_nix_root_immutable(USERNAMEVAR, os.path.abspath(args.nixpath))
    # If no path specified and immutable root.
    elif os.path.isdir(path) is False and immutable_root is True:
        create_nix_root_immutable(USERNAMEVAR)
    # If path specified and no immutable root.
    elif os.path.isdir(path) is True and immutable_root is False:
        create_nix_root_mutable_bind(USERNAMEVAR, os.path.abspath(args.nixpath))
    # If no path specified and no immutable root.
    else:
        create_nix_root_mutable_nobind(USERNAMEVAR)

    # Install profile modifications.
    install_profile_config()
    # Perform install for user if requested.
    if args.install is True:
        call_install_script(USERNAMEVAR)
