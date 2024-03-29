#!/usr/bin/env python3
"""Setup nix as a normal user."""

# Python includes.
import argparse
import fileinput
import os
import subprocess
import tempfile
# Custom includes
import CFunc

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))
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
    # Cleanup
    if os.path.isfile(nix_install_script):
        os.remove(nix_install_script)
def install_homemanager():
    """Install home-manager."""
    setup_nix_envvars()
    # Add channel
    print("WARNING: This script assumes you are using master channel.")
    if CFunc.is_nixos() is True:
        subprocess.run("nix-channel --add https://nixos.org/channels/nixos-unstable nixos", shell=True, check=True)
    channel_url = "https://github.com/nix-community/home-manager/archive/master.tar.gz"
    subprocess.run("nix-channel --add {0} home-manager".format(channel_url), shell=True, check=True)
    subprocess.run("nix-channel --update", shell=True, check=True)
    # Set nix path
    customenv = os.environ
    customnixpath = customenv.get("NIX_PATH", '')
    if customnixpath:
        customnixpath += ":"
    customenv["NIX_PATH"] = customnixpath + "{0}/.nix-defexpr/channels:/nix/var/nix/profiles/per-user/{1}/channels".format(homepath, currentusername)
    # Install
    subprocess.run("nix-shell '<home-manager>' -A install", shell=True, check=True, env=customenv)

    # home.nix
    homeman_dirpath = os.path.join(homepath, ".config", "home-manager")
    homeman_filepath = os.path.join(homeman_dirpath, "home.nix")
    # Check if the pattern isn't found
    if os.path.isfile(homeman_filepath) and not CFunc.find_pattern_infile(homeman_filepath, "home.packages = with pkgs;"):
        print("Adding home.packages to Home Manager config.")
        for line in fileinput.FileInput(homeman_filepath, inplace=1):
            # Insert the package line after the homedirectory entry.
            if "home.homeDirectory = " in line:
                line = line.replace(line, line + """
  news.display = "silent";
  manual.manpages.enable = false;
  # https://github.com/nix-community/home-manager/issues/1439#issuecomment-1605851533
  targets.genericLinux.enable = true;
  xdg.mime.enable = true;
  xdg.systemDirs.data = [ "${config.home.homeDirectory}/.nix-profile/share/applications" ];
  # https://github.com/nix-community/home-manager/issues/1439#issuecomment-1106208294
  # Sync the desktop files (except for excludes) and ensure they have current timestamps.
  home.activation = {
    linkDesktopApplications = {
      after = [ "installPackages" "createXdgUserDirectories" ];
      before = [ ];
      data = ''
        touch "${config.home.homeDirectory}/.exclude_nix.txt"
        ${pkgs.rsync}/bin/rsync -azL --exclude-from="${config.home.homeDirectory}/.exclude_nix.txt" "${config.home.homeDirectory}/.nix-profile/share/applications/" "${config.xdg.dataHome}/applications/"
        chmod a+rwx -R "${config.xdg.dataHome}/applications"
        find "${config.xdg.dataHome}/applications/" -type f -name "*.desktop" -exec touch {} +
        ${pkgs.desktop-file-utils}/bin/update-desktop-database "${config.xdg.dataHome}/applications/"
      '';
    };
  };
""")
            print(line, end='')
        CFunc.find_replace(homeman_dirpath, "home.packages = [", "home.packages = with pkgs; [", "home.nix")
    else:
        print("home.packages found in config file. Not editing.")

    # Create exclulde file for rsync activation command.
    with open(os.path.join(homepath, ".exclude_nix.txt"), 'w') as f:
        f.write("mimeinfo.cache\n")
    # Initial rsync into .nix-share, to enable desktop shortcuts
    os.makedirs(os.path.join(homepath, ".nix-share"), exist_ok=True)
    subprocess.run('rsync -aL --del "{0}/.nix-profile/share" "{0}/.nix-share/"'.format(homepath), shell=True, check=True)
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
    subprocess.run("sudo rm -rf $HOME/.nix-profile $HOME/.nix-profile $HOME/.nix-channels $HOME/.nix-defexpr $HOME/.config/nix/ $HOME/.config/nixpkgs/ $HOME/.config/home-manager/", shell=True, check=False)
    subprocess.run("sudo rm -rf /etc/profile.d/rcustom_nix.sh", shell=True, check=False)
    # Immutable os instructions
    if os.path.isfile("/etc/systemd/system/mount-nix-prepare.service"):
        subprocess.run("sudo systemctl stop mount-nix-prepare; sudo systemctl disable --now mount-nix-prepare.service; sleep 1; sudo rm -rf /etc/systemd/system/mount-nix-prepare.service", shell=True, check=False)
        subprocess.run("sudo chattr -i / ; sudo umount -l /nix /var/lib/nix ; sleep 1 ; sudo rm -rf /nix /var/lib/nix ; sudo chattr +i /", shell=True, check=False)
    else:
        subprocess.run('sudo umount -l /nix ; sudo rm -rf /nix', shell=True, check=False)
    if os.path.isdir("/var/lib/nix"):
        subprocess.run("sudo rm -rf /var/lib/nix", shell=True, check=False)
    print("INFO: Remove nix information from '~/.bash_profile', and remove custom nix folder stored on another drive.")


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
