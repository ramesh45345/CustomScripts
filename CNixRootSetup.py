#!/usr/bin/env python3
"""Create immutable root configuration. Must run as root."""

# Python includes.
import argparse
import os
import shutil
import subprocess
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

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
    if not os.path.isdir(path):
        print("Changing bindmount path to /var/lib")
        path = "/var/lib"
    fstab_text = "{0}/nix    /nix    none    bind    0    0".format(path)
    if not CFunc.Fstab_CheckStringInFile("/etc/fstab", " /nix "):
        os.makedirs("{0}/nix".format(path), 0o777, exist_ok=True)
        CFunc.Fstab_AddLine("/etc/fstab", fstab_text)
        os.makedirs("/nix", exist_ok=True)
        subprocess.run(["mount", "/nix"], check=True)
        shutil.chown("/nix", user)
def create_nix_root_mutable_nobind(user: str):
    """Create /nix on local filesystem."""
    # Just using /nix on local filesystem.
    os.makedirs("/nix", exist_ok=True)
    shutil.chown("/nix", user)
def install_profile_config():
    """Install system profile script."""
    profile_text = r"""
[ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ] && . $HOME/.nix-profile/etc/profile.d/nix.sh
[ -e "$HOME/.nix-profile/etc/profile.d/hm-session-vars.sh" ] && . $HOME/.nix-profile/etc/profile.d/hm-session-vars.sh
"""
    with open(os.path.join(os.sep, "etc", "profile.d", "rcustom_nix.sh"), 'w') as f:
        f.write(profile_text)
    # Needed for Debian
    # https://unix.stackexchange.com/a/281923
    # https://unix.stackexchange.com/a/440617
    if os.path.isdir(os.path.join(os.sep, "etc", "X11", "Xsession.d")):
        with open(os.path.join(os.sep, "etc", "X11", "Xsession.d", "60nixcustom"), 'w') as f:
            f.write(profile_text)
def call_install_script(user: str):
    """Run the installation script as a normal user."""
    CFunc.run_as_user_su(user, "{0}/CNixUserSetup.py -n".format(SCRIPTDIR), error_on_fail=True)
def call_nix_update_user(user: str):
    """
    Run nix update as a normal user.
    This function is intended for use in scripts that run as root.
    """
    CFunc.run_as_user_su(user, "nix-channel --update; home-manager switch")


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
    if args.nixpath is not None and os.path.isdir(args.nixpath) and immutable_root is True:
        create_nix_root_immutable(USERNAMEVAR, os.path.abspath(args.nixpath))
    # If no path specified and immutable root.
    elif (args.nixpath is None or os.path.isdir(args.nixpath) is False) and immutable_root is True:
        create_nix_root_immutable(USERNAMEVAR)
    # If path specified and no immutable root.
    elif args.nixpath is not None and os.path.isdir(args.nixpath) is True and immutable_root is False:
        create_nix_root_mutable_bind(USERNAMEVAR, os.path.abspath(args.nixpath))
    # If no path specified and no immutable root.
    else:
        create_nix_root_mutable_nobind(USERNAMEVAR)

    # Install profile modifications.
    install_profile_config()
    # Perform install for user if requested.
    if args.install is True:
        call_install_script(USERNAMEVAR)
