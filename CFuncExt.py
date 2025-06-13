#!/usr/bin/env python3
"""
General Python Extended Functions
Includes distribution specific and more complex common functions.
To run a function in this script that doesn't have an argument switch:
```
sudo python -c "import CFuncExt; CFuncExt.topgrade_install()" ; sudo rm -rf ./__pycache__/
```
"""

# Python includes.
import fileinput
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib
# Custom includes
import CFunc
import CNixRootSetup

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))


### Functions ###
def numix_icons(iconfolder=os.path.join(os.sep, "usr", "local", "share", "icons")):
    """
    Install Numix Circle icons using git.
    """
    # Icons
    os.makedirs(iconfolder, exist_ok=True)
    # Numix Icon Theme
    shutil.rmtree(os.path.join(iconfolder, "numix-icon-theme"), ignore_errors=True)
    shutil.rmtree(os.path.join(iconfolder, "Numix"), ignore_errors=True)
    shutil.rmtree(os.path.join(iconfolder, "Numix-Light"), ignore_errors=True)
    CFunc.gitclone("https://github.com/numixproject/numix-icon-theme.git", os.path.join(iconfolder, "numix-icon-theme"))
    shutil.move(os.path.join(iconfolder, "numix-icon-theme", "Numix"), iconfolder)
    shutil.move(os.path.join(iconfolder, "numix-icon-theme", "Numix-Light"), iconfolder)
    shutil.rmtree(os.path.join(iconfolder, "numix-icon-theme"), ignore_errors=True)
    subprocess.run("gtk-update-icon-cache {0}".format(os.path.join(iconfolder, "Numix")), shell=True, check=True)
    # Numix Circle Icons
    shutil.rmtree(os.path.join(iconfolder, "numix-icon-theme-circle"), ignore_errors=True)
    shutil.rmtree(os.path.join(iconfolder, "Numix-Circle"), ignore_errors=True)
    shutil.rmtree(os.path.join(iconfolder, "Numix-Circle-Light"), ignore_errors=True)
    CFunc.gitclone("https://github.com/numixproject/numix-icon-theme-circle.git", os.path.join(iconfolder, "numix-icon-theme-circle"))
    shutil.move(os.path.join(iconfolder, "numix-icon-theme-circle", "Numix-Circle"), iconfolder)
    shutil.move(os.path.join(iconfolder, "numix-icon-theme-circle", "Numix-Circle-Light"), iconfolder)
    shutil.rmtree(os.path.join(iconfolder, "numix-icon-theme-circle"), ignore_errors=True)
    if shutil.which("gtk-update-icon-cache"):
        subprocess.run("gtk-update-icon-cache {0}".format(os.path.join(iconfolder, "Numix-Circle")), shell=True, check=True)
        subprocess.run("gtk-update-icon-cache {0}".format(os.path.join(iconfolder, "Numix-Circle-Light")), shell=True, check=True)
def SudoersEnvSettings(sudoers_file=os.path.join(os.sep, "etc", "sudoers")):
    """
    Change sudoers settings.
    """
    if os.path.isfile(sudoers_file):
        CFunc.BackupSudoersFile(sudoers_file)
        with open(sudoers_file, 'r') as sources:
            lines = sources.readlines()
        with open(sudoers_file, mode='w') as f:
            for line in lines:
                # Debian/Ubuntu use tabs, Fedora uses spaces. Check for both.
                line = re.sub(r'^(Defaults(\t|\s{4}|\s{1})mail_badpass)', r'# \1', line)
                # Set to not reset environment when sudoing.
                line = re.sub(r'^(Defaults(\t|\s{4}|\s{1})env_reset)$', r'Defaults\t!env_reset', line)
                line = re.sub(r'^(Defaults(\t|\s{4}|\s{1})secure_path)', r'# \1', line)
                f.write(line)
        CFunc.CheckRestoreSudoersFile(sudoers_file)
    else:
        print("ERROR: {0} does not exists, not modifying sudoers.".format(sudoers_file))
def GrubEnvAdd(grub_config_file, grub_line_detect, grub_line_add):
    """
    Add parameters to a given config line in the grub default config.
    grub_config = os.path.join(os.sep, "etc", "default", "grub")
    grub_line_detect = "GRUB_CMDLINE_LINUX_DEFAULT"
    grub_line_add = "mitigations=off"
    """
    if os.path.isfile(grub_config_file):
        if not CFunc.find_pattern_infile(grub_config_file, grub_line_add):
            with open(grub_config_file, 'r') as sources:
                grub_lines = sources.readlines()
            with open(grub_config_file, mode='w') as f:
                for line in grub_lines:
                    # Add mitigations line.
                    if grub_line_detect in line:
                        line = re.sub(r'{0}="(.*)"'.format(grub_line_detect), r'{0}="\g<1> {1}"'.format(grub_line_detect, grub_line_add), line)
                    f.write(line)
        else:
            print("NOTE: file {0} already modified config {1}.".format(grub_config_file, grub_line_detect))
    else:
        print("ERROR, file {0} does not exist.".format(grub_config_file))
def GrubUpdate():
    """
    Update grub configuration, if detected.
    """
    grub_default_cfg = os.path.join(os.sep, "etc", "default", "grub")
    if os.path.isfile(grub_default_cfg):
        # Uncomment
        subprocess.run("sed -i '/^#GRUB_TIMEOUT=.*/s/^#//g' {0}".format(grub_default_cfg), shell=True, check=True)
        # Comment
        subprocess.run("sed -i '/GRUB_HIDDEN_TIMEOUT/ s/^#*/#/' {0}".format(grub_default_cfg), shell=True, check=True)
        subprocess.run("sed -i '/GRUB_HIDDEN_TIMEOUT_QUIET/ s/^#*/#/' {0}".format(grub_default_cfg), shell=True, check=True)
        # Change timeout
        subprocess.run("sed -i 's/GRUB_TIMEOUT=.*$/GRUB_TIMEOUT=1/g' {0}".format(grub_default_cfg), shell=True, check=True)
        subprocess.run("sed -i 's/GRUB_HIDDEN_TIMEOUT=.*$/GRUB_HIDDEN_TIMEOUT=1/g' {0}".format(grub_default_cfg), shell=True, check=True)
        # Change timeout style to menu
        subprocess.run("sed -i 's/^GRUB_TIMEOUT_STYLE=.*/GRUB_TIMEOUT_STYLE=menu/g' {0}".format(grub_default_cfg), shell=True, check=True)
        # Update grub
        if shutil.which("update-grub2"):
            print("Updating grub config using update-grub2.")
            subprocess.run(["update-grub2"], check=True)
        elif shutil.which("update-grub"):
            print("Updating grub config using update-grub.")
            subprocess.run(["update-grub"], check=True)
        elif os.path.isfile(os.path.join(os.sep, "boot", "grub2", "grub.cfg")):
            print("Updating grub config using mkconfig grub2.")
            subprocess.run(["grub2-mkconfig", "-o", os.path.join(os.sep, "boot", "grub2", "grub.cfg")], check=True)
        elif os.path.isfile(os.path.join(os.sep, "boot", "grub", "grub.cfg")):
            print("Updating grub config using mkconfig grub.")
            subprocess.run(["grub-mkconfig", "-o", os.path.join(os.sep, "boot", "grub", "grub.cfg")], check=True)
        elif os.path.isfile(os.path.join(os.sep, "boot", "efi", "EFI", "fedora", "grub.cfg")):
            print("Update fedora efi grub config.")
            subprocess.run(["grub2-mkconfig", "-o", os.path.join(os.sep, "boot", "efi", "EFI", "fedora", "grub.cfg")], check=True)
def FirewalldConfig():
    """
    Set common firewalld settings.
    """
    if shutil.which("firewall-cmd"):
        subprocess.run("firewall-cmd --permanent --add-service=ssh", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-service=samba", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-service=syncthing", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-service=syncthing-gui", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-service=synergy", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-service=cockpit", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-service=mdns", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-port=1025-65535/udp", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-port=1025-65535/tcp", shell=True, check=True)
        # Add masquerade for docker/podman.
        subprocess.run("firewall-cmd --zone=trusted --permanent --add-masquerade", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --add-masquerade", shell=True, check=True)
        subprocess.run("firewall-cmd --reload", shell=True, check=True)
def ytdlp_install(install_path: str = os.path.join(os.sep, "usr", "local", "bin")):
    """
    Install yt-dlp.
    """
    CFunc.downloadfile("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp", install_path, overwrite=True)
    os.chmod(os.path.join(install_path, "yt-dlp"), 0o755)
    # Symlink youtube-dl
    if os.path.islink(os.path.join(install_path, "youtube-dl")):
        os.unlink(os.path.join(install_path, "youtube-dl"))
    os.chdir(install_path)
    os.symlink("yt-dlp", "youtube-dl")
def nix_standalone_install(username: str, packages: str):
    """Install standalone version of nix."""
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser(username)
    # Install nix
    subprocess.run("{0}/CNixRootSetup.py -i".format(SCRIPTDIR), shell=True, check=True)
    # Add apps to home.nix
    homeman_filepath = os.path.join(USERHOME, ".config", "home-manager", "home.nix")
    # Check if the pattern isn't found
    if os.path.isfile(homeman_filepath) and not CFunc.find_pattern_infile(homeman_filepath, "unrar"):
        print("Adding home.packages to Home Manager config.")
        for line in fileinput.FileInput(homeman_filepath, inplace=1):
            # Insert the package line after the homedirectory entry.
            if "home.packages = with pkgs; [" in line:
                line = line.replace(line, line + """{0}
    unrar
""".format(packages))
            print(line, end='')
    else:
        print("home.packages found in config file. Not editing.")
    # Nix upgrade
    CNixRootSetup.call_nix_update_user(USERNAMEVAR)
def topgrade_install(dest_folder: str = os.path.join(os.sep, "usr", "local", "bin")):
    """Install the latest topgrade version from github"""
    releasejson_link = "https://api.github.com/repos/topgrade-rs/topgrade/tags"
    # Get the json data from GitHub.
    with urllib.request.urlopen(releasejson_link) as releasejson_handle:
        releasejson_data = json.load(releasejson_handle)
    for release in releasejson_data:
        # Stop after the first (latest) release is found.
        latestrelease = release["name"].strip().replace("v", "")
        break
    if os.path.exists(dest_folder):
        print("Detected topgrade version: {0}".format(latestrelease))
        tempfolder = tempfile.gettempdir()
        # Download release
        topgrade_gz_file = CFunc.downloadfile(f"https://github.com/topgrade-rs/topgrade/releases/download/v{latestrelease}/topgrade-v{latestrelease}-x86_64-unknown-linux-gnu.tar.gz", tempfolder)[0]
        # Unzip release
        subprocess.run(["tar", "-xf", topgrade_gz_file, "-C", dest_folder], check=True)
        # Set permissions for extracted file.
        unzipped_path = os.path.join(dest_folder, "topgrade")
        if os.path.isfile(unzipped_path):
            os.chmod(unzipped_path, 0o777)
        else:
            print(f"ERROR: {unzipped_path} does not exist.")
        # Cleanup
        if os.path.isfile(topgrade_gz_file):
            os.remove(topgrade_gz_file)
    else:
        print(f"ERROR: {dest_folder} does not exist.")


if __name__ == '__main__':
    import argparse

    # Get arguments
    parser = argparse.ArgumentParser(description='CFunc Extras.')
    parser.add_argument("-f", "--firewalldcfg", help='Firewalld configuration', action="store_true")
    parser.add_argument("-g", "--grubupdate", help='Run Grub update', action="store_true")
    parser.add_argument("-n", "--numix", help='Numix Circle Icons', action="store_true")
    parser.add_argument("-s", "--sudoenv", help='Sudo Environment Changes', action="store_true")
    parser.add_argument("--ytdlp", help='Install yt-dlp', action="store_true")
    args = parser.parse_args()

    # Run functions
    if args.firewalldcfg:
        FirewalldConfig()
    if args.grubupdate:
        GrubUpdate()
    if args.numix:
        numix_icons()
    if args.sudoenv:
        SudoersEnvSettings()
    if args.ytdlp:
        ytdlp_install()
