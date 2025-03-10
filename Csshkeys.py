#!/usr/bin/env python3
"""Inject SSH keys into a remote computer."""

# Python includes.
import argparse
import functools
import os
import sys
import subprocess
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Inject SSH keys (priv and pub) into a remote computer.')
    parser.add_argument("-r", "--remotehost", help="Remote host to inject keys into. IP or hostname.")
    parser.add_argument("-u", "--user", help="User to install keys. (default: %(default)s)", default=None)
    parser.add_argument("-n", "--keynew", help='Generate a new priv/pub key pair for injection', action="store_true")
    parser.add_argument("-p", "--keypath", help='Path to keys (new or existing). (default: %(default)s)', default=os.getcwd())
    parser.add_argument("--sshport", type=str, help='SSH Port. (default: %(default)s)', default="22")
    args = parser.parse_args()

    CFunc.commands_check(["ssh", "ssh-keygen", "ssh-copy-id", "scp"])

    if not args.remotehost:
        sys.exit("ERROR: remotehost not specified. Exiting.")

    # Define key paths
    os.chdir(args.keypath)
    keyfile_priv = os.path.join(args.keypath, "id_ed25519")
    keyfile_pub = os.path.join(args.keypath, "id_ed25519.pub")
    # Generate keys
    if args.keynew or not os.path.exists(keyfile_priv):
        subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", '', "-f", keyfile_priv], check=True)

    # Check if keys exist regardless of generation.
    if not os.path.isfile(keyfile_priv):
        sys.exit(f"ERROR: {keyfile_priv} does not exist. Exiting.")
    if not os.path.isfile(keyfile_pub):
        sys.exit(f"ERROR: {keyfile_pub} does not exist. Exiting.")

    # Copy public keys to authorized_users
    subprocess.run(["ssh-copy-id", "-p", str(args.sshport), "-i", keyfile_priv, f"root@{args.remotehost}"], check=True)
    # Copy private and public keys
    subprocess.run(["scp", "-p", "-i", keyfile_priv, "-P", args.sshport, keyfile_priv, f"root@{args.remotehost}:~/.ssh/id_ed25519"])
    subprocess.run(["scp", "-p", "-i", keyfile_priv, "-P", args.sshport, keyfile_pub, f"root@{args.remotehost}:~/.ssh/id_ed25519.pub"])
    subprocess.run(["ssh", "-l", "root", "-i", keyfile_priv, "-p", str(args.sshport), args.remotehost, "chown root:root -R ~/.ssh"], check=True)
    # Copy .ssh folder for root into user
    if args.user:
        # Check remote group
        user_group = subprocess.run(["ssh", "-l", "root", "-i", keyfile_priv, "-p", str(args.sshport), args.remotehost, f"id -gn {args.user}"], stdout=subprocess.PIPE, universal_newlines=True, check=True).stdout.strip()
        # Find remote user home folder
        user_home = subprocess.run(["ssh", "-l", "root", "-i", keyfile_priv, "-p", str(args.sshport), args.remotehost, f'''bash -c "cd ~$(printf %q "{args.user}") && pwd"'''], stdout=subprocess.PIPE, universal_newlines=True, check=True).stdout.strip()
        print(user_group, user_home)
        # Copy ssh folder to user folder.
        subprocess.run(["ssh", "-l", "root", "-i", keyfile_priv, "-p", str(args.sshport), args.remotehost, f"rsync -rlptDxHAX --info=progress2 --del --numeric-ids ~/.ssh {user_home}/ ; chown {args.user}:{user_group} -R {user_home}/.ssh"], check=True)

    print(f"\nPrivate key: {keyfile_priv}\nPublic Key: {keyfile_pub}")
    print("\nScript End")
