#!/usr/bin/env python3
"""Setup nix as a normal user."""

# Python includes.
import argparse
import os
import subprocess
import sys
import tempfile
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = sys.path[0]
currentusername = os.getenv("USER")
homepath = CFunc.getnormaluser(currentusername)[2]

### Functions ###
def prompt_continue(prompt_enable: bool = False):
    """Prompt to continue."""
    if prompt_enable is False:
        input("Press Enter to continue.")
def setup_nix_envvars():
    """Add required nix environment variables."""
    if os.path.isfile("/etc/pki/tls/certs/ca-bundle.crt"):
        os.environ['NIX_SSL_CERT_FILE'] = "/etc/pki/tls/certs/ca-bundle.crt"
    os.environ['NIX_PROFILES'] = "/nix/var/nix/profiles/default {0}/.nix-profile".format(homepath)
    # Ensure nix is in path
    pathvar = os.environ.get('PATH')
    pathvar = pathvar + ":{0}/.nix-profile/bin".format(homepath)
    os.environ['PATH'] = pathvar
def install_nix():
    """Install nix."""
    tempfolder = tempfile.gettempdir()
    # Get nix install script
    nix_install_script = CFunc.downloadfile("https://nixos.org/nix/install", tempfolder)[0]
    # Install nix
    subprocess.run("sh {0} --no-daemon".format(nix_install_script), shell=True, check=True)
    # Add environment variables
    setup_nix_envvars()
    # Upgrade nix
    subprocess.run("nix-channel --update; nix-env -iA nixpkgs.nix", shell=True, check=True)
def install_homemanager():
    """Install home-manager."""
    setup_nix_envvars()
    # Add channel
    subprocess.run("nix-channel --add https://github.com/nix-community/home-manager/archive/master.tar.gz home-manager", shell=True, check=True)
    subprocess.run("nix-channel --update", shell=True, check=True)
    # # Set nix path
    os.environ['NIX_PATH'] = "{0}/.nix-defexpr/channels:/nix/var/nix/profiles/per-user/{1}/channels".format(homepath, currentusername)
    # Install
    subprocess.run("nix-shell '<home-manager>' -A install", shell=True, check=True)
def configure_nix():
    """Insert nix configuration."""
    # nix.conf
    if not os.path.isfile(os.path.join(homepath, ".config", "nix", "nix.conf")):
        os.makedirs(os.path.join(homepath, ".config", "nix"), exist_ok=True)
        with open(os.path.join(homepath, ".config", "nix", "nix.conf"), 'w') as f:
            f.write("experimental-features = nix-command flakes\n")
    # config.nix
    if not os.path.isfile(os.path.join(homepath, ".config", "nixpkgs", "config.nix")):
        os.makedirs(os.path.join(homepath, ".config", "nixpkgs"), exist_ok=True)
        with open(os.path.join(homepath, ".config", "nixpkgs", "config.nix"), 'w') as f:
            f.write("""
{
  # Enable searching for and installing unfree packages
  allowUnfree = true;
}
""")
def uninstall_nix():
    """Uninstall nix."""
    subprocess.run("sudo rm -rf $HOME/.nix-profile $HOME/.nix-profile $HOME/.nix-channels $HOME/.nix-defexpr", shell=True, check=False)
    subprocess.run("sudo rm -rf /etc/profile.d/rcustom_nix.sh", shell=True, check=False)
    # Immutable os instructions
    if os.path.isfile("/etc/systemd/system/mount-nix-prepare.service"):
        subprocess.run("sudo systemctl stop mount-nix-prepare; sudo systemctl disable --now mount-nix-prepare.service; sleep 1; sudo rm -rf /etc/systemd/system/mount-nix-prepare.service", shell=True, check=False)
        subprocess.run("sudo chattr -i / ; sudo umount -l /nix /var/lib/nix ; sleep 1 ; sudo rm -rf /nix /var/lib/nix ; sudo chattr +i /", shell=True, check=False)
    else:
        subprocess.run('sudo rm -rf /nix', shell=True, check=False)
    if os.path.isdir("/var/lib/nix"):
        subprocess.run("sudo rm -rf /var/lib/nix", shell=True, check=False)
    print("INFO: Remove nix information from '~/.bash_profile'")


### Begin Code ###
if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Setup nix.')
    parser.add_argument("-u", "--uninstall", help='Remove nix.', action="store_true")
    parser.add_argument("-m", "--homemanager", help='Only install home-manager (i.e. for NixOS).', action="store_true")
    parser.add_argument("-n", "--noprompt", help="Make changes without prompting.", action="store_true")

    # Save arguments.
    args = parser.parse_args()

    # Get non-root user information.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser(currentusername)
    print("Username is:", USERNAMEVAR)

    # Warn if root.
    if CFunc.is_root(checkstate=True, state_exit=False):
        print("WARNING: This script is being run as root. Make sure this is intended.")
        prompt_continue(args.noprompt)

    if args.uninstall:
        uninstall_nix()
    elif args.homemanager:
        install_homemanager()
    else:
        # Install Nix
        install_nix()
        configure_nix()
        install_homemanager()
