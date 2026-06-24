#!/usr/bin/env python3
"""Virtual Machine functions"""

# Python includes.
import argparse
import functools
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

### Functions ###
# TODO: Add functions from Pkvm and PCreateChroot
def nmcli_connecteddevice():
    """Get the connected device from Network Manager."""
    # Get the device list, and convert it into a 2D list
    dev = None
    nmcli_dev = CFunc.subpout(f"nmcli --terse dev", error_on_fail=False)
    nmcli_array = []
    for nmcli_lines in nmcli_dev.split("\n"):
        nmcli_array += [nmcli_lines.split(":")]
    # Only return "connected" and not "connected (externally)"
    for line in nmcli_array:
        if line[2] == "connected":
            dev = line[0]
            break
    return dev


if __name__ == '__main__':
    # Get arguments
    parser = argparse.ArgumentParser(description='Virtual Machine functions.')
    parser.add_argument("-i", "--nmgetdev", help="Return the Network Manager connected device", action="store_true")
    args = parser.parse_args()

    if args.nmgetdev:
        print(f"{nmcli_connecteddevice()}", end="")
