#!/usr/bin/env python3

# Python includes.
import argparse
import grp
import ipaddress
import hashlib
import json
import multiprocessing
import os
import pwd
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR=sys.path[0]

# Exit if root.
# if os.geteuid() == 0:
#     sys.exit("\nError: Please run this script as a normal (non root) user.\n")

# Get non-root user information.
if os.getenv("SUDO_USER") != None and os.getenv("SUDO_USER") != "root":
    USERNAMEVAR=os.getenv("SUDO_USER")
elif os.getenv("USER") != "root":
    USERNAMEVAR=os.getenv("USER")
else:
    # https://docs.python.org/3/library/pwd.html
    USERNAMEVAR=pwd.getpwuid(1000)[0]
# https://docs.python.org/3/library/grp.html
USERGROUP=grp.getgrgid(pwd.getpwnam(USERNAMEVAR)[3])[0]
USERHOME=os.path.expanduser("~")
CPUCORES=multiprocessing.cpu_count() if multiprocessing.cpu_count() <= 4 else 4

# Ensure that certain commands exist.
cmdcheck = ["packer", "ssh"]
for cmd in cmdcheck:
    if not shutil.which(cmd):
        sys.exit("\nError, ensure command {0} is installed.".format(cmd))

# Get arguments
parser = argparse.ArgumentParser(description='Create a VM using packer.')
parser.add_argument("-n", "--noprompt",help='Do not prompt to continue.', action="store_true")
parser.add_argument("-t", "--vmtype", type=int, help="Virtual Machine type (1=Virtualbox, 2=libvirt, 3=VMWare)", default="1")
parser.add_argument("-a", "--ostype", type=int, help="OS type (1=Ubuntu, 2=Fedora, 3=opensuse)", default="1")
parser.add_argument("-f", "--fullname", help="Full Name", default="User Name")
parser.add_argument("-i", "--iso", help="Path to live cd")
parser.add_argument("-s", "--imgsize", type=int, help="Size of image", default=65536)
parser.add_argument("-p", "--vmpath", help="Path of Packer output", required=True)
parser.add_argument("-y", "--vmuser", help="VM Username", default="user")
parser.add_argument("-z", "--vmpass", help="VM Password", default="asdf")
parser.add_argument("--memory", help="Memory for VM", default="2048")
parser.add_argument("--vmprovision", help="Override provision options.")

# Save arguments.
args = parser.parse_args()

# Variables most likely to change.
vmpath = os.path.abspath(args.vmpath)
print("Path to Packer output is {0}".format(vmpath))
print("OS Type is {0}".format(args.ostype))
print("VM Memory is {0}".format(args.memory))
print("VM User is {0}".format(args.vmuser))

# Determine VM hypervisor
if args.vmtype == 1:
    hvname = "vbox"
elif args.vmtype == 2:
    hvname = "kvm"
elif args.vmtype == 3:
    hvname = "vmware"

# Set OS options.
if args.ostype == 1:
    vmname = "Packer-CentosTest-{0}".format(hvname)
    vboxosid = "Fedora_64"
    vmprovisionscript = "MFedora.sh"
    vmprovision_defopts = "-n -s {0}".format(args.vmpass)
    kvm_variant = "fedora24"
    isourl = "http://mirrors.kernel.org/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1511.iso"
elif args.ostype == 2:
    vmname = "Packer-FedoraTest-{0}".format(hvname)
    vboxosid = "Fedora_64"
    vmprovisionscript = "MFedora.sh"
    vmprovision_defopts = "-n -s {0}".format(args.vmpass)
    kvm_variant = "fedora24"
    isourl = "https://download.fedoraproject.org/pub/fedora/linux/releases/25/Server/x86_64/iso/Fedora-Server-dvd-x86_64-25-1.3.iso"
if args.ostype == 10:
    vmname = "Packer-UbuntuTest-{0}".format(hvname)
    vboxosid = "Ubuntu_64"
    vmprovisionscript = "MDebUbu.sh"
    vmprovision_defopts = "-n -e 3 -s {0}".format(args.vmpass)
    kvm_variant = "ubuntu16.04"
    isourl = "http://releases.ubuntu.com/16.10/ubuntu-16.10-server-amd64.iso"
elif args.ostype == 50:
    vmname = "Packer-Windows10-{0}".format(hvname)
    vboxosid = "Windows10_64"
    isourl = None
elif args.ostype == 51:
    vmname = "Packer-WindowsServer2016-{0}".format(hvname)
    vboxosid = "Windows10_64"
    isourl = None

# Override provision opts if provided.
if args.vmprovision is None:
    vmprovision_opts = vmprovision_defopts
else:
    vmprovision_opts = args.vmprovision
print("VM Provision Options:", vmprovision_opts)

print("VM Name is {0}".format(vmname))

if args.noprompt == False:
    input("Press Enter to continue.")

# Delete leftover VMs
if args.vmtype == 1:
    DELETESCRIPT="""#!/bin/bash
    if VBoxManage list vms | grep -i "{0}"; then
      VBoxManage unregistervm "{0}" --delete
    fi
    """.format(vmname)
    subprocess.run(DELETESCRIPT, shell=True)
elif args.vmtype == 2:
    print("Delete KVM image.")
elif args.vmtype == 3:
    print("Delete vmware image.")


# Check iso
if args.iso is not None:
    isopath = os.path.abspath(args.iso)
else:
    print("Retrieving ISO")
    # Get the filename from the URL.
    fileinfo = urllib.parse.urlparse(isourl)
    filename = urllib.parse.unquote(os.path.basename(fileinfo.path))
    # Check if the file already exists.
    os.chdir(vmpath)
    isopath = vmpath+"/"+filename
    if os.path.isfile(isopath) is False:
        # Download the file if it doesn't exist.
        print("Downloading",filename,"from",isourl)
        urllib.request.urlretrieve(isourl, filename)
if os.path.isfile(isopath) is True:
    print("Path to ISO is {0}".format(isopath))
else:
    sys.exit("\nError, ensure iso {0} exists.".format(isopath))

# Create temporary folder for packer
packer_temp_folder = vmpath+"/packertemp"+vmname
if os.path.isdir(packer_temp_folder):
    print("\nDeleting old VM.")
    shutil.rmtree(packer_temp_folder)
os.mkdir(packer_temp_folder)
os.chdir(packer_temp_folder)

# Copy unattend script folder
if os.path.isdir(SCRIPTDIR+"/unattend"):
    shutil.copytree(SCRIPTDIR+"/unattend", packer_temp_folder+"/unattend")

# Get hash for iso.
print("Generating Checksum of {0}".format(isopath))
md5 = subprocess.run("md5sum {0} | awk -F' ' '{{ print $1 }}'".format(isopath), shell=True, stdout=subprocess.PIPE, universal_newlines=True)

# Create Packer json configuration
# Packer Builder Configuration
data = {}
data['builders']=['']
data['builders'][0]={}
if args.vmtype is 1:
    data['builders'][0]["type"] = "virtualbox-iso"
    data['builders'][0]["guest_os_type"] = "{0}".format(vboxosid)
    data['builders'][0]["vm_name"] = "{0}".format(vmname)
    data['builders'][0]["vboxmanage"] = ['']
    data['builders'][0]["vboxmanage"][0]= ["modifyvm", "{{.Name}}", "--memory", "{0}".format(args.memory)]
    data['builders'][0]["vboxmanage"].append(["modifyvm", "{{.Name}}", "--vram", "40"])
    data['builders'][0]["vboxmanage"].append(["modifyvm", "{{.Name}}", "--cpus", "{0}".format(CPUCORES)])
elif args.vmtype is 2:
    data['builders'][0]["type"] = "qemu"
    data['builders'][0]["accelerator"] = "kvm"
    data['builders'][0]["vm_name"] = "{0}.qcow2".format(vmname)
    data['builders'][0]["qemuargs"]=['']
    data['builders'][0]["qemuargs"][0]= ["-m", "{0}M".format(args.memory)]
    data['builders'][0]["qemuargs"].append(["--cpu", "host"])
    data['builders'][0]["qemuargs"].append(["--smp", "cores={0}".format(CPUCORES)])
elif args.vmtype is 3:
    data['builders'][0]["type"] = "vmware-iso"
    data['builders'][0]["vm_name"] = "{0}".format(vmname)
    data['builders'][0]["vmdk_name"] = "{0}".format(vmname)
    data['builders'][0]["vmx_data"] = { "memsize": "{0}".format(args.memory), "numvcpus": "{0}".format(CPUCORES), "cpuid.coresPerSocket": "{0}".format(CPUCORES) }
data['builders'][0]["shutdown_command"] = "shutdown -P now"
data['builders'][0]["iso_url"] = "file://"+isopath
data['builders'][0]["iso_checksum"] = "{0}".format(md5.stdout.strip())
data['builders'][0]["iso_checksum_type"] = "md5"
data['builders'][0]["output_directory"] = "{0}".format(vmname)
data['builders'][0]["http_directory"] = "unattend"
data['builders'][0]["disk_size"] = "{0}".format(args.imgsize)
data['builders'][0]["boot_wait"] = "5s"
data['builders'][0]["ssh_username"] = "root"
data['builders'][0]["ssh_password"] = "{0}".format(args.vmpass)
data['builders'][0]["ssh_wait_timeout"] = "90m"
data['builders'][0]["winrm_timeout"] = "90m"
data['builders'][0]["winrm_username"] = "{0}".format("vagrant")
data['builders'][0]["winrm_password"] = "{0}".format("vagrant")
# Packer Provisioning Configuration
data['provisioners']=['']
data['provisioners'][0]={}
if args.ostype is 1:
    data['builders'][0]["boot_command"] = ["<tab> text ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/centos7-ks.cfg<enter><wait>"]
    data['provisioners'][0]["type"] = "shell"
    data['provisioners'][0]["inline"] = "git clone https://github.com/vinadoros/CustomScripts /opt/CustomScripts;"
if args.ostype is 2:
    data['builders'][0]["boot_command"] = ["<tab> text ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/fedora.cfg<enter><wait>"]
    data['provisioners'][0]["type"] = "shell"
    data['provisioners'][0]["inline"] = "dnf update -y; dnf install -y git; git clone https://github.com/vinadoros/CustomScripts /opt/CustomScripts;/opt/CustomScripts/{0} {1}".format(vmprovisionscript, vmprovision_opts)
if args.ostype is 10:
    data['builders'][0]["boot_command"] = ["<enter><wait><f6><wait><esc><home>url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/ubuntu.cfg hostname=ubuntu locale=en_US keyboard-configuration/modelcode=SKIP <enter>"]
    data['provisioners'][0]["type"] = "shell"
    data['provisioners'][0]["inline"] = "apt install -y git; git clone https://github.com/vinadoros/CustomScripts /opt/CustomScripts; /opt/CustomScripts/{0} {1}".format(vmprovisionscript, vmprovision_opts)
if 50 <= args.ostype <= 69:
    data['provisioners'][0]["type"] = "powershell"
    data['provisioners'][0]["inline"] = "dir"
    data['builders'][0]["communicator"] = "winrm"
    data['builders'][0]["floppy_files"] = ["unattend/autounattend.xml",
    "unattend/windows/floppy/00-run-all-scripts.cmd",
    "unattend/windows/floppy/01-install-wget.cmd",
    "unattend/windows/floppy/_download.cmd",
    "unattend/windows/floppy/_packer_config.cmd",
    "unattend/windows/floppy/disablewinupdate.bat",
    "unattend/windows/floppy/fixnetwork.ps1",
    "unattend/windows/floppy/install-winrm.cmd",
    "unattend/windows/floppy/passwordchange.bat",
    "unattend/windows/floppy/powerconfig.bat",
    "unattend/windows/floppy/update.bat",
    "unattend/windows/floppy/zz-start-sshd.cmd"]
    data['builders'][0]["boot_command"] = ["<wait5> <enter> <wait>"]
    subprocess.run("git clone https://github.com/boxcutter/windows {0}".format(packer_temp_folder+"/unattend/windows"), shell=True)

# Write packer json file.
with open(packer_temp_folder+'/file.json', 'w') as file_json_wr:
    json.dump(data, file_json_wr, indent=2)

# Call packer.
subprocess.run("packer build file.json", shell=True)

# Remove temp folder
os.chdir(vmpath)
output_folder = packer_temp_folder+"/"+vmname
# Copy output to VM folder.
if os.path.isdir(output_folder):
    # Remove previous folder, if it exists.
    if os.path.isdir(vmpath+"/"+vmname):
        shutil.rmtree(vmpath+"/"+vmname)
    print("\nCopying {0} to {1}.".format(output_folder, vmpath))
    shutil.copytree(output_folder, vmpath+"/"+vmname)
print("Removing {0}".format(packer_temp_folder))
shutil.rmtree(packer_temp_folder)
print("VM successfully output to {0}".format(vmpath+"/"+vmname))