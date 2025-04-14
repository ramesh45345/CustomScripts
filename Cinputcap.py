#!/usr/bin/env python3
"""Click input capture dialogue when detected."""

# Python includes.
import argparse
import functools
import os
import subprocess
import time
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))


### Functions ###
def ydo_click(x: int = 0, y: int = 0):
    """Have ydotool click in a specified coordinate."""
    # Need to move the cursor, becasue there are a few issues with absolute coordinates.
    subprocess.run("ydotool mousemove -a -x 0 -y 0", shell=True, check=True)
    subprocess.run("ydotool mousemove -x -99999 -y -99999", shell=True, check=True)
    time.sleep(0.05)
    subprocess.run("ydotool mousemove -x -99999 -y -99999", shell=True, check=True)
    time.sleep(0.05)
    # Now really move the mouse cursor and click.
    subprocess.run(f"ydotool mousemove -x {x} -y {y}", shell=True, check=True)
    time.sleep(0.05)
    subprocess.run("ydotool click C0", shell=True, check=True)
def detect_click(x: int, y: int):
    """Detect window and click."""
    search_titles = ["Remote control requested", "Input Capture Requested"]
    title_detected = False
    for title in search_titles:
        out = CFunc.subpout(f'kdotool search "{title}"')
        if args.debug:
            print(f"kdotool output: {out}")
        if out != "":
            title_detected = True
    if title_detected is True:
        if args.debug:
            print("Title detected.")
        ydo_click(args.xcoord, args.ycoord)


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Get arguments
    parser = argparse.ArgumentParser(description='Click input capture dialogue when detected.')
    parser.add_argument("-x", "--xcoord", type=int, help='X coordinate for click', default=170)
    parser.add_argument("-y", "--ycoord", type=int, help='Y coordinate for click', default=250)
    parser.add_argument("-o", "--oneshot", help='Do not loop.', action="store_true")
    parser.add_argument("-d", "--debug", help='Print debug lines.', action="store_true")
    args = parser.parse_args()

    # Check for tools
    CFunc.commands_check(["ydotool", "kdotool"])

    if args.oneshot:
        detect_click(args.xcoord, args.ycoord)
    else:
        while True:
            detect_click(args.xcoord, args.ycoord)
            time.sleep(1)
