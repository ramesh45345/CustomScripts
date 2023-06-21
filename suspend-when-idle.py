#!/usr/bin/env python3
"""Suspend on Network Inactivity"""

# Python includes.
import argparse
import datetime
import logging
import os
import shutil
import subprocess
import sys
import time

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Suspend on Network Inactivity.')
parser.add_argument("-d", "--debug", help='Use Debug Logging', action="store_true")
parser.add_argument("-s", "--idletime", help='Number of minutes before sleeping (default: %(default)s)', type=int, default=30)
parser.add_argument("-t", "--diskthreshold", help='Disk threshold for idleness (in kb, default: %(default)s)', type=float, default=100.0)
args = parser.parse_args()

# Enable logging
if args.debug:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(message)s')


# Check if not running as root.
if os.geteuid() != 0:
    sys.exit("ERROR: Please run as root.")

# Ensure that certain commands exist.
cmdcheck = ["systemctl", "ss"]
for cmd in cmdcheck:
    if not shutil.which(cmd):
        sys.exit("\nError, ensure command {0} is installed.".format(cmd))


### Functions ###
def reset_timers():
    """Reset the initial timers"""
    global current_time
    global suspend_time
    current_time = datetime.datetime.now()
    suspend_time = current_time + datetime.timedelta(minutes=args.idletime)
def hdstats_get():
    """Retrieve disk statistics once from kernel interface."""
    # Blacklist of device terms
    dev_blacklist = ["loop", "zram"]
    # https://www.kernel.org/doc/html/latest/admin-guide/iostats.html
    # https://www.kernel.org/doc/html/latest/block/stat.html
    # Read the iostats from the kernel.
    diskstats = open('/proc/diskstats', 'r').read()
    diskstats_array = []
    for l in diskstats.splitlines():
        diskstats_parts = l.split()
        # Exclude devices listed in the blacklist.
        if not any(dev_item in diskstats_parts[2] for dev_item in dev_blacklist):
            # Save the read and write completion stats. Sector reads is field 3 after the device name and sector writes are field 8. Convert the reads and writes to kilobytes, assuming 512 byte sector size according to kernel docs. Therefore convert to kb by dividing by 2.
            diskstats_array.append([int(int(diskstats_parts[5]) / 2), int(int(diskstats_parts[10]) / 2)])
    # Sum the stats for all devices.
    diskstats_readkb_total = 0
    diskstats_writekb_total = 0
    for i in diskstats_array:
        diskstats_readkb_total += i[0]
        diskstats_writekb_total += i[1]
    diskstats_sum_current = [diskstats_readkb_total, diskstats_writekb_total]
    return diskstats_sum_current
def check_hd_used_once(throughput_threshold: float = 100.0):
    """Check if disks are being used."""
    disks_are_used = False
    diskstats_first = hdstats_get()
    time.sleep(1)
    diskstats_second = hdstats_get()
    diskstats_read_delta = diskstats_second[0] - diskstats_first[0]
    diskstats_write_delta = diskstats_second[1] - diskstats_first[1]
    logging.debug("Disk Read (kb): %s, Write: %s", diskstats_read_delta, diskstats_write_delta)
    if diskstats_read_delta >= throughput_threshold or \
       diskstats_write_delta >= throughput_threshold:
        disks_are_used = True
    return disks_are_used
def check_hd_used_multiple(num_times: int = 5):
    """Check multiple times if disks are being used. This is cheap substitute for averaging."""
    disks_are_used = False
    disk_used_numtrue = 0
    # Loop through the list
    for _ in range(0, num_times):
        # Add one to the counter if it was used.
        if check_hd_used_once(args.diskthreshold) is True:
            disk_used_numtrue += 1
    logging.debug("Disk Checks Idle: %s, Total: %s", disk_used_numtrue, num_times)
    # If the disk was used more than half the times checked, it was in use.
    if disk_used_numtrue >= (num_times / 2):
        disks_are_used = True
    return disks_are_used
def check_idle():
    """Check if network services are not being used."""
    status = False
    statuses = {}
    inhibit_string = ""
    # Check samba status. Note that sport only considers connections to this machine, while dport would consider this machine connecting to another server.
    samba_ss_output = subprocess.check_output("ss -Htua -o state established '( sport = :microsoft-ds )'", shell=True)
    statuses['samba'] = bool(samba_ss_output.decode() != "")
    # Check nfs status.
    nfs_ss_output = subprocess.check_output("ss -Htua -o state established '( sport = :nfs )'", shell=True)
    statuses['nfs'] = bool(nfs_ss_output.decode() != "")
    # Check libvirt status. Inhibit suspend if any VM is running.
    statuses['libvirt'] = False
    libvirt_lines = 0
    if shutil.which("virsh"):
        libvirt_lines = int(subprocess.check_output("virsh list --state-running --name | wc -l", shell=True))
    # Libvirt outputs 1 line if no VMs are running. Will output 2 or more if VMs are running.
    if libvirt_lines >= 2:
        statuses['libvirt'] = True
    # Check if packer is running
    if subprocess.run("pgrep packer", shell=True, check=False, stdout=subprocess.DEVNULL).returncode == 0:
        statuses['packer'] = True
    else:
        statuses['packer'] = False
    # HD Idle time
    if check_hd_used_multiple():
        statuses['hdidle'] = True
    else:
        statuses['hdidle'] = False
    # Build log string
    for item in statuses:
        inhibit_string += "{0}: {1} ".format(item, statuses[item])
    logging.info(inhibit_string)
    # Loop through all statuses for general status. The any() function will use the true if branch if any option is true. In this case, if any of the statuses is True, set the general status to true.
    if any(statuses[st] is True for st in statuses):
        status = True
    return status


# Global variables
current_time_saved = datetime.datetime.now()
loop_delay_seconds = 30

### Begin Code ###
logging.info("Script Started")
reset_timers()
while True:
    current_time = datetime.datetime.now()
    # If the current timer has elapsed more than 3 times the loop timer, then forcibly reset the timers. This means that the script was not counting, perhaps due to an external sleep event.
    current_time_diff = (current_time - current_time_saved).total_seconds() / 60
    logging.debug("Current Time vs Saved Time diff: %s seconds", round(current_time_diff, 2))
    if current_time_diff >= (3 * loop_delay_seconds):
        reset_timers()
    # Check if services are being used. If services are being used, reset the suspend timer.
    if check_idle() is True:
        reset_timers()
    logging.info("Minutes until suspend: %s", round(((suspend_time - current_time).total_seconds() / 60), 2))
    # Suspend if the current time exceeds the suspend time.
    if current_time >= suspend_time:
        # Log the time before suspending.
        current_time_beforesuspend = datetime.datetime.now()
        while True:
            # Check if the system resumed too quickly. If the current time is within 90 seconds of sleeping, then the system came out of suspend too quickly.
            current_time_aftersuspend = datetime.datetime.now()
            if (current_time_aftersuspend - current_time_beforesuspend).total_seconds() < 90:
                logging.info("Suspending.")
                # Suspend the system.
                subprocess.run("systemctl start systemd-suspend.service", shell=True, check=True)
                time.sleep(10)
            else:
                # Escape this loop after 90 seconds, in case of continued suspending.
                break
        # Sleep until the suspend cycle is finished.
        time.sleep(20)
        # If a suspend occurs, reset the timers to the startup values, and begin counting down again.
        reset_timers()
        logging.info("Came out of suspend.")
    # Wait before checking the services again. Wait the specified time minus the amount of time the loop took to run.
    current_time_saved = datetime.datetime.now()
    time.sleep(loop_delay_seconds - (current_time_saved - current_time).total_seconds())

logging.info("Script Exited")
