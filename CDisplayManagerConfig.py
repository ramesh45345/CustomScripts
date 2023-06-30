#!/usr/bin/env python3
"""Install Display Manager Configuration."""

# Python includes.``
import argparse
import os
import shutil
import subprocess
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Configure the Display Manager.')
parser.add_argument("-a", "--autologin", help='Force automatic login in display managers.', action="store_true")

# Save arguments.
args = parser.parse_args()

# Get VM State
vmstatus = CFunc.getvmstate()

# Exit if not root.
CFunc.is_root(True)

# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
MACHINEARCH = CFunc.machinearch()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)


### LightDM Section ###
if shutil.which("lightdm"):
    print("\n Processing lightdm configuration.")
    if "autologin" not in open('/etc/group', 'r').read():
        subprocess.run("groupadd autologin", shell=True)
    subprocess.run("gpasswd -a {0} autologin".format(USERNAMEVAR), shell=True)
    # Enable autologin
    if vmstatus or args.autologin is True:
        if os.path.isfile("/etc/lightdm/lightdm.conf"):
            subprocess.run("sed -i 's/#autologin-user=/autologin-user={0}/g' /etc/lightdm/lightdm.conf".format(USERNAMEVAR), shell=True)
        os.makedirs("/etc/lightdm/lightdm.conf.d", exist_ok=True)
        with open('/etc/lightdm/lightdm.conf.d/12-autologin.conf', 'w') as file:
            file.write("""[SeatDefaults]
autologin-user={0}""".format(USERNAMEVAR))
# Enable listing of users
if os.path.isfile("/etc/lightdm/lightdm.conf"):
    subprocess.run("sed -i 's/#greeter-hide-users=false/greeter-hide-users=false/g' /etc/lightdm/lightdm.conf", shell=True)


### GDM Section ###
if shutil.which("gdm") or shutil.which("gdm3") or shutil.which("/usr/sbin/gdm3"):
    # Enable gdm autologin for virtual machines.
    if vmstatus or args.autologin is True:
        print("Enabling gdm autologin for {0}.".format(USERNAMEVAR))
        # https://afrantzis.wordpress.com/2012/06/11/changing-gdmlightdm-user-login-settings-programmatically/
        # Get dbus path for the user
        USER_PATH = CFunc.subpout("dbus-send --print-reply=literal --system --dest=org.freedesktop.Accounts /org/freedesktop/Accounts org.freedesktop.Accounts.FindUserByName string:{0}".format(USERNAMEVAR))
        # Send the command over dbus to freedesktop accounts.
        subprocess.run("dbus-send --print-reply --system --dest=org.freedesktop.Accounts {0} org.freedesktop.Accounts.User.SetAutomaticLogin boolean:true".format(USER_PATH), shell=True)
        # https://hup.hu/node/114631
        # Can check options with following command:
        # dbus-send --system --dest=org.freedesktop.Accounts --print-reply --type=method_call $USER_PATH org.freedesktop.DBus.Introspectable.Introspect
        # qdbus --system org.freedesktop.Accounts $USER_PATH org.freedesktop.Accounts.User.AutomaticLogin


### SDDM Section ###
if shutil.which("sddm"):
    print("\n Processing sddm configuration.")
    # Enable autologin
    if vmstatus or args.autologin is True:
        plasma_desktop_file = "plasma.desktop"
        if os.path.isfile("/usr/share/xsessions/plasmax11.desktop"):
            plasma_desktop_file = "plasmax11.desktop"
        os.makedirs("/etc/sddm.conf.d", exist_ok=True)
        with open("/etc/sddm.conf.d/autologin.conf", 'w') as f:
            f.write("""[Autologin]
User={0}
Session={1}
""".format(USERNAMEVAR, plasma_desktop_file))
