#!/usr/bin/env python3
"""Install CoreOS"""

# Python includes.
import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
# Custom includes
import CFunc
import Pkvm

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]
# Temporary folder
temp_folder = os.path.join(tempfile.gettempdir(), "fcos")


########################## Functions ##########################
def cosinstaller_run(cmd=list):
    """Run coreos-installer."""
    if shutil.which("coreos-installer"):
        subprocess.run(["coreos-installer"] + cmd, check=True)
    else:
        ci_podman_list = ["podman", "run", "--pull=always", "--rm", "--tty", "--interactive", "--security-opt", "label=disable", "--volume", "{0}:{0}".format(SCRIPTDIR), "--volume", f"{temp_folder}:{temp_folder}"]
        if vmpath != SCRIPTDIR:
            ci_podman_list += ["--volume", "{0}:{0}".format(vmpath)]
        if args.drive:
            ci_podman_list += ["--privileged", "--volume", "/dev:/dev", "--volume", "/run/udev:/run/udev"]
        ci_podman_list += ["--workdir", SCRIPTDIR, "quay.io/coreos/coreos-installer:release"]
        subprocess.run(ci_podman_list + cmd, check=True)

def ignitionvalidate_run(cmd=list):
    """Run ignition-validate."""
    if shutil.which("ignition-validate"):
        subprocess.run(["ignition-validate"] + cmd, check=True)
    else:
        iv_podman_list = ["podman", "run", "--pull=always", "--rm", "--tty", "--interactive", "--security-opt", "label=disable", "--volume", "{0}:{0}".format(SCRIPTDIR), "--volume", f"{temp_folder}:{temp_folder}"]
        if vmpath != SCRIPTDIR:
            iv_podman_list += ["--volume", "{0}:{0}".format(vmpath)]
        iv_podman_list += ["--workdir", SCRIPTDIR, "quay.io/coreos/ignition-validate:release"]
        subprocess.run(iv_podman_list + cmd, check=True)

def fcct_run(cmd=list):
    """Run fcct."""
    if shutil.which("fcct"):
        subprocess.run(["fcct"] + cmd, check=True)
    else:
        fcct_podman_list = ["podman", "run", "--pull=always", "--rm", "--tty", "--interactive", "--security-opt", "label=disable", "--volume", "{0}:/{0}".format(SCRIPTDIR), "--volume", f"{temp_folder}:{temp_folder}"]
        if vmpath != SCRIPTDIR:
            fcct_podman_list += ["--volume", "{0}:{0}".format(vmpath)]
        fcct_podman_list += ["--workdir", SCRIPTDIR, "quay.io/coreos/fcct:release"]
        subprocess.run(fcct_podman_list + cmd, check=True)


# Get arguments
parser = argparse.ArgumentParser(description='Install CoreOS.')
parser.add_argument("-v", "--vm", help='Install to libvirt VM.', action="store_true")
parser.add_argument("-p", "--imagepath", help='Path to store libvirt images.')
parser.add_argument("-d", "--drive", help='Install bare-metal to block device (i.e. /dev/sdX). Mutually exclusive with vm option.')
parser.add_argument("-s", "--hostname", help='Specify hostname. (default: %(default)s)', default="CoreOS")
parser.add_argument("-f", "--fullname", help="Full Name", default="User Name")
parser.add_argument("-x", "--sshkey", help="SSH Key")
parser.add_argument("-y", "--username", help="VM Username", default="user")
parser.add_argument("-z", "--password", help="VM Password", default="asdf")
parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
args = parser.parse_args()

# Process variables
if (args.vm and args.drive) or (not args.vm and not args.drive):
    sys.exit("ERROR: Only vm OR drive can be specified, not both or neither.")
vmpath = None
if args.vm:
    if args.imagepath and os.path.isdir(args.imagepath):
        vmpath = os.path.abspath(args.imagepath)
    else:
        vmpath = os.path.join(CFunc.storage_path_detect(), "VMs")
    print("Installing to VM. Image path: {0}".format(vmpath))
if args.drive:
    if os.path.exists(args.drive) is True and stat.S_ISBLK(os.stat(args.drive).st_mode) is True:
        print("Installing to {0}.".format(args.drive))
        subprocess.run("lsblk -o MODEL {0}".format(args.drive), shell=True, check=True)
        subprocess.run("lsblk {0}".format(args.drive), shell=True, check=True)
        print("WARNING: Ensure that {0} is the correct block device, it will be erased.")
    else:
        sys.exit("ERROR: {0} is not a block device. Exiting.")
if args.sshkey:
    ssh_key = args.sshkey
else:
    ssh_key = Pkvm.sshkey_detect()
print(f"""Hostname: {args.hostname}
VM Username: {args.username}
VM Password: {args.password}
sshkey: {ssh_key}
fullname: {args.fullname}
""")

######################### Begin Code ##########################

# Make temp folder
os.makedirs(temp_folder, exist_ok=True)
# Replace hostname in yaml.
ignition_yaml_stockfile = os.path.join(SCRIPTDIR, "unattend", "fedora-coreos.yaml")
ignition_yaml_modified = os.path.join(temp_folder, "fcos-gen.yaml")
with open(ignition_yaml_stockfile, 'r') as f:
    ignition_yaml_data = f.read()
# Replace the hostname
ignition_yaml_data = ignition_yaml_data.replace('INSERTHOSTNAMENAMEHERE', args.hostname)
ignition_yaml_data = ignition_yaml_data.replace('INSERTUSERHERE', args.username)
ignition_yaml_data = ignition_yaml_data.replace('INSERTPASSWORDHERE', args.password)
pw_output = subprocess.run(['mkpasswd', '-s', '--method=yescrypt'], stdout=subprocess.PIPE, universal_newlines=True, check=True, input=args.password).stdout.strip()
ignition_yaml_data = ignition_yaml_data.replace('INSERTHASHEDPASSWORDHERE', pw_output)
ignition_yaml_data = ignition_yaml_data.replace('INSERTSSHKEYHERE', ssh_key)
# Write to the new file.
with open(ignition_yaml_modified, 'w') as f:
    f.write(ignition_yaml_data)

# Generate ignition file.
ignition_generated_file = os.path.join(temp_folder, "fcos.ign")
fcct_run(['--pretty', '--strict', ignition_yaml_modified, '--output', ignition_generated_file])

# Validate ignition file.
ignitionvalidate_run([ignition_generated_file])

if args.noprompt is False:
    input("Press Enter to continue.")

### Create VM ###
if args.vm and vmpath:
    qcow2_baseimage = os.path.join(vmpath, "CoreOS_BaseImage.qcow2")
    qcow2_deltaimage = os.path.join(vmpath, "{0}.qcow2".format(args.hostname))
    vmname = args.hostname

    # Remove the libvirt entry if it already exists.
    kvmlist = subprocess.run("virsh --connect qemu:///system -q list --all", shell=True, stdout=subprocess.PIPE, universal_newlines=True, check=True).stdout.strip()
    if vmname.lower() in kvmlist.lower():
        subprocess.run('virsh --connect qemu:///system destroy "{0}"'.format(vmname), shell=True, check=False)
        subprocess.run('virsh --connect qemu:///system undefine --snapshots-metadata --nvram "{0}"'.format(vmname), shell=True, check=True)

    # Get the Base image.
    if not os.path.isfile(qcow2_baseimage):
        cosinstaller_run(["download", "--platform", "qemu", "--format", "qcow2.xz", "--decompress", "--directory", vmpath])
        # Find the name of the image.
        qcow2_baseimage_originaldl = None
        for root, dirs, files in os.walk(vmpath):
            for file in files:
                absfilepath = os.path.join(root, file)
                if file.startswith("fedora-coreos-"):
                    qcow2_baseimage_originaldl = absfilepath
                    break
        # Rename the image.
        os.rename(qcow2_baseimage_originaldl, qcow2_baseimage)

    # Remove the original Delta image.
    if os.path.isfile(qcow2_deltaimage):
        os.remove(qcow2_deltaimage)

    # Create the virtual machine.
    subprocess.run(['virt-install', '--connect', 'qemu:///system', '--name={0}'.format(vmname), '--disk', 'size=60,backing_store={0},bus=virtio,path={1}'.format(qcow2_baseimage, qcow2_deltaimage), '--graphics', 'spice', '--vcpu=4', '--ram=4096', '--network', 'bridge=virbr0,model=virtio', '--filesystem', 'source=/,target=root,mode=mapped', '--os-variant=fedora-coreos-stable', '--import', '--noautoconsole', '--video=virtio', '--channel', 'unix,target_type=virtio,name=org.qemu.guest_agent.0', '--channel', 'spicevmc,target_type=virtio,name=com.redhat.spice.0', '--qemu-commandline="-fw_cfg"', '--qemu-commandline="name=opt/com.coreos/config,file={0}"'.format(ignition_generated_file)], check=True)

### Install on Bare Metal ###
if args.drive:
    subprocess.run("lsblk -o MODEL {0}".format(args.drive), shell=True, check=True)
    subprocess.run("lsblk {0}".format(args.drive), shell=True, check=True)
    print("WARNING, Confirm that the correct block device has been chosen.")
    input("Press Enter to continue.")
    # Install to block device.
    cosinstaller_run(["install", args.drive, "-i", ignition_generated_file])
