#!/usr/bin/env python3
"""Synchronize folders."""

# Python includes.
import argparse
import datetime
import functools
import os
import shutil
import subprocess
import sys
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Ensure that certain commands exist.
    CFunc.commands_check(["rsync"])

    # Get arguments
    parser = argparse.ArgumentParser(description='Create and run a Virtual Machine.')
    parser.add_argument('source', type=str, help='Source Folder')
    parser.add_argument('destination', type=str, help='Destination Folder')
    parser.add_argument("-a", "--noattrib", help="Disable attribute and ACL checks.", action="store_true")
    parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
    parser.add_argument("-p", "--sshport", type=int, help='For ssh hosts, use this port.', default=0)
    parser.add_argument("-x", "--skipdryrun", help="Skip the dry run.", action="store_true")
    args = parser.parse_args()

    sshport_text = ""
    if args.sshport > 0:
        sshport_text = r'-e "ssh -p {0}"'.format(args.sshport)
    if args.noattrib:
        sync_opts = "-axH"
    else:
        sync_opts = "-axHAX"
    cmd_options = f"--numeric-ids --del {sync_opts} {sshport_text}"
    # Add source and destination to end of command options.
    cmd_options = f"{cmd_options} {args.source} {args.destination}"

    # Full command and dry run command
    cmd_dryrun = f"rsync -nvi {cmd_options}"
    cmd_full = f"rsync --info=progress2 {cmd_options}"

    print(f"""
Source: {args.source}
Destination: {args.destination}
Executing: {cmd_full}
""")

    if not args.skipdryrun:
        subprocess.run(cmd_dryrun, shell=True, check=False)

    if args.noprompt is False:
        input("Press Enter to continue.")

    # Save start time.
    beforetime = datetime.datetime.now()

    # Run sync
    subprocess.run(cmd_full, shell=True, check=False)
    subprocess.run(["sync"], shell=False, check=True)

    # Save finish time.
    finishtime = datetime.datetime.now()
    print(f"Sync to {args.destination} completed in {str(finishtime - beforetime)}")
