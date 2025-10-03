#!/usr/bin/env python3
"""Create a VM from a chroot environment."""

# Python includes.
import argparse
import datetime
import functools
import ipaddress
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
# Custom includes
import CFunc
import Pkvm
import Snetvm

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Folder of this script
SCRIPTDIR = os.path.abspath(os.path.dirname(__file__))

### Functions ###
def vm_getip(vmname: str):
    """Get IP address of Virtual Machine."""
    ip = None
    while ip is None:
        # Note: domifaddr does not always work. Use domiflist to get mac address and then look up ip using "ip neighbor" command.
        # Check for a valid IP address.
        try:
            ip = Snetvm.libvirt_ipv4(vmname)
            # Test if it is an IPv4 or IPv6 address.
            ipaddress.ip_address(address=ip)
            # For now, enforce ipv4, since can't connect to ssh in ipv6 address.
            if not isinstance(ipaddress.ip_address(ip), ipaddress.IPv4Address):
                raise Exception()
            logging.debug('%s is a correct IP address.', ip)
            return ip
        except:
            logging.debug('Address/Netmask is invalid: %s', ip)
            ip = None
        time.sleep(1)
    return ip
def vm_getimgpath(vmname: str, folder_path: str):
    """Get the hypothetical full path of a VM image."""
    imgfile_fullpath = os.path.abspath(os.path.join(folder_path, "{0}.qcow2".format(vmname)))
    return imgfile_fullpath
def vm_createimage(img_path: str, size_gb: int):
    """Create a VM image file."""
    subprocess.run("qemu-img create -f qcow2 -o compression_type=zstd,compat=1.1,lazy_refcounts=on '{0}' {1}G".format(img_path, size_gb), shell=True, check=True)
def vm_create(vmname: str, img_path: str, isopath: str, memory: int):
    """Create the VM in libvirt."""
    # Copy efi firmware (ensure non-secureboot firmware is chosen)
    efi_bin, efi_nvram = Pkvm.ovmf_bin_nvramcopy(os.path.dirname(img_path), vmname, secureboot=False)
    # virt-install manual: https://www.mankier.com/1/virt-install
    # List of os: osinfo-query os
    CREATESCRIPT_KVM = Pkvm.cmd_virtinstall(vmname=vmname, diskpath=os.path.join(vmpath, vmname), variant=kvm_variant, efi_bin=efi_bin, efi_nvram=efi_nvram, memory=memory, cdrom_path=isopath)
    subprocess.run(CREATESCRIPT_KVM, shell=True, check=True)
    # Log the launch command.
    logging.info(f"""KVM launch command: {Pkvm.cmd_virtinstall(vmname=vmname, diskpath=os.path.join(vmpath, vmname), variant=kvm_variant, efi_bin=efi_bin, efi_nvram=efi_nvram, memory=args.memory)}""")
def vm_ejectiso(vmname: str):
    """Eject an iso from a VM."""
    subprocess.run("virsh --connect qemu:///system change-media {0} sda --eject --config".format(vmname), shell=True, check=False)
def ssh_vm(ip: str, command: str, ssh_opts: str = "", port: int = 22, user: str = "root", password: str = "asdf"):
    """SSH into the Virtual Machine and run a command."""
    status = CFunc.subpout_logger("""sshpass -p "{password}" ssh {ssh_opts} {ip} -p {port} -l {user} '{command}'""".format(password=password, ip=ip, port=port, user=user, command=command, ssh_opts=ssh_opts))
    return status
def scp_vm(ip: str, filepath: str, destination: str, port: int = 22, user: str = "root", password: str = "asdf", folder: bool = False):
    """Copy files into the Virtual Machine."""
    scp_opts = ""
    if folder is True:
        scp_opts += "-r"
    status = CFunc.subpout_logger("""sshpass -p "{password}" scp -P {port} {opts} "{filepath}" {user}@{ip}:{destination}""".format(password=password, ip=ip, port=port, user=user, filepath=filepath, destination=destination, opts=scp_opts))
    return status
def ssh_wait(ip: str, port: int = 22, user: str = "root", password: str = "asdf", retries: int = 10000):
    """Wait for ssh to connect successfully to the VM."""
    logging.info("Waiting for VM to boot.")
    status = 1
    attempt = 0
    # Run ssh in quiet mode.
    while status != 0 and attempt < retries:
        logging.debug("SSH status was %s, attempt %s, waiting.", status, attempt)
        time.sleep(5)
        status = ssh_vm(ip=ip, port=port, user=user, password=password, command="echo Connected", ssh_opts="-q")
        attempt += 1
    if status != 0:
        logging.info("ERROR: ssh_wait could not connect.")
    return status
def vm_check_onoff(vmname: str):
    """Check if a VM is started or not. Return True if VM is on."""
    status = subprocess.run('virsh --connect qemu:///system -q list | grep -i "{0}"'.format(vmname), shell=True, check=False, stdout=subprocess.DEVNULL).returncode
    return bool(status == 0)
def vm_start(vmname: str):
    """Start the VM."""
    if not vm_check_onoff(vmname=vmname):
        # Start the VM
        logging.info("Starting VM %s", vmname)
        subprocess.run("virsh --connect qemu:///system start {0}".format(vmname), shell=True, check=True)
        time.sleep(5)
def vm_shutdown(vmname: str, timeout_seconds: int = 30):
    """Shutdown the VM. Timeout in minutes."""
    logging.info("Shutting down VM %s", vmname)
    vm_is_on = vm_check_onoff(vmname=vmname)
    # Issue a shutdown if the VM is on.
    if vm_is_on:
        subprocess.run("virsh --connect qemu:///system shutdown {0}".format(vmname), shell=True, check=True, stdout=subprocess.DEVNULL)
        # Save time variables.
        current_time_saved = datetime.datetime.now()
        current_time_diff = 0
        # Check if VM is shutdown every 5 seconds.
        while vm_is_on and current_time_diff < timeout_seconds:
            time.sleep(5)
            vm_is_on = vm_check_onoff(vmname=vmname)
            current_time_diff = (datetime.datetime.now() - current_time_saved).total_seconds()
        # If after timeout is exceeded, force off the VM.
        if vm_is_on and current_time_diff >= timeout_seconds:
            logging.debug("Force Shutting down VM %s", vmname)
            subprocess.run("virsh --connect qemu:///system destroy {0}".format(vmname), shell=True, check=True, stdout=subprocess.DEVNULL)
def vm_cleanup(vmname: str, img_path: str):
    """Cleanup existing VM."""
    # Destroy and undefine the VM.
    vm_shutdown(vmname)
    subprocess.run("virsh --connect qemu:///system undefine --snapshots-metadata --nvram {0}".format(vmname), shell=True, check=False)
    # Delete the image file.
    if os.path.isfile(img_path):
        os.remove(img_path)
def vm_runscript(ip: str, script: str, port: int = 22, user: str = "root", password: str = "asdf"):
    """Run a script (passed as a variable) on a VM."""
    # Write the script to a file.
    tempfolder = tempfile.gettempdir()
    tempscript_path = os.path.join(tempfolder, "tempscript")
    with open(tempscript_path, 'w') as f:
        f.write(script)
    # Make the file executable.
    os.chmod(tempscript_path, 0o777)
    # SCP the file to the host.
    scp_vm(ip=ip, filepath=tempscript_path, destination=f"{tempfolder}/", port=port, user=user, password=password, folder=False)
    # Run the file in the VM.
    ssh_vm(ip=ip, command=f"bash {tempscript_path}", port=port, user=user, password=password)
    # Remove the file from host and guest.
    if os.path.isfile(tempscript_path):
        os.remove(tempscript_path)
    ssh_vm(ip=ip, command=f"rm {tempscript_path}", port=port, user=user, password=password)
def git_branch_retrieve():
    """Retrieve the current branch of this script's git repo."""
    git_branch = None
    if shutil.which("git"):
        original_working_folder = os.getcwd()
        os.chdir(SCRIPTDIR)
        git_branch = CFunc.subpout("git rev-parse --abbrev-ref HEAD")
        os.chdir(original_working_folder)
    else:
        git_branch = "master"
    return git_branch
def git_cmdline(destination=os.path.join(os.sep, "opt", "CustomScripts")):
    """Compose the git command line to check out the repo."""
    git_branch = git_branch_retrieve()
    git_cmd = "git clone https://github.com/ramesh45345/CustomScripts {0} -b {1}".format(destination, git_branch)
    return git_cmd


if __name__ == '__main__':
    print("Running {0}".format(__file__))

    # Exit if root.
    CFunc.is_root(False)

    # Get non-root user information.
    USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
    imgsize_default = "100"

    # Ensure that certain commands exist.
    CFunc.commands_check(["ssh", "sshpass", "qemu-img", "virsh", "ip"])

    # Get arguments
    parser = argparse.ArgumentParser(description='Create and run a Virtual Machine.')
    parser.add_argument("-a", "--ostype", type=int, help="OS type (1=Arch. 2=NixOS, 3=Ubuntu, 4=Debian, 5=Opensuse)", default="1")
    parser.add_argument("-c", "--nixconfig", help="Path of folder configuration for nix")
    parser.add_argument("-e", "--desktopenv", help="Desktop Environment (default: %(default)s)", default="gnome")
    parser.add_argument("-f", "--fullname", help="Full Name", default="User Name")
    parser.add_argument("-g", "--debversion", help="Ubuntu/Debian version to install.")
    parser.add_argument("-i", "--iso", help="Path to live cd", required=True)
    parser.add_argument("-n", "--vmname", help="Name of Virtual Machine")
    parser.add_argument("-p", "--vmpath", help="Path of Virtual Machine folders", required=True)
    parser.add_argument("-s", "--imgsize", type=int, help="Size of image in GB (default: %(default)s)", default=imgsize_default)
    parser.add_argument("-v", "--rootsshkey", help="Root SSH Key")
    parser.add_argument("--vmprovision", help="""Override provision options. Enclose options in double backslashes and quotes. Example: \\\\"-n -e 3\\\\" """, default=None)
    parser.add_argument("-w", "--livesshuser", help="Live SSH Username", default="root")
    parser.add_argument("-x", "--livesshpass", help="Live SSH Password", default="asdf")
    parser.add_argument("-y", "--vmuser", help="VM Username", default="user")
    parser.add_argument("-z", "--vmpass", help="VM Password", default="asdf")
    parser.add_argument("-m", "--memory", help="Memory for VM (default: %(default)s)", default=Pkvm.vm_memory_range())
    parser.add_argument("--noprompt", help='Do not prompt to continue.', action="store_true")
    args = parser.parse_args()

    debversion = ""
    vm_name = "Default"
    vmprovision_cmd = "Command Not Set"
    vmbootstrap_cmd = "Command Not Set"
    # Set paths
    vmpath = os.path.abspath(args.vmpath)
    iso_path = os.path.abspath(args.iso)

    # Override provision opts if provided.
    if args.vmprovision is None:
        vmprovision_opts = f"-d {args.desktopenv}"
    else:
        vmprovision_opts = args.vmprovision

    # Detect root ssh key.
    if args.rootsshkey is not None:
        sshkey = args.rootsshkey
    else:
        sshkey = Pkvm.sshkey_detect(USERNAMEVAR)

    # Determine VM Name
    if args.ostype == 1:
        if args.vmname is not None:
            vm_name = args.vmname
        else:
            vm_name = "CC-Arch-kvm"
        # VM commands
        vmbootstrap_cmd = f"""#!/bin/bash
cd ~
export LANG=en_US.UTF-8
/opt/CustomScripts/ZSlimDrive.py -b -n -g
/opt/CustomScripts/BArch.py -n -g 3 -i /dev/vda2 -c "{vm_name}" -u {args.vmuser} -q "{args.vmpass}" -f "{args.fullname}" /mnt
echo "PermitRootLogin yes" >> /mnt/etc/ssh/sshd_config && poweroff"""
        vmprovision_cmd = f"""#!/bin/bash
mkdir -m 700 -p /root/.ssh; echo '{sshkey}' > /root/.ssh/authorized_keys
mkdir -m 700 -p ~{args.vmuser}/.ssh; echo '{sshkey}' > ~{args.vmuser}/.ssh/authorized_keys
chown {args.vmuser}:users -R ~{args.vmuser}
/opt/CustomScripts/MArch.py {vmprovision_opts}"""
        kvm_variant = "archlinux"
    if args.ostype == 2:
        if args.vmname is not None:
            vm_name = args.vmname
        else:
            vm_name = "CC-NixOS-kvm"
        if not os.path.isdir(args.nixconfig):
            print("ERROR: nixconfig {0} must be a folder.".format(args.nixconfig))
            sys.exit()
        # VM commands
        vmbootstrap_cmd = f'''#!/bin/bash
cd ~
disko --mode destroy,format,mount /nixos_config/modules/disko/ext4-single.nix --yes-wipe-all-disks --arg disks "[ \\"/dev/vda\\" ]" && mkdir -p /mnt/etc
mv /nixos_config /mnt/etc/nixos
sed -i 's/qemu-nixos/{vm_name}/g' /mnt/etc/nixos/flake.nix /mnt/etc/nixos/machines/qemu/configuration.nix
nix-channel --update
nixos-install --flake /mnt/etc/nixos#{vm_name} && poweroff'''
        vmprovision_cmd = """#!/bin/bash
mkdir -m 700 -p /root/.ssh
echo '{sshkey}' > /root/.ssh/authorized_keys
export UNVAR=$(id -un 1000)
mkdir -m 700 -p ~$UNVAR/.ssh
echo '{sshkey}' > ~$UNVAR/.ssh/authorized_keys
chown $UNVAR:users -R ~$UNVAR
while ! test -f /var/opt/CustomScripts/MNixOS.py; do sleep 1; done;
/var/opt/CustomScripts/MNixOS.py""".format(sshkey=sshkey)
        kvm_variant = "nixos-unstable"
    if args.ostype == 3:
        if args.vmname is not None:
            vm_name = args.vmname
        else:
            vm_name = "CC-Ubuntu-kvm"
        if args.debversion is not None:
            debversion = args.debversion
        else:
            debversion = "noble"
        # VM commands
        vmbootstrap_cmd = f"""#!/bin/bash
cd ~
export LANG=en_US.UTF-8
/opt/CustomScripts/ZSlimDrive.py -n -g
/opt/CustomScripts/BDebian.py -n -z -t ubuntu -r {debversion} -g 3 -i /dev/vda2 -c "{vm_name}" -u {args.vmuser} -q "{args.vmpass}" -f "{args.fullname}" --forcelink /mnt
echo "PermitRootLogin yes" >> /mnt/etc/ssh/sshd_config
poweroff"""
        vmprovision_cmd = f"""#!/bin/bash
mkdir -m 700 -p /root/.ssh; echo '{sshkey}' > /root/.ssh/authorized_keys
mkdir -m 700 -p ~{args.vmuser}/.ssh; echo '{sshkey}' > ~{args.vmuser}/.ssh/authorized_keys
chown {args.vmuser}:users -R ~{args.vmuser}
rm -f /etc/resolv.conf
echo -e "nameserver 1.0.0.1\\nnameserver 1.1.1.1\\nnameserver 2606:4700:4700::1111\\nnameserver 2606:4700:4700::1001" > /etc/resolv.conf
/opt/CustomScripts/MUbuntu.py {vmprovision_opts}"""
        kvm_variant = "ubuntu22.04"
    if args.ostype == 4:
        if args.vmname is not None:
            vm_name = args.vmname
        else:
            vm_name = "CC-Debian-kvm"
        if args.debversion is not None:
            debversion = args.debversion
        else:
            debversion = "unstable"
        # VM commands
        vmbootstrap_cmd = f'''#!/bin/bash
cd ~
export LANG=en_US.UTF-8
/opt/CustomScripts/ZSlimDrive.py -n -g
/opt/CustomScripts/BDebian.py -n -z -t debian -r {debversion} -g 3 -i /dev/vda2 -c "{vm_name}" -u {args.vmuser} -q "{args.vmpass}" -f "{args.fullname}" /mnt
echo "PermitRootLogin yes" >> /mnt/etc/ssh/sshd_config
poweroff'''
        vmprovision_cmd = f"""#!/bin/bash
mkdir -m 700 -p /root/.ssh
echo '{sshkey}' > /root/.ssh/authorized_keys
mkdir -m 700 -p ~{args.vmuser}/.ssh
echo '{sshkey}' > ~{args.vmuser}/.ssh/authorized_keys
chown {args.vmuser}:users -R ~{args.vmuser}
rm -f /etc/resolv.conf
echo -e "nameserver 1.0.0.1\\nnameserver 1.1.1.1\\nnameserver 2606:4700:4700::1111\\nnameserver 2606:4700:4700::1001" > /etc/resolv.conf
/opt/CustomScripts/MDebian.py {vmprovision_opts}"""
        kvm_variant = "debiantesting"
    if args.ostype == 5:
        if args.vmname is not None:
            vm_name = args.vmname
        else:
            vm_name = "CC-OpenSuse-kvm"
        # VM commands
        vmbootstrap_cmd = f'''#!/bin/bash
cd ~
export LANG=en_US.UTF-8
/opt/CustomScripts/ZSlimDrive.py -n -g
/opt/CustomScripts/BOpensuse.py -n -g 3 -i /dev/vda2 -c "{vm_name}" -u {args.vmuser} -q "{args.vmpass}" -f "{args.fullname}" /mnt
echo "PermitRootLogin yes" >> /mnt/etc/ssh/sshd_config
poweroff'''
        vmprovision_cmd = f"""#!/bin/bash
mkdir -m 700 -p /root/.ssh
echo '{sshkey}' > /root/.ssh/authorized_keys
mkdir -m 700 -p ~{args.vmuser}/.ssh
echo '{sshkey}' > ~{args.vmuser}/.ssh/authorized_keys
chown {args.vmuser}:users -R ~{args.vmuser}
/opt/CustomScripts/MOpensuse.py {vmprovision_opts}"""
        kvm_variant = "opensusetumbleweed"

    # Override VM Name if provided
    print("VM Name is {0}".format(vm_name))
    print("Path to LiveCD/ISO is {0}".format(iso_path))
    print("OS Type is {0}".format(args.ostype))
    print("VM Memory is {0}".format(args.memory))
    print("VM Disk size is {0} GB".format(args.imgsize))
    print("Live SSH user is {0}".format(args.livesshuser))
    print("VM User is {0}".format(args.vmuser))
    print("SSH Key is \"{0}\"".format(sshkey))
    print("VM Provision Options:", vmprovision_opts)
    if debversion != "":
        print(f"Debian/Ubuntu Release: {debversion}")

    # Variables less likely to change.
    sship = None
    localsshport = 22

    if not os.path.isdir(vmpath) or not os.path.isfile(iso_path):
        sys.exit("\nError, ensure {0} is a folder, and {1} is a file.".format(vmpath, iso_path))

    if args.noprompt is False:
        input("Press Enter to continue.")

    ### Begin Code ###

    # Save start time.
    beforetime = datetime.datetime.now()
    # Initiate logger
    buildlog_path = os.path.join(vmpath, "{0}.log".format(vm_name))
    CFunc.log_config(buildlog_path)

    # Run this if we are destroying (not keeping) the VM.
    imgpath = vm_getimgpath(vm_name, vmpath)
    vm_cleanup(vm_name, imgpath)

    # Create new VM.
    print("\nCreating VM.")
    vm_createimage(imgpath, args.imgsize)
    vm_create(vm_name, imgpath, iso_path, memory=args.memory)
    # Bootstrap the VM.
    vm_start(vm_name)
    sship = vm_getip(vm_name)
    ssh_wait(ip=sship, port=localsshport, user=args.livesshuser, password=args.livesshpass)
    # Pre-bootstrap commands
    if args.ostype == 2:
        scp_vm(ip=sship, port=localsshport, user=args.livesshuser, password=args.livesshpass, filepath=args.nixconfig, destination="/nixos_config", folder=True)
        scp_vm(ip=sship, port=localsshport, user=args.livesshuser, password=args.livesshpass, filepath=SCRIPTDIR, destination="/CustomScripts", folder=True)
    # All else besides nixos, sync the CustomScripts folder into the live environment.
    else:
        scp_vm(ip=sship, port=localsshport, user=args.livesshuser, password=args.livesshpass, filepath=SCRIPTDIR, destination="/opt/", folder=True)
    # Bootstrap
    vm_runscript(ip=sship, port=localsshport, user=args.livesshuser, password=args.livesshpass, script=vmbootstrap_cmd)
    vm_shutdown(vm_name)
    # Eject cdrom
    vm_ejectiso(vm_name)
    time.sleep(5)
    # Provision the VM.
    vm_start(vm_name)
    sship = vm_getip(vm_name)
    ssh_wait(ip=sship, port=localsshport, user="root", password=args.vmpass)
    # Pre-provision commands
    if args.ostype == 2:
        scp_vm(ip=sship, port=localsshport, user="root", password=args.vmpass, filepath=SCRIPTDIR, destination="/var/opt/", folder=True)
    else:
        scp_vm(ip=sship, port=localsshport, user="root", password=args.vmpass, filepath=SCRIPTDIR, destination="/opt/", folder=True)
    # Provision VM
    vm_runscript(ip=sship, port=localsshport, user="root", password=args.vmpass, script=vmprovision_cmd)
    vm_shutdown(vm_name)
    # Save finish time.
    fullfinishtime = datetime.datetime.now()
    logging.info("Creation completed in {0}".format(str(fullfinishtime - beforetime)))
