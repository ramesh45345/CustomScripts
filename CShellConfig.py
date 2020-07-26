#!/usr/bin/env python3
"""Configure enhancements for shells."""

# Python includes.
import argparse
import os
import sys
import subprocess
import shutil
import tempfile
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]

# Get arguments
parser = argparse.ArgumentParser(description='Configure enhancements for shells.')
parser.add_argument("-z", "--zsh", help='Configure zsh.', action="store_true")
parser.add_argument("-f", "--fish", help='Configure fish.', action="store_true")
parser.add_argument("-d", "--changedefault", help='Change the default shell based on whether zsh or fish is specified.', action="store_true")
args = parser.parse_args()

# Check if we are root.
rootstate = CFunc.is_root(checkstate=True, state_exit=False)
# Get non-root user information.
USERNAMEVAR, USERGROUP, USERVARHOME = CFunc.getnormaluser()
# Note: This folder is the root home folder.
ROOTHOME = os.path.expanduser("~root")

# Detect OS information
distro, release = CFunc.detectdistro()
print("Distro is {0}.".format(distro))
print("Release is {0}.".format(release))


### Generic Section ###
# Create bash-like shell rc additions
rc_additions = """
# Set root and non-root cmds.
if [ $(id -u) != "0" ]; then
    SUDOCMD="sudo"
    # Detect the normal user
    if [[ ! -z "$SUDO_USER" && "$SUDO_USER" != "root" ]]; then
        export USERNAMEVAR=$SUDO_USER
    elif [ "$USER" != "root" ]; then
        export USERNAMEVAR=$USER
    else
        export USERNAMEVAR=$(id 1000 -un)
    fi
else
    SUDOCMD=""
    USERNAMEVAR="$USERNAME"
fi
CUSTOMSCRIPTPATH="%s"
function sl () {
    sudo bash
}
if [ $(id -u) != "0" ]; then
    function pc () {
        EXISTPATH="$(pwd)"
        cd "$CUSTOMSCRIPTPATH"
        git fetch --all
        git diff
        git status
        if [ ! -z "$1" ]; then
            git add -A
            git commit -m "$1"
            git pull
            git push
        else
            echo "No commit message entered. Exiting."
        fi
        git pull
        cd "$EXISTPATH"
        unset EXISTPATH
    }
fi

# Expand $PATH to include the CustomScripts path.
if [ "${PATH#*$CUSTOMSCRIPTPATH}" = "${PATH}" ] && [ -d "$CUSTOMSCRIPTPATH" ]; then
    export PATH=$PATH:$CUSTOMSCRIPTPATH
fi

# Set editor to nano
export EDITOR=nano

# Add sbin paths if not in path
if [ "${PATH#*/sbin}" = "${PATH}" ]; then
    export PATH=/sbin:/usr/sbin:/usr/local/sbin:$PATH
fi

# Functions
function sst () {
    ssh -t "$@" "tmux attach || tmux new";
}
function rm_common () {
    for todel in "$@"; do
        echo "Deleting $(realpath $todel)"
    done
    echo "Press enter to continue or Ctrl-C to abort"
    read
}
function rmr () {
    rm_common "$@"
    for todel in "$@"; do
        rm -rf "$(realpath $todel)"
    done
}
function rms () {
    rm_common "$@"
    for todel in "$@"; do
        sudo rm -rf "$(realpath $todel)"
    done
}
function start () {
    echo "Starting systemd service $@."
    $SUDOCMD systemctl start "$@"
    $SUDOCMD systemctl status -l "$@"
}
function stop () {
    echo "Stopping systemd service $@."
    $SUDOCMD systemctl stop "$@"
    $SUDOCMD systemctl status -l "$@"
}
function en () {
    echo "Enabling systemd service $@."
    $SUDOCMD systemctl enable "$@"
    $SUDOCMD systemctl status -l "$@"
}
function dis () {
    echo "Disabling systemd service $@."
    $SUDOCMD systemctl disable "$@"
    $SUDOCMD systemctl status -l "$@"
}
function res () {
    echo "Restarting systemd service $@."
    $SUDOCMD systemctl restart "$@"
    $SUDOCMD systemctl status -l "$@"
}
function st () {
    echo "Getting status for systemd service $@."
    $SUDOCMD systemctl status -l "$@"
}
function dr () {
    echo "Executing systemd daemon-reload."
    $SUDOCMD systemctl daemon-reload
}
function startu () {
    echo "Starting systemd service $@ for user."
    systemctl --user start "$@"
    systemctl --user status -l "$@"
}
function stopu () {
    echo "Stopping systemd service $@ for user."
    systemctl --user stop "$@"
    systemctl --user status -l "$@"
}
function resu () {
    echo "Restarting systemd service $@ for user."
    systemctl --user restart "$@"
    systemctl --user status -l "$@"
}
function stu () {
    echo "Getting status for systemd service $@ for user."
    systemctl --user status -l "$@"
}
function dru () {
    echo "Executing systemd daemon-reload for user."
    systemctl --user daemon-reload
}
function fup () {
    flatpak_update
}
function flatpak_update () {
    if type flatpak &> /dev/null; then
        echo "Updating Flatpaks"
        flatpak update --system --assumeyes
    fi
}
function flatpak_clean () {
    if type flatpak &> /dev/null; then
        echo "Clean unused Flatpaks"
        flatpak uninstall --system --delete-data --unused --assumeyes
    fi
}
function flatpak_search () {
    # Don't search if using SSH.
    if type flatpak &> /dev/null && [ -z "$SSH_CLIENT" ] || [ -z "$SSH_TTY" ]; then
        echo "Searching Flatpaks"
        flatpak search $@
    fi
}
function snap_search () {
    if type snap &> /dev/null; then
        echo "Searching Snaps"
        snap find $@
    fi
}

if type -p apt-get &> /dev/null; then
    function ins () {
        echo "Installing $@."
        $SUDOCMD apt-get install $@
    }
    function rmv () {
        echo "Removing $@."
        $SUDOCMD apt-get --purge remove $@
    }
    function agu () {
        echo "Updating Repos."
        $SUDOCMD apt-get update
    }
    function se () {
        echo "Searching for $@."
        apt-cache search $@
        echo "Policy for $@."
        apt-cache policy $@
        snap_search "$@"
        flatpak_search "$@"
    }
    function cln () {
        echo "Auto-cleaning cache."
        $SUDOCMD apt-get autoclean
        echo "Auto-removing packages."
        $SUDOCMD apt-get autoremove --purge
        flatpak_clean
    }
    function up () {
        echo "Updating and Dist-upgrading system."
        $SUDOCMD apt-get update
        $SUDOCMD apt-get dist-upgrade
    }
elif type dnf &> /dev/null || type yum &> /dev/null; then
    if type dnf &> /dev/null; then
        PKGMGR=dnf
    elif type yum &> /dev/null; then
        PKGMGR=yum
    fi

    function ins () {
        echo "Installing $@."
        $SUDOCMD $PKGMGR install $@
    }
    function rmv () {
        echo "Removing $@."
        $SUDOCMD $PKGMGR remove $@
    }
    function se () {
        echo -e "\nSearching for $@."
        $SUDOCMD $PKGMGR search "$@"
        echo -e "\nSearching installed packages for $@."
        $SUDOCMD $PKGMGR list installed | grep -i "$@"
        echo -e "\nInfo for $@."
        $SUDOCMD $PKGMGR info "$@"
        snap_search "$@"
        flatpak_search "$@"
    }
    function cln () {
        echo "Auto-removing packages."
        $SUDOCMD $PKGMGR autoremove
        flatpak_clean
    }
    function up () {
        echo "Updating system."
        $SUDOCMD $PKGMGR upgrade --refresh -y
    }
elif type yay &> /dev/null || type pacman &> /dev/null; then
    if type yay &> /dev/null && [ $(id -u) != "0" ]; then
        PKGMGR=yay
    else
        PKGMGR=pacman
    fi

    function ins () {
        echo "Installing $@."
        $PKGMGR -S --needed $@
    }
    function rmv () {
        echo "Removing $@."
        $PKGMGR -Rsn $@
    }
    function se () {
        echo -e "\nSearching for $@."
        snap_search "$@"
        flatpak_search "$@"
        echo -e "\nPackage info"
        $PKGMGR -Si "$@"
        echo -e "\nPackages in repo."
        $PKGMGR -Ss "$@"
        echo -e "\nInstalled packages."
        $PKGMGR -Qs "$@"
    }
    function cln () {
        echo "Auto-removing packages."
        $PKGMGR -Qdtq | $PKGMGR -Rs -
        flatpak_clean
    }
    function up () {
        echo "Updating system."
        $PKGMGR -Syu --needed --noconfirm
    }
elif type rpm-ostree &> /dev/null; then
    function ins () {
        echo "Installing $@."
        $SUDOCMD rpm-ostree install $@
    }
    function rmv () {
        echo "Removing $@."
        $SUDOCMD rpm-ostree remove $@
    }
    function se () {
        echo -e "\nSearching for $@."
        snap_search "$@"
        flatpak_search "$@"
    }
    function cln () {
        echo "Auto-removing packages."
        flatpak_clean
    }
    function up () {
        echo "Updating system."
        $SUDOCMD rpm-ostree upgrade
    }
fi

# Load tmux upon interactive ssh connection
# References:
# https://stackoverflow.com/questions/27613209/how-to-automatically-start-tmux-on-ssh-session
# https://jordanelver.co.uk/blog/2010/11/27/automatically-attaching-to-a-tmux-session-via-ssh/
#
# If statement explanations:
# type tmux &> /dev/null : Check if the tmux command exists.
# [[ $- == *i* ]] : Check if the interactive flag has been set for the shell.
# [[ -z "$TMUX" ]] : Check if tmux is already running.
# [[ -n "$SSH_TTY" ]] : Ensure ssh tty exists.
if type tmux &> /dev/null && [[ $- == *i* ]] && [[ -z "$TMUX" ]] && [[ -n "$SSH_TTY" ]]; then
  # Connect to existing session, and if that fails, create a new session.
  tmux attach-session -t ssh_tmux || tmux new-session -s ssh_tmux
  # Exit ssh session if exiting tmux
  exit
fi
""" % SCRIPTDIR
# C-style printf string formatting was used to avoid collision with curly braces above.
# https://docs.python.org/3/library/stdtypes.html#old-string-formatting


######### Bash Section #########
# Generate profile file.
customprofile_path = os.path.join("/", "etc", "profile.d", "rcustom.sh")
# Check if the profile.d folder exists.
if os.path.isdir(os.path.dirname(customprofile_path)) and os.access(os.path.dirname(customprofile_path), os.W_OK):
    print("Writing {0}".format(customprofile_path))
    customprofile_text = """#!/bin/sh --this-shebang-is-just-here-to-inform-shellcheck--

# Expand $PATH to include the CustomScripts path.
if [ "${{PATH#*{0}}}" = "${{PATH}}" ] && [ -d "{0}" ]; then
    export PATH=$PATH:{0}
fi

# Set editor to nano
if [ -z "$EDITOR" ] || [ "$EDITOR" != "nano" ]; then
    export EDITOR=nano
fi

# Add sbin paths if not in path
if [ "${{PATH#*/sbin}}" = "${{PATH}}" ]; then
    export PATH=/sbin:/usr/sbin:/usr/local/sbin:$PATH
fi""".format(SCRIPTDIR)
    with open(customprofile_path, 'w') as file:
        file.write(customprofile_text)
else:
    print("ERROR: {0} is not writeable.".format(os.path.dirname(customprofile_path)))

# Generate bash script
BASHSCRIPT = "\nalias la='ls -lah --color=auto'"
BASHSCRIPT += rc_additions

# Set bash script
BASHSCRIPTPATH = os.path.join(USERVARHOME, ".bashrc")
print("Bash script path is {0}".format(BASHSCRIPTPATH))
if rootstate is True:
    BASHROOTSCRIPTPATH = os.path.join(ROOTHOME, ".bashrc")
    print("Bash root script path is {0}".format(BASHROOTSCRIPTPATH))

# Remove existing bash scripts and copy skeleton.
if os.path.isfile(BASHSCRIPTPATH):
    os.remove(BASHSCRIPTPATH)
if rootstate is True:
    if os.path.isfile(BASHROOTSCRIPTPATH):
        os.remove(BASHROOTSCRIPTPATH)

# Skeleton will get overwritten by bash-it below, this is left here just in case it is needed in the future.
if os.path.isfile("/etc/skel/.bashrc"):
    shutil.copy("/etc/skel/.bashrc", BASHSCRIPTPATH)
    if rootstate is True:
        shutil.copy("/etc/skel/.bashrc", BASHROOTSCRIPTPATH)
        shutil.chown(BASHSCRIPTPATH, USERNAMEVAR, USERGROUP)
else:
    # Create bashrc if no skeleton
    open(BASHSCRIPTPATH, 'a').close()
    if rootstate is True:
        open(BASHROOTSCRIPTPATH, 'a').close()
        shutil.chown(BASHSCRIPTPATH, USERNAMEVAR, USERGROUP)

# Install bash-it before modifying bashrc (which automatically deletes bashrc)
# If /opt exists, use it. If not Windows, make and use /var/opt
if os.path.isdir(os.path.join(os.sep, "opt")) and os.access(os.path.join(os.sep, "opt"), os.W_OK):
    repos_path = os.path.join(os.sep, "opt")
elif os.path.isdir(os.path.join(os.sep, "var")) and os.access(os.path.join(os.sep, "var"), os.W_OK) and not CFunc.is_windows():
    repos_path = os.path.join(os.sep, "var", "opt")
    os.makedirs(repos_path)
else:
    repos_path = os.path.join(USERVARHOME, "opt")
    os.makedirs(repos_path)
# Only do it if the current user can write to repos_path
bashit_path = os.path.join(repos_path, "bash-it")
if os.access(repos_path, os.W_OK):
    CFunc.gitclone("https://github.com/Bash-it/bash-it", bashit_path)
    subprocess.run("chmod -R a+rwx {0}".format(bashit_path), shell=True, check=True)
if os.path.isdir(bashit_path):
    subprocess.run("""
    [ "$(id -u)" = "0" ] && HOME={0}
    {1}/install.sh --silent
    """.format(ROOTHOME, bashit_path), shell=True, check=True)
    subprocess.run("""sed -i -- "s/BASH_IT_THEME=.*/BASH_IT_THEME='powerline'/g" {0}""".format(BASHSCRIPTPATH), shell=True, check=True)
    if rootstate is True:
        CFunc.run_as_user(USERNAMEVAR, "{0}/install.sh --silent".format(bashit_path), shutil.which("bash"), error_on_fail=True)
        subprocess.run("""sed -i -- "s/BASH_IT_THEME=.*/BASH_IT_THEME='powerline'/g" {0} {1}""".format(BASHROOTSCRIPTPATH, BASHSCRIPTPATH), shell=True, check=True)

# Install bash script
BASHSCRIPT_VAR = open(BASHSCRIPTPATH, mode='a')
BASHSCRIPT_VAR.write(BASHSCRIPT)
BASHSCRIPT_VAR.close()
os.chmod(BASHSCRIPTPATH, 0o644)
if rootstate is True:
    BASHSCRIPTUSER_VAR = open(BASHROOTSCRIPTPATH, mode='a')
    BASHSCRIPTUSER_VAR.write(BASHSCRIPT)
    BASHSCRIPTUSER_VAR.close()
    os.chmod(BASHROOTSCRIPTPATH, 0o644)
    shutil.chown(BASHSCRIPTPATH, USERNAMEVAR, USERGROUP)


######### Zsh Section #########
# Check if zsh exists
if args.zsh is True and shutil.which('zsh'):
    ZSHPATH = shutil.which('zsh')

    # Install oh-my-zsh for user
    CFunc.gitclone("git://github.com/robbyrussell/oh-my-zsh.git", "{0}/.oh-my-zsh".format(USERVARHOME))
    # Install zsh-syntax-highlighting
    CFunc.gitclone("https://github.com/zsh-users/zsh-syntax-highlighting.git", "{0}/.oh-my-zsh/plugins/zsh-syntax-highlighting".format(USERVARHOME))
    # Install zsh-autosuggestions
    CFunc.gitclone("https://github.com/zsh-users/zsh-autosuggestions", "{0}/.oh-my-zsh/plugins/zsh-autosuggestions".format(USERVARHOME))

    # Determine which plugins to install
    ohmyzsh_plugins = "git systemd zsh-syntax-highlighting zsh-autosuggestions"
    if distro == "Ubuntu":
        ohmyzsh_plugins += " ubuntu"
    if shutil.which("dnf"):
        ohmyzsh_plugins += " dnf"
    if shutil.which("yum"):
        ohmyzsh_plugins += " yum"
    # Write zshrc
    zshrc_path = os.path.join(USERVARHOME, ".zshrc")
    print("Writing {0}".format(zshrc_path))
    ZSHSCRIPT = """export ZSH={0}/.oh-my-zsh
ZSH_THEME="agnoster"
plugins=( {1} )
DISABLE_UPDATE_PROMPT=true
source $ZSH/oh-my-zsh.sh

# Expand $PATH to include the CustomScripts path.
if [ "${{PATH#*{2}}}" = "${{PATH}}" ] && [ -d "{2}" ]; then
    export PATH=$PATH:{2}
fi
""".format(USERVARHOME, ohmyzsh_plugins, SCRIPTDIR)
    ZSHSCRIPT += customrctext
    ZSHSCRIPT += rc_additions
    with open(zshrc_path, 'w') as file:
        file.write(ZSHSCRIPT)
else:
    print("zsh not detected, skipping configuration.")


######### tmux config Section #########
if shutil.which("tmux"):
    tmux_cfg_path = os.path.join(repos_path, ".tmux")
    # Clone tmux config repo
    CFunc.gitclone("https://github.com/gpakosz/.tmux.git", tmux_cfg_path)
    subprocess.run("chmod -R a+rw {0}".format(tmux_cfg_path), shell=True, check=True)
    tmux_cfg_common = os.path.join(tmux_cfg_path, ".tmux.conf")
    tmux_cfg_common_local = os.path.join(tmux_cfg_path, ".tmux.conf.local")
    # Modify Local settings before copying
    subprocess.run("""sed -i 's/tmux_conf_copy_to_os_clipboard=false/tmux_conf_copy_to_os_clipboard=true/g' {0}
sed -i 's/#set -g mouse on/set -g mouse on/g' {0}
sed -i 's/#set -g history-limit 10000/set -g history-limit 10000/g' {0}
""".format(tmux_cfg_common_local), shell=True, check=True)
    # Rebind n and p to cycle windows
    with open(tmux_cfg_common_local, 'a') as f:
        f.write("\nbind p previous-window\nbind n next-window\n")
    # Install tmux config
    if not os.path.exists(os.path.join(USERVARHOME, ".tmux.conf")):
        os.symlink(tmux_cfg_common, os.path.join(USERVARHOME, ".tmux.conf"))
    shutil.copy(os.path.join(tmux_cfg_path, ".tmux.conf.local"), USERVARHOME)
    shutil.chown(os.path.join(USERVARHOME, ".tmux.conf.local"), USERNAMEVAR, USERGROUP)
    if rootstate is True:
        if not os.path.exists(os.path.join(ROOTHOME, ".tmux.conf")):
            os.symlink(tmux_cfg_common, os.path.join(ROOTHOME, ".tmux.conf"))
        shutil.copy(os.path.join(tmux_cfg_path, ".tmux.conf.local"), ROOTHOME)


######### Fish Section #########
# Check if fish exists
if args.fish is True and shutil.which('fish'):
    # Change to temp dir. User can't install omf if current dir is root home folder.
    os.chdir(tempfile.gettempdir())

    # Test for omf
    if rootstate is True:
        status = CFunc.run_as_user(USERNAMEVAR, "omf update", shutil.which("fish"))
    else:
        status = subprocess.Popen("omf update", shell=True, executable=shutil.which("fish")).returncode

    # Install omf and plugins, since status was not 0
    if status != 0:
        # Install omf
        omf_git_path = os.path.join(tempfile.gettempdir(), "oh-my-fish")
        CFunc.gitclone("https://github.com/oh-my-fish/oh-my-fish", omf_git_path)
        if rootstate is True:
            CFunc.run_as_user(USERNAMEVAR, "cd {0}; bin/install --offline --noninteractive".format(omf_git_path), shutil.which("fish"), error_on_fail=True)
        else:
            subprocess.Popen("cd {0}; bin/install --offline --noninteractive", shell=True, executable=shutil.which("fish"), error_on_fail=True)
        shutil.rmtree(omf_git_path)
        # Install bobthefish
        if rootstate is True:
            CFunc.run_as_user(USERNAMEVAR, "omf install bobthefish", shutil.which("fish"), error_on_fail=True)
        else:
            subprocess.Popen("omf install bobthefish", shell=True, executable=shutil.which("fish"))

    # Personal note: To uninstall omf completely, use the following command as a normal user:
    # omf destroy; rm -rf ~/.config/omf/ ~/.cache/omf/ ~/.local/share/omf/

    # Generate fish script.
    FISHSCRIPT = """
# Set bobthefish options
set -g theme_display_user yes
# Set root and non-root cmds.
if [ (id -u) != "0" ]
    set SUDOCMD "sudo"
else
    set SUDOCMD ""
end
set CUSTOMSCRIPTPATH "{SCRIPTDIR}"
# Set editor
set -gx EDITOR nano
set -gx XZ_OPT "-T0"

# Function to check if in path
function checkpath
    set PATHSPLIT (string split " " $PATH)
    for x in $PATHSPLIT
        if test "$argv" = "$x"
            return 1
        end
    end
    return 0
end
# Function to add path
function pathadd
    if checkpath "$argv"; and test -d "$argv"
        set -gx PATH $PATH $argv
    end
end
# Set sbin in path
pathadd "/sbin"
pathadd "/usr/sbin"
pathadd "/usr/local/sbin"
# Set Custom Scripts in path
pathadd "$CUSTOMSCRIPTPATH"
# Add snap paths
pathadd "/snap/bin"
pathadd "/var/lib/snapd/snap/bin"

function sl
    xhost +localhost >> /dev/null
    env DISPLAY=$DISPLAY sudo bash
end
if [ (id -u) != "0" ]
    function pc
        set -x EXISTPATH (pwd)
        cd "$CUSTOMSCRIPTPATH"
        git fetch --all
        git diff
        git status
        if not test -z $argv
            git add -A
            git commit -m "$argv"
            git pull
            git push
        else
            echo "No commit message entered. Exiting."
        end
        git pull
        cd "$EXISTPATH"
        set -e EXISTPATH
    end
end
function sst
    ssh -t $argv "tmux attach; or tmux new"
end
function rm_common
    for todel in $argv
        echo Deleting (realpath $todel)
    end
    echo "Press enter to continue or Ctrl-C to abort"
    read
end
function rmr
    rm_common $argv
    for todel in $argv
        rm -rf (realpath $todel)
    end
end
function rms
    rm_common $argv
    for todel in $argv
        sudo rm -rf (realpath $todel)
    end
end
function start
    echo "Starting systemd service $argv."
    sudo systemctl start $argv
    sudo systemctl status -l $argv
end
function stop
    echo "Stopping systemd service $argv."
    sudo systemctl stop $argv
    sudo systemctl status -l $argv
end
function en
    echo "Enabling systemd service $argv."
    sudo systemctl enable $argv
    sudo systemctl status -l $argv
end
function dis
    echo "Disabling systemd service $argv."
    sudo systemctl disable $argv
    sudo systemctl status -l $argv
end
function res
    echo "Restarting systemd service $argv."
    sudo systemctl restart $argv
    sudo systemctl status -l $argv
end
function st
    echo "Getting status for systemd service $argv."
    sudo systemctl status -l $argv
end
function dr
    echo "Executing systemd daemon-reload."
    sudo systemctl daemon-reload
end
function startu
    echo "Starting systemd service $argv for user."
    systemctl --user start $argv
    systemctl --user status -l $argv
end
function stopu
    echo "Stopping systemd service $argv for user."
    systemctl --user stop $argv
    systemctl --user status -l $argv
end
function resu
    echo "Restarting systemd service $argv for user."
    systemctl --user restart $argv
    systemctl --user status -l $argv
end
function stu
    echo "Getting status for systemd service $argv for user."
    systemctl --user status -l $argv
end
function dru
    echo "Executing systemd daemon-reload for user."
    systemctl --user daemon-reload
end
function fup
    flatpak_update
end
function flatpak_update
    if type -q flatpak
        echo "Updating Flatpaks"
        flatpak update --system --assumeyes
    end
end
function flatpak_clean
    if type -q flatpak
        echo "Clean unused Flatpaks"
        flatpak uninstall --system --delete-data --unused --assumeyes
    end
end
function flatpak_search
    if type -q flatpak
        echo "Search Flatpaks"
        flatpak search $argv
    end
end
function snap_search
    if type -q snap
        echo "Search Snaps"
        snap find $argv
    end
end
# Set package manager functions
if type -q apt-get
    function ins
        echo "Installing $argv."
        sudo apt-get install $argv
    end
    function rmv
        echo "Removing $argv."
        sudo apt-get --purge remove $argv
    end
    function agu
        echo "Updating Repos."
        sudo apt-get update
    end
    function se
        echo "Searching for $argv."
        apt-cache search $argv
        echo "Policy for $argv."
        apt-cache policy $argv
        snap_search $argv
        flatpak_search $argv
    end
    function cln
        echo "Auto-cleaning cache."
        sudo apt-get autoclean
        echo "Auto-removing packages."
        sudo apt-get autoremove --purge
        flatpak_clean
    end
    function up
        echo "Updating and Dist-upgrading system."
        sudo apt-get update
        sudo apt-get dist-upgrade
    end
else if type -q dnf; or type -q yum
    if type -q dnf
        set PKGMGR dnf
    else if type -q yum
        set PKGMGR yum
    end
    function ins
        echo "Installing $argv."
        sudo $PKGMGR install $argv
    end
    function rmv
        echo "Removing $argv."
        sudo $PKGMGR remove $argv
    end
    function se
        echo -e "\\nSearching for $argv."
        sudo $PKGMGR search $argv
        echo -e "\\nSearching installed packages for $argv."
        sudo $PKGMGR list installed | grep -i $argv
        echo -e "\\nInfo for $argv."
        sudo $PKGMGR info $argv
        snap_search $argv
        flatpak_search $argv
    end
    function cln
        echo "Auto-removing packages."
        sudo $PKGMGR autoremove
        flatpak_clean
    end
    function up
        echo "Updating system."
        sudo $PKGMGR update --refresh -y
    end
else if type -q yay
    function ins
        echo "Installing $argv."
        yay -S --needed $argv
    end
    function rmv
        echo "Removing $argv."
        yay -Rsn $argv
    end
    function se
        echo -e "\\nSearching for $argv."
        snap_search $argv
        flatpak_search $argv
        echo -e "\\nPackage info"
        yay -Si $argv
        echo -e "\\nPackages in repo."
        yay -Ss $argv
        echo -e "\\nInstalled packages."
        yay -Qs $argv
    end
    function cln
        echo "Auto-removing packages."
        yay -Qdtq | yay -Rs -
        flatpak_clean
    end
    function up
        echo "Updating system."
        yay -Syu --needed --noconfirm
    end
else if type -q rpm-ostree
    function ins
        echo "Installing $argv."
        sudo rpm-ostree install $argv
    end
    function rmv
        echo "Removing $argv."
        sudo rpm-ostree remove $argv
    end
    function se
        echo -e "\\nSearching for $argv."
        snap_search $argv
        flatpak_search $argv
    end
    function cln
        echo "Auto-removing packages."
        flatpak_clean
    end
    function up
        echo "Updating system."
        sudo rpm-ostree upgrade
    end
end
""".format(SCRIPTDIR=SCRIPTDIR)

    # Set fish script
    FISHSCRIPTUSERPATH = os.path.join(USERVARHOME, ".config", "fish", "config.fish")
    # Create path if it doesn't existing
    os.makedirs(os.path.dirname(FISHSCRIPTUSERPATH), exist_ok=True)

    # Install fish script for user (overwrite previous script)
    with open(FISHSCRIPTUSERPATH, mode='w') as f:
        f.write(FISHSCRIPT)
    os.chmod(FISHSCRIPTUSERPATH, 0o644)

    if rootstate is True:
        subprocess.run("chown -R {0}:{1} {2}".format(USERNAMEVAR, USERGROUP, os.path.dirname(FISHSCRIPTUSERPATH)), shell=True, check=True)


# Fix permissions of home folder if the script was run as root.
if rootstate is True:
    subprocess.run("chown -R {0}:{1} {2}".format(USERNAMEVAR, USERGROUP, USERVARHOME), shell=True, check=True)


######### Default Shell Configuration #########
# Change the default shell for zsh only.
default_shell_value = None
if args.changedefault is True and args.zsh is True:
    default_shell_value = shutil.which("zsh")

# Perform the shell change
if rootstate is True and args.changedefault is True and default_shell_value:
    # Change shells for user.
    print("Changing shell for user {0} to {1}.".format(USERNAMEVAR, default_shell_value))
    subprocess.run("chsh -s {0} {1}".format(default_shell_value, USERNAMEVAR), shell=True, check=True)
elif rootstate is False and args.changedefault is True and default_shell_value:
    # Change the shells for this user.
    print("Changing shell for the current user to {0}.".format(default_shell_value))
    subprocess.run("chsh -s {0}".format(default_shell_value), shell=True, check=True)

print("Script finished successfully.")
