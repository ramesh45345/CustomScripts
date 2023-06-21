#!/usr/bin/env python3
"""Configure Samba and other network services"""

# Python includes.
import argparse
import getpass
import os
import shutil
import subprocess
import time
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Install Samba Configuration.')
parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
parser.add_argument("-p", "--password", help='Set the password if not read from a file.', default="asdf")
parser.add_argument("-d", "--passfilepath", help='Set the password full file path when reading from a file.', default="/var/tmp/sambapass.txt")
parser.add_argument("-f", "--force", help='Force setting the samba password.', action="store_true")

# Save arguments.
args = parser.parse_args()

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)


### Functions ###
def subpout(cmd):
    """Get output from subprocess"""
    output = subprocess.run("{0}".format(cmd), shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
    return output
def inputpassword():
    """Get password from user"""
    pprompt = lambda: (getpass.getpass(), getpass.getpass('Retype password: '))
    p1, p2 = pprompt()
    while p1 != p2:
        print('Passwords do not match. Try again')
        p1, p2 = pprompt()
    return p1
def addsambatext(smbconfpath, folderpath):
    """Add folder path to file handle smbf"""
    if os.path.isdir(folderpath) and os.path.isfile(smbconfpath):
        abs_path = os.path.abspath(folderpath)
        basename_path = os.path.basename(abs_path)
        # Special case of "/" for root filesystem
        if abs_path == "/" and basename_path == "":
            basename_path = "rootfs"
        # Check if smbconf contains the path already as a share
        with open(smbconfpath, 'r') as smbconf_readonly:
            smbconf_lines = smbconf_readonly.readlines()
            foundtext = False
            for line in smbconf_lines:
                if "[{0}]".format(basename_path) in line:
                    foundtext = True
        # Add the share if not found.
        if foundtext is False:
            print("Adding Path {0} to {1}.".format(abs_path, smbconfpath))
            with open(smbconfpath, 'a') as smbconf_write:
                smbconf_write.write("""
[{0}]
    force user = {2}
    write list = {2}
    writeable = yes
    force group = {3}
    valid users = {2}
    path = {1}
    delete readonly = yes""".format(basename_path, abs_path, USERNAMEVAR, USERGROUP))
        else:
            print("Path {0} was detected. Skipping.".format(abs_path))


# Temp code write password to file
with open(args.passfilepath, 'w') as VAR:
    VAR.write(args.password)

# Use sambapass file if it exists
if os.path.exists(args.passfilepath) and os.path.isfile(args.passfilepath):
    with open(args.passfilepath, 'r') as VAR:
        SAMBAPASS = VAR.read().strip()
    print("Using password detected from {0}.".format(args.passfilepath))
else:
    print("Using password passed as an argument.")
    SAMBAPASS = args.password

if SAMBAPASS == "asdf":
    print("\nWARNING: Insecure default password is used. Ensure this is what you really want. Will proceed with insecure password if -f flag was used, otherwise will now prompt for new password.")

### Samba Password ###
# Set samba password for given user.
pdbout = subpout("pdbedit -L")
if USERNAMEVAR not in pdbout or args.force is True:
    # Ask user for samba password if password is insecure default.
    if args.noprompt is False:
        if SAMBAPASS == "asdf" or SAMBAPASS is None:
            print("\nPlease enter a samba password.")
            SAMBAPASS = inputpassword()
        input("Press Enter to continue.")
    print("Setting samba password for {0}.".format(USERNAMEVAR))
    # Use a subprocess pipe to feed the password in.
    pdbproc = subprocess.run(['pdbedit', '-a', '-u', USERNAMEVAR, '-t'], stdout=subprocess.PIPE, input="{0}\n{0}".format(SAMBAPASS), encoding='ascii')
    print(pdbproc.stdout.strip())
else:
    print("Password already set for user {0}. Skipping.".format(USERNAMEVAR))

# Remove sambapass file if it exists
if os.path.exists(args.passfilepath) and os.path.isfile(args.passfilepath):
    os.remove(args.passfilepath)


### Add Samba share entries ###
smbconf = "/etc/samba/smb.conf"
if os.path.isfile(smbconf):
    # Backup smb.conf
    currentdatetime = time.strftime("%Y-%m-%d_%H:%M")
    shutil.copy2(smbconf, "{0}.backup_{1}".format(smbconf, currentdatetime))
    # Add home folder of non-root user.
    addsambatext(smbconf, USERHOME)
    # Add root of filesystem.
    addsambatext(smbconf, "/")
    # Add detected folders under mnt.
    mntfolder = "/mnt"
    mntitems = os.listdir(mntfolder)
    for item in mntitems:
        mntabspathitem = os.path.abspath(os.path.join(mntfolder, item))
        if os.path.isdir(mntabspathitem):
            print("Detected {0}".format(mntabspathitem))
            addsambatext(smbconf, mntabspathitem)


### Avahi and nsswitch changes ###
nsswitchconf = "/etc/nsswitch.conf"
if os.path.isfile(nsswitchconf) is True:
    status = subprocess.run('grep -iq "^hosts:.*mdns_minimal" {0}'.format(nsswitchconf), shell=True)
    if status.returncode != 0:
        print("Adding mdns_minimal to {0}.".format(nsswitchconf))
        subprocess.run("sed -i '/^hosts:/ s=files=files mdns_minimal=' {0}".format(nsswitchconf), shell=True, check=True)
    else:
        print("{0} already modified. Skipping.".format(nsswitchconf))
else:
    print("{0} not found.".format(nsswitchconf))

avahidaemonconf = "/etc/avahi/avahi-daemon.conf"
if os.path.isfile(avahidaemonconf):
    print("Modifying {0}".format(avahidaemonconf))
    subprocess.run("sed -i 's/^use-ipv6=.*$/use-ipv6=yes/' {0}".format(avahidaemonconf), shell=True, check=True)
    subprocess.run("sed -i 's/^publish-workstation=.*$/publish-workstation=yes/' {0}".format(avahidaemonconf), shell=True, check=True)
else:
    print("{0} not found.".format(avahidaemonconf))
