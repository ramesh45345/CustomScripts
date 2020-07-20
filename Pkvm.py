#!/usr/bin/env python3
"""Create a virtual machine image using Packer"""

# Python includes.
import argparse
from datetime import datetime
import hashlib
import json
import logging
import multiprocessing
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Folder of this script
SCRIPTDIR = sys.path[0]


### Functions ###
def md5sum(md5_filename, blocksize=65536):
    """
    Calculate the MD5Sum of a file
    https://stackoverflow.com/a/21565932
    """
    hashmd5 = hashlib.md5()
    with open(md5_filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hashmd5.update(block)
    return hashmd5.hexdigest()
def packerversion_get():
    """Get the packer version from github"""
    releasejson_link = "https://api.github.com/repos/hashicorp/packer/tags"
    # Get the json data from GitHub.
    with urllib.request.urlopen(releasejson_link) as releasejson_handle:
        releasejson_data = json.load(releasejson_handle)
    for release in releasejson_data:
        # Stop after the first (latest) release is found.
        latestrelease = release["name"].strip().replace("v", "")
        break
    print("Detected packer version: {0}".format(latestrelease))
    return latestrelease
def xml_indent(elem, level=0):
    """
    Pretty Print XML using Python Standard libraries only
    http://effbot.org/zone/element-lib.htm#prettyprint
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            xml_indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
def xml_insertwindowskey(key, unattendfile):
    """Insert the windows key into the unattend xml file."""
    # Load the xml file
    xmlkey_tree = ET.parse(unattendfile)
    xmlkey_root = xmlkey_tree.getroot()
    # Insert ProductKey inside UserData.
    for element in xmlkey_root.iter():
        if "UserData" in element.tag:
            pkey_element = ET.SubElement(element, "ProductKey")
            key_subel = ET.SubElement(pkey_element, "Key")
            key_subel.text = key
    # Write the XML file
    xml_indent(xmlkey_root)
    xmlkey_tree.write(unattendfile)
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


# Exit if root.
CFunc.is_root(False)

# Get system and user information.
USERHOME = os.path.expanduser("~")
CPUCORES = multiprocessing.cpu_count() if multiprocessing.cpu_count() <= 4 else 4

# Get arguments
parser = argparse.ArgumentParser(description='Create a VM using packer.')
parser.add_argument("-a", "--ostype", type=int, help="OS type", default="1")
parser.add_argument("-b", "--getpacker", help="Force refresh packer", action="store_true")
parser.add_argument("-d", "--debug", help="Enable Debug output from packer", action="store_true")
parser.add_argument("-e", "--desktopenv", help="Desktop Environment (defaults to mate)", default="mate")
parser.add_argument("-i", "--iso", help="Path to live cd")
parser.add_argument("-m", "--memory", help="Memory for VM", default="4096")
parser.add_argument("-n", "--vmname", help="Name of Virtual Machine")
parser.add_argument("-p", "--vmpath", help="Path of Packer output", required=True)
parser.add_argument("-q", "--headless", help='Generate Headless', action="store_true")
parser.add_argument("-s", "--imgsize", type=int, help="Size of image", default=65536)
parser.add_argument("-t", "--vmtype", type=int, help="Virtual Machine type (1=Virtualbox, 2=libvirt, 3=VMWare, 4=hyperv)", default="1")
parser.add_argument("--noprompt", help='Do not prompt to continue.', action="store_true")
parser.add_argument("--fullname", help="Full Name", default="User Name")
parser.add_argument("--vmprovision", help="""Override provision options. Enclose options in double backslashes and quotes. Example: \\\\"-n -e 3\\\\" """)
parser.add_argument("--vmuser", help="VM Username", default="user")
parser.add_argument("--vmpass", help="VM Password", default="asdf")
parser.add_argument("--sshkey", help="SSH authorizaiton key")

# Save arguments.
args = parser.parse_args()

# Variables most likely to change.
vmpath = os.path.abspath(args.vmpath)
print("Path to Packer output is {0}".format(vmpath))
print("OS Type is {0}".format(args.ostype))
print("VM Memory is {0}".format(args.memory))
print("VM Hard Disk size is {0}".format(args.imgsize))
print("VM User is {0}".format(args.vmuser))
print("Desktop Environment:", args.desktopenv)
print("Headless:", args.headless)

# Get Packer
if not shutil.which("packer") or args.getpacker is True:
    print("Getting packer binary.")
    if not CFunc.is_windows():
        packer_os = "linux"
        packer_zipurl = "https://releases.hashicorp.com/packer/{0}/packer_{0}_{1}_amd64.zip".format(packerversion_get(), packer_os)
        packer_zipfile = CFunc.downloadfile(packer_zipurl, "/tmp")[0]
        subprocess.run("7z x -aoa -y {0} -o/usr/local/bin".format(packer_zipfile), shell=True)
        os.chmod("/usr/local/bin/packer", 0o777)
        if os.path.isfile(packer_zipfile):
            os.remove(packer_zipfile)
    subprocess.run("packer -v", shell=True)

# Ensure that certain commands exist.
cmdcheck = ["packer"]
for cmd in cmdcheck:
    if not shutil.which(cmd):
        sys.exit("\nError, ensure command {0} is installed.".format(cmd))

# Determine VM hypervisor
if args.vmtype == 1:
    hvname = "vbox"
elif args.vmtype == 2:
    hvname = "kvm"
elif args.vmtype == 3:
    hvname = "vmware"
elif args.vmtype == 4:
    hvname = "hyperv"

# Set OS options.
# KVM os options can be found by running "osinfo-query os"
if 1 <= args.ostype <= 4:
    vmprovisionscript = "MFedora.py"
    vboxosid = "Fedora_64"
    vmwareid = "fedora-64"
    kvm_os = "linux"
    kvm_variant = "fedora30"
    isourl = "https://download.fedoraproject.org/pub/fedora/linux/releases/32/Server/x86_64/iso/Fedora-Server-dvd-x86_64-32-1.6.iso"
if args.ostype == 1:
    vmname = "Packer-Fedora-{0}".format(hvname)
    vmprovision_defopts = "-d {0} -a".format(args.desktopenv)
if args.ostype == 2:
    vmname = "Packer-FedoraBare-{0}".format(hvname)
    vmprovision_defopts = "-d {0} -b".format(args.desktopenv)
if args.ostype == 3:
    vmname = "Packer-FedoraCLI-{0}".format(hvname)
    vmprovision_defopts = "-x -a"
if args.ostype == 4:
    vmname = "Packer-FedoraCLIBare-{0}".format(hvname)
    vmprovision_defopts = "-x -b"
if args.ostype == 9:
    vmprovisionscript = "MFedoraSilverblue.py"
    vboxosid = "Fedora_64"
    vmwareid = "fedora-64"
    kvm_os = "linux"
    kvm_variant = "fedora26"
    isourl = "https://download.fedoraproject.org/pub/fedora/linux/releases/32/Silverblue/x86_64/iso/Fedora-Silverblue-ostree-x86_64-32-1.6.iso"
    vmname = "Packer-FedoraSilverblue-{0}".format(hvname)
    vmprovision_defopts = ""
if 10 <= args.ostype <= 19:
    vboxosid = "Ubuntu_64"
    vmwareid = "ubuntu-64"
    vmprovisionscript = "MUbuntu.py"
    kvm_os = "linux"
# Ubuntu latest
if 10 <= args.ostype <= 14:
    kvm_variant = "ubuntu18.04"
    isourl = "https://releases.ubuntu.com/20.04/ubuntu-20.04-live-server-amd64.iso"
# Ubuntu LTS
if 15 <= args.ostype <= 19:
    kvm_variant = "ubuntu18.04"
    isourl = "http://cdimage.ubuntu.com/releases/18.04/release/ubuntu-18.04.4-server-amd64.iso"
if args.ostype == 10:
    vmname = "Packer-Ubuntu-{0}".format(hvname)
    vmprovision_defopts = "-d {0}".format(args.desktopenv)
if args.ostype == 11:
    vmname = "Packer-UbuntuCLI-{0}".format(hvname)
    vmprovision_defopts = "-x"
if args.ostype == 12:
    vmname = "Packer-UbuntuRolling-{0}".format(hvname)
    vmprovision_defopts = "-d {0} -r".format(args.desktopenv)
if args.ostype == 15:
    vmname = "Packer-UbuntuLTS-{0}".format(hvname)
    vmprovision_defopts = "-l -d {0}".format(args.desktopenv)
if args.ostype == 16:
    vmname = "Packer-UbuntuLTSCLI-{0}".format(hvname)
    vmprovision_defopts = "-l -x"
if 20 <= args.ostype <= 29:
    vboxosid = "Fedora_64"
    vmwareid = "fedora-64"
    kvm_os = "linux"
    kvm_variant = "manjaro"
    isourl = "http://www.gtlib.gatech.edu/pub/archlinux/iso/2020.07.01/archlinux-2020.07.01-x86_64.iso"
    vmprovisionscript = "MManjaro.py"
if args.ostype == 20:
    vmname = "Packer-Manjaro-{0}".format(hvname)
    vmprovision_defopts = "-d {0}".format(args.desktopenv)
if args.ostype == 21:
    vmname = "Packer-ManjaroCLI-{0}".format(hvname)
    vmprovision_defopts = "-x"
if 30 <= args.ostype <= 39:
    vboxosid = "Debian_64"
    vmwareid = "debian-64"
    vmprovisionscript = "MDebian.py"
    kvm_os = "linux"
    kvm_variant = "debiantesting"
# Debian Testing and Unstable
if 30 <= args.ostype <= 35:
    isourl = "https://cdimage.debian.org/cdimage/weekly-builds/amd64/iso-cd/debian-testing-amd64-netinst.iso"
# Debian Stable
if 36 <= args.ostype <= 38:
    isourl = "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-10.4.0-amd64-netinst.iso"
if args.ostype == 30:
    vmname = "Packer-DebianTesting-{0}".format(hvname)
    vmprovision_defopts = "-d {0} -a".format(args.desktopenv)
if args.ostype == 31:
    vmname = "Packer-DebianTestingCLI-{0}".format(hvname)
    vmprovision_defopts = "-a -x"
if args.ostype == 32:
    vmname = "Packer-DebianTestingBare-{0}".format(hvname)
    vmprovision_defopts = "-b -x"
if args.ostype == 33:
    vmname = "Packer-DebianUnstable-{0}".format(hvname)
    vmprovision_defopts = "-u -d {0} -a".format(args.desktopenv)
if args.ostype == 34:
    vmname = "Packer-DebianUnstableCLI-{0}".format(hvname)
    vmprovision_defopts = "-u -a -x"
if args.ostype == 35:
    vmname = "Packer-DebianUnstableBare-{0}".format(hvname)
    vmprovision_defopts = "-u -b -x"
if args.ostype == 36:
    vmname = "Packer-DebianStable-{0}".format(hvname)
    vmprovision_defopts = "-d {0} -a".format(args.desktopenv)
if args.ostype == 37:
    vmname = "Packer-DebianStableCLI-{0}".format(hvname)
    vmprovision_defopts = "-a -x"
if args.ostype == 38:
    vmname = "Packer-DebianStableBare-{0}".format(hvname)
    vmprovision_defopts = "-b -x"
if args.ostype == 40:
    vmname = "Packer-FreeBSD-{0}".format(hvname)
    vboxosid = "FreeBSD_64"
    vmwareid = "freebsd-64"
    vmprovisionscript = "MFreeBSD.py"
    vmprovision_defopts = "-d {0} -a".format(args.desktopenv)
    kvm_os = "freebsd"
    kvm_variant = "freebsd11.0"
    isourl = "https://download.freebsd.org/ftp/releases/amd64/amd64/ISO-IMAGES/12.1/FreeBSD-12.1-RELEASE-amd64-disc1.iso"
if 50 <= args.ostype <= 59:
    vboxosid = "Windows10_64"
    vmwareid = "windows9-64"
    kvm_os = "windows"
    kvm_variant = "win10"
    vmprovision_defopts = " "
    isourl = None
    # Windows KMS key list: https://docs.microsoft.com/en-us/windows-server/get-started/kmsclientkeys
    windows_key = None
if args.ostype == 50:
    vmname = "Packer-Windows10-{0}".format(hvname)
    windows_key = "NRG8B-VKK3Q-CXVCJ-9G2XF-6Q84J"
if args.ostype == 51:
    vmname = "Packer-Windows10LTS-{0}".format(hvname)
    windows_key = "M7XTQ-FN8P6-TTKYV-9D4CC-J462D"
if 55 <= args.ostype <= 59:
    vboxosid = "Windows2016_64"
    vmwareid = "windows9srv-64"
    kvm_os = "windows"
    kvm_variant = "win2k19"
    vmprovision_defopts = " "
if 55 <= args.ostype <= 56:
    windows_key = "N69G4-B89J2-4G8F4-WWYCC-J464C"
if args.ostype == 55:
    vmname = "Packer-Windows2019-{0}".format(hvname)
if args.ostype == 56:
    vmname = "Packer-Windows2019Core-{0}".format(hvname)


# Override provision opts if provided.
if args.vmprovision is None:
    vmprovision_opts = vmprovision_defopts
else:
    vmprovision_opts = args.vmprovision
print("VM Provision Options:", vmprovision_opts)

# Override VM Name if provided
if args.vmname is not None:
    vmname = args.vmname
print("VM Name is {0}".format(vmname))

# Detect Powershell command for Windows
powershell_cmd = None
if CFunc.is_windows():
    if shutil.which("pwsh"):
        powershell_cmd = "pwsh"
    elif shutil.which("powershell"):
        powershell_cmd = "powershell"

if args.noprompt is False:
    input("Press Enter to continue.")

# Set up VM hypervisor settings
if args.vmtype == 1:
    # Set vbox machine folder path.
    subprocess.run('vboxmanage setproperty machinefolder "{0}"'.format(vmpath), shell=True, check=True)
    # Create host only adapter if it does not exist.
    if CFunc.is_windows():
        vbox_hostonlyif_name = "VirtualBox Host-Only Ethernet Adapter"
    else:
        vbox_hostonlyif_name = "vboxnet0"
    vbox_hostonlyifs = CFunc.subpout("vboxmanage list hostonlyifs")
    if vbox_hostonlyif_name not in vbox_hostonlyifs:
        print("Creating {0} hostonlyif.".format(vbox_hostonlyif_name))
        subprocess.run("vboxmanage hostonlyif create", shell=True, check=True)
        # Set DHCP active on created adapter
        subprocess.run('vboxmanage hostonlyif ipconfig "{0}" --ip 192.168.253.1'.format(vbox_hostonlyif_name), shell=True, check=True)
        subprocess.run('vboxmanage dhcpserver modify --ifname "{0}" --ip 192.168.253.1 --netmask 255.255.255.0 --lowerip 192.168.253.2 --upperip 192.168.253.253 --enable'.format(vbox_hostonlyif_name), shell=True, check=True)
elif args.vmtype == 4:
    # Create an external switch if it does not already exist. External switch is required for guests to get DHCP.
    # https://github.com/MattHodge/PackerTemplates#building-hyper-v-images
    hyperv_switch_name = "External VM Switch"
    hyperv_mainnetadapter_name = "Ethernet"
    hyperv_winadapters = CFunc.subpout('{0} -c "Get-NetAdapter -Name "*" | Format-List -Property "Name""'.format(powershell_cmd))
    if hyperv_switch_name not in hyperv_winadapters:
        sys.exit('HyperV network adapter "{0}" not detected. Please install before continuing.'.format(hyperv_switch_name))

# Delete leftover VMs
if args.vmtype == 1:
    vboxvmlist = CFunc.subpout("VBoxManage list vms")
    if vmname in vboxvmlist:
        subprocess.run('VBoxManage unregistervm "{0}" --delete'.format(vmname), shell=True)
# KVM VMs removed before copy below.
elif args.vmtype == 3:
    print("Delete vmware image.")
elif args.vmtype == 4:
    hyperv_vmlist = CFunc.subpout('{0} -c "Get-VM"'.format(powershell_cmd))
    if vmname in hyperv_vmlist:
        subprocess.run('{0} -c "Stop-VM -Name {1} -TurnOff -Force"'.format(powershell_cmd, vmname), shell=True)
        subprocess.run('{0} -c "Remove-VM -Name {1} -TurnOff -Force"'.format(powershell_cmd, vmname), shell=True)

# Check iso
if args.iso is not None:
    isopath = os.path.abspath(args.iso)
else:
    isopath = CFunc.downloadfile(isourl, vmpath)[0]
if os.path.isfile(isopath) is True:
    print("Path to ISO is {0}".format(isopath))
else:
    sys.exit("\nError, ensure iso {0} exists.".format(isopath))

# Create temporary folder for packer
packer_temp_folder = os.path.join(vmpath, "packertemp" + vmname)
if os.path.isdir(packer_temp_folder):
    print("\nDeleting {0}.".format(packer_temp_folder))
    shutil.rmtree(packer_temp_folder)
os.mkdir(packer_temp_folder)
os.chdir(packer_temp_folder)

# Detect root ssh key.
if args.sshkey is not None:
    sshkey = args.rootsshkey
elif os.path.isfile(os.path.join(USERHOME, ".ssh", "id_ed25519.pub")) is True:
    with open(os.path.join(USERHOME, ".ssh", "id_ed25519.pub"), 'r') as sshfile:
        sshkey = sshfile.read().replace('\n', '')
elif os.path.isfile(os.path.join(USERHOME, ".ssh", "id_rsa.pub")) is True:
    with open(os.path.join(USERHOME, ".ssh", "id_rsa.pub"), 'r') as sshfile:
        sshkey = sshfile.read().replace('\n', '')
else:
    sshkey = " "
print("SSH Key is \"{0}\"".format(sshkey))

# Generate hashed password
# https://serverfault.com/questions/330069/how-to-create-an-sha-512-hashed-password-for-shadow#330072

if CFunc.is_windows() is True:
    from passlib import hash
    sha512_password = hash.sha512_crypt.hash(args.vmpass, rounds=5000)
else:
    import crypt
    sha512_password = crypt.crypt(args.vmpass, crypt.mksalt(crypt.METHOD_SHA512))


# Copy unattend script folder
if os.path.isdir(os.path.join(SCRIPTDIR, "unattend")):
    tempscriptbasename = os.path.basename(SCRIPTDIR)
    tempscriptfolderpath = os.path.join(packer_temp_folder, tempscriptbasename)
    tempunattendfolder = os.path.join(tempscriptfolderpath, "unattend")
    shutil.copytree(SCRIPTDIR, tempscriptfolderpath, ignore=shutil.ignore_patterns('.git'))
    # Set usernames and passwords
    CFunc.find_replace(tempunattendfolder, "INSERTUSERHERE", args.vmuser, "*")
    CFunc.find_replace(tempscriptfolderpath, "INSERTUSERHERE", args.vmuser, "Win-provision.ps1")
    CFunc.find_replace(tempunattendfolder, "INSERTPASSWORDHERE", args.vmpass, "*")
    CFunc.find_replace(tempscriptfolderpath, "INSERTPASSWORDHERE", args.vmpass, "Win-provision.ps1")
    CFunc.find_replace(tempunattendfolder, "INSERTFULLNAMEHERE", args.fullname, "*")
    CFunc.find_replace(tempunattendfolder, "INSERTHOSTNAMENAMEHERE", vmname, "*")
    CFunc.find_replace(tempunattendfolder, "INSERTHASHEDPASSWORDHERE", sha512_password, "*")
    CFunc.find_replace(tempunattendfolder, "INSERTSSHKEYHERE", sshkey, "*")


# Get hash for iso.
print("Generating Checksum of {0}".format(isopath))
md5 = md5sum(isopath)

# Create Packer json configuration
# Packer Builder Configuration
data = {}
data['builders'] = ['']
data['builders'][0] = {}
if args.headless is True:
    data['builders'][0]["headless"] = "true"
else:
    data['builders'][0]["headless"] = "false"
if args.vmtype == 1:
    data['builders'][0]["type"] = "virtualbox-iso"
    data['builders'][0]["guest_os_type"] = "{0}".format(vboxosid)
    data['builders'][0]["vm_name"] = "{0}".format(vmname)
    data['builders'][0]["hard_drive_interface"] = "sata"
    data['builders'][0]["sata_port_count"] = 2
    data['builders'][0]["iso_interface"] = "sata"
    data['builders'][0]["vboxmanage"] = ['']
    data['builders'][0]["vboxmanage"][0] = ["modifyvm", "{{.Name}}", "--memory", "{0}".format(args.memory)]
    data['builders'][0]["vboxmanage"].append(["modifyvm", "{{.Name}}", "--vram", "40"])
    data['builders'][0]["vboxmanage"].append(["modifyvm", "{{.Name}}", "--cpus", "{0}".format(CPUCORES)])
    data['builders'][0]["vboxmanage"].append(["modifyvm", "{{.Name}}", "--nic2", "hostonly"])
    data['builders'][0]["vboxmanage"].append(["modifyvm", "{{.Name}}", "--hostonlyadapter2", vbox_hostonlyif_name])
    data['builders'][0]["vboxmanage_post"] = ['']
    data['builders'][0]["vboxmanage_post"][0] = ["modifyvm", "{{.Name}}", "--clipboard", "bidirectional"]
    data['builders'][0]["vboxmanage_post"].append(["modifyvm", "{{.Name}}", "--accelerate3d", "on"])
    if CFunc.is_windows() is False:
        data['builders'][0]["vboxmanage_post"].append(["sharedfolder", "add", "{{.Name}}", "--name", "root", "--hostpath", "/", "--automount"])
    data['builders'][0]["post_shutdown_delay"] = "30s"
    if 1 <= args.ostype <= 39 or 70 <= args.ostype <= 99:
        data['builders'][0]["vboxmanage"].append(["modifyvm", "{{.Name}}", "--nictype1", "virtio"])
        data['builders'][0]["vboxmanage"].append(["modifyvm", "{{.Name}}", "--nictype2", "virtio"])
    if 50 <= args.ostype <= 59:
        # https://hodgkins.io/best-practices-with-packer-and-windows#use-headless-mode
        data['builders'][0]["headless"] = "true"
        data['builders'][0]["guest_additions_mode"] = "upload"
        data['builders'][0]["guest_additions_path"] = "c:/Windows/Temp/windows.iso"
elif args.vmtype == 2:
    data['builders'][0]["type"] = "qemu"
    data['builders'][0]["accelerator"] = "kvm"
    if 50 <= args.ostype <= 59:
        # Use more generic hardware for windows
        kvm_diskinterface = "ide"
        kvm_netdevice = "e1000"
    else:
        kvm_diskinterface = "virtio"
        kvm_netdevice = "virtio-net"
    data['builders'][0]["disk_interface"] = kvm_diskinterface
    data['builders'][0]["net_device"] = kvm_netdevice
    data['builders'][0]["vm_name"] = "{0}.qcow2".format(vmname)
    data['builders'][0]["qemuargs"] = ['']
    data['builders'][0]["qemuargs"][0] = ["-m", "{0}M".format(args.memory)]
    data['builders'][0]["qemuargs"].append(["--cpu", "host"])
    data['builders'][0]["qemuargs"].append(["--smp", "cores={0}".format(CPUCORES)])
elif args.vmtype == 3:
    data['builders'][0]["type"] = "vmware-iso"
    data['builders'][0]["version"] = "12"
    data['builders'][0]["vm_name"] = "{0}".format(vmname)
    data['builders'][0]["vmdk_name"] = "{0}".format(vmname)
    data['builders'][0]["vmx_data"] = {"virtualhw.version": "12", "memsize": "{0}".format(args.memory), "numvcpus": "{0}".format(CPUCORES), "cpuid.coresPerSocket": "{0}".format(CPUCORES), "guestos": "{0}".format(vmwareid), "usb.present": "TRUE", "scsi0.virtualDev": "lsisas1068"}
    data['builders'][0]["vmx_data_post"] = {"sharedFolder0.present": "TRUE", "sharedFolder0.enabled": "TRUE", "sharedFolder0.readAccess": "TRUE", "sharedFolder0.writeAccess": "TRUE", "sharedFolder0.hostPath": "/", "sharedFolder0.guestName": "root", "sharedFolder0.expiration": "never", "sharedFolder.maxNum": "1", "isolation.tools.hgfs.disable": "FALSE"}
    if 50 <= args.ostype <= 59:
        data['builders'][0]["tools_upload_flavor"] = "windows"
        data['builders'][0]["tools_upload_path"] = "c:/Windows/Temp/windows.iso"
elif args.vmtype == 4:
    data['builders'][0]["type"] = "hyperv-iso"
    data['builders'][0]["vm_name"] = "{0}".format(vmname)
    data['builders'][0]["memory"] = "{0}".format(args.memory)
    data['builders'][0]["enable_dynamic_memory"] = True
data['builders'][0]["shutdown_command"] = "shutdown -P now"
data['builders'][0]["iso_url"] = "{0}".format(isopath)
data['builders'][0]["iso_checksum"] = "md5:{0}".format(md5)
data['builders'][0]["output_directory"] = "{0}".format(vmname)
data['builders'][0]["http_directory"] = tempunattendfolder
data['builders'][0]["disk_size"] = "{0}".format(args.imgsize)
data['builders'][0]["boot_wait"] = "5s"
data['builders'][0]["ssh_username"] = "root"
data['builders'][0]["ssh_password"] = "{0}".format(args.vmpass)
data['builders'][0]["ssh_timeout"] = "90m"
# Packer Provisioning Configuration
data['provisioners'] = ['']
data['provisioners'][0] = {}
if 1 <= args.ostype <= 4:
    data['builders'][0]["boot_command"] = ["<tab> inst.text inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/fedora.cfg<enter><wait>"]
    data['provisioners'][0]["type"] = "shell"
    data['provisioners'][0]["inline"] = "dnf install -y git; {2}; /opt/CustomScripts/{0} {1}".format(vmprovisionscript, vmprovision_opts, git_cmdline())
if args.ostype == 9:
    data['builders'][0]["boot_command"] = ["<tab> inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/silverblue.cfg<enter><wait>"]
    data['provisioners'][0]["type"] = "shell"
    data['provisioners'][0]["inline"] = "{1}; /opt/CustomScripts/{0} -s 1; systemctl reboot".format(vmprovisionscript, git_cmdline())
    data['provisioners'][0]["expect_disconnect"] = True
    data['provisioners'].append('')
    data['provisioners'][1] = {}
    data['provisioners'][1]["type"] = "shell"
    data['provisioners'][1]["inline"] = "/opt/CustomScripts/{0} -s 2".format(vmprovisionscript)
    data['provisioners'][1]["pause_before"] = "15s"
    data['provisioners'][1]["timeout"] = "90m"
if 10 <= args.ostype <= 19:
    data['provisioners'][0]["type"] = "shell"
    data['provisioners'][0]["inline"] = "mkdir -m 700 -p /root/.ssh; echo '{sshkey}' > /root/.ssh/authorized_keys; mkdir -m 700 -p ~{vmuser}/.ssh; echo '{sshkey}' > ~{vmuser}/.ssh/authorized_keys; chown {vmuser}:{vmuser} -R ~{vmuser}; apt install -y git; {gitcmd}; /opt/CustomScripts/{vmprovisionscript} {vmprovision_opts}".format(vmprovisionscript=vmprovisionscript, vmprovision_opts=vmprovision_opts, sshkey=sshkey, vmuser=args.vmuser, gitcmd=git_cmdline())
if 10 <= args.ostype <= 14:
    # Create user-data and meta-data.
    # https://cloudinit.readthedocs.io/en/latest/topics/datasources/nocloud.html
    shutil.move(os.path.join(tempscriptfolderpath, "unattend", "ubuntu.yaml"), os.path.join(tempscriptfolderpath, "unattend", "user-data"))
    pathlib.Path(os.path.join(tempscriptfolderpath, "unattend", "meta-data")).touch(exist_ok=True)
    data['builders'][0]["boot_wait"] = "1s"
    data['builders'][0]["boot_command"] = ["<space><wait><enter><wait><f6><wait><esc><home>ds=nocloud-net;s=http://{{ .HTTPIP }}:{{ .HTTPPort }}/ autoinstall <enter>"]
    # Workaround for ssh being enabled on livecd. Remove this when a method to disable ssh on livecd is found.
    data['builders'][0]["ssh_handshake_attempts"] = "9999"
if 15 <= args.ostype <= 19:
    data['builders'][0]["boot_command"] = ["<enter><wait><down><wait><f6><wait><esc><home>url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/ubuntu.cfg hostname=ubuntu locale=en_US keyboard-configuration/modelcode=SKIP netcfg/choose_interface=auto <enter>"]
if 20 <= args.ostype <= 29:
    data['builders'][0]["boot_wait"] = "1s"
    data['builders'][0]["boot_command"] = ["""<enter><wait40>bash -c 'pacman -Sy --noconfirm git wget && {gitcmd} && /opt/CustomScripts/ZSlimDrive.py -n && /opt/CustomScripts/BManjaro.py -n -c "{vmname}" -u "{vmuser}" -f "{fullname}" -q "{vmpass}" -l "linux-lts" /mnt && reboot'<enter>""".format(vmname=vmname, vmuser=args.vmuser, vmpass=args.vmpass, fullname=args.fullname, gitcmd=git_cmdline())]
    data['builders'][0]["ssh_handshake_attempts"] = "9999"
    data['provisioners'][0]["type"] = "shell"
    data['provisioners'][0]["inline"] = "mkdir -m 700 -p /root/.ssh; echo '{sshkey}' > /root/.ssh/authorized_keys; mkdir -m 700 -p ~{vmuser}/.ssh; echo '{sshkey}' > ~{vmuser}/.ssh/authorized_keys; chown {vmuser}:users -R ~{vmuser}; pacman -Sy --noconfirm git; {gitcmd}; /opt/CustomScripts/{vmprovisionscript} {vmprovision_opts}".format(vmuser=args.vmuser, sshkey=sshkey, vmprovisionscript=vmprovisionscript, vmprovision_opts=vmprovision_opts, gitcmd=git_cmdline())
if 30 <= args.ostype <= 39:
    data['provisioners'][0]["type"] = "shell"
    data['provisioners'][0]["inline"] = "mkdir -m 700 -p /root/.ssh; echo '{sshkey}' > /root/.ssh/authorized_keys; mkdir -m 700 -p ~{vmuser}/.ssh; echo '{sshkey}' > ~{vmuser}/.ssh/authorized_keys; chown {vmuser}:{vmuser} -R ~{vmuser}; apt install -y git; {gitcmd}; /opt/CustomScripts/{vmprovisionscript} {vmprovision_opts}".format(vmprovisionscript=vmprovisionscript, vmprovision_opts=vmprovision_opts, sshkey=sshkey, vmuser=args.vmuser, gitcmd=git_cmdline())
    data['builders'][0]["boot_command"] = ["<esc>auto url=http://{{ .HTTPIP }}:{{ .HTTPPort }}/debian.cfg hostname=debian locale=en_US keyboard-configuration/modelcode=SKIP netcfg/choose_interface=auto <enter>"]
if 40 <= args.ostype <= 41:
    data['builders'][0]["boot_command"] = ["<wait2><enter><wait30><right><wait><enter><wait>dhclient -b vtnet0<enter><wait>dhclient -b em0<enter><wait10>fetch -o /tmp/installerconfig http://{{ .HTTPIP }}:{{ .HTTPPort }}/freebsd<wait><enter><wait>bsdinstall script /tmp/installerconfig<wait><enter>"]
    data['provisioners'][0]["type"] = "shell"
    # Needed for freebsd: https://www.packer.io/docs/provisioners/shell.html#execute_command
    data['provisioners'][0]["execute_command"] = "chmod +x {{ .Path }}; env {{ .Vars }} {{ .Path }}"
    data['provisioners'][0]["inline"] = '''export ASSUME_ALWAYS_YES=yes; pw useradd -n {vmuser} -m; pw usermod {vmuser} -c "{fullname}"; chpass -p '{encpass}' {vmuser}; mkdir -m 700 -p /root/.ssh; echo "{sshkey}" > /root/.ssh/authorized_keys; mkdir -m 700 -p ~{vmuser}/.ssh; echo "{sshkey}" > ~{vmuser}/.ssh/authorized_keys; chown -R {vmuser}:{vmuser} ~{vmuser}; pkg update -f; pkg install -y git python3; {gitcmd}; /opt/CustomScripts/{vmprovisionscript} {vmprovision_opts}'''.format(vmprovisionscript=vmprovisionscript, vmprovision_opts=vmprovision_opts, sshkey=sshkey, vmuser=args.vmuser, encpass=sha512_password, fullname=args.fullname, gitcmd=git_cmdline())
    data['builders'][0]["shutdown_command"] = "shutdown -p now"
if 50 <= args.ostype <= 59:
    # Reboot after initial script
    data['provisioners'][0]["type"] = "windows-restart"
    data['provisioners'][0]["restart_timeout"] = "10m"
    # Set up provisioner for powershell script
    data['provisioners'].append('')
    data['provisioners'][1] = {}
    data['provisioners'][1]["type"] = "powershell"
    # Provision with generic windows script
    data['provisioners'][1]["scripts"] = [os.path.join(tempscriptfolderpath, "Win-provision.ps1")]
    data['builders'][0]["boot_command"] = ["<wait5>"]
    data['builders'][0]["shutdown_command"] = "shutdown /s /t 60"
    data['builders'][0]["shutdown_timeout"] = "15m"
    data['builders'][0]["communicator"] = "winrm"
    data['builders'][0]["winrm_insecure"] = True
    data['builders'][0]["winrm_username"] = "{0}".format(args.vmuser)
    data['builders'][0]["winrm_password"] = "{0}".format(args.vmpass)
    data['builders'][0]["winrm_timeout"] = "90m"
    data['builders'][0]["winrm_use_ssl"] = False
    data['builders'][0]["winrm_use_ntlm"] = True
    data['builders'][0]["ssh_username"] = "{0}".format(args.vmuser)
    data['builders'][0]["floppy_files"] = [os.path.join(tempscriptbasename, "unattend", "autounattend.xml"),
                                           os.path.join(tempscriptbasename, "unattend", "win_initial.bat"),
                                           os.path.join(tempscriptbasename, "unattend", "win_enablerm.ps1"),
                                           os.path.join(tempscriptbasename, "unattend", "win_cygssh.bat")]
    # Register the namespace to avoid nsX in namespace.
    ET.register_namespace('', "urn:schemas-microsoft-com:unattend")
    ET.register_namespace('wcm', "http://schemas.microsoft.com/WMIConfig/2002/State")
    ET.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")
if args.ostype == 50:
    shutil.move(os.path.join(tempunattendfolder, "windows10.xml"), os.path.join(tempunattendfolder, "autounattend.xml"))
    # Insert product key
    xml_insertwindowskey(windows_key, os.path.join(tempunattendfolder, "autounattend.xml"))
if args.ostype == 51:
    shutil.move(os.path.join(tempunattendfolder, "windows10.xml"), os.path.join(tempunattendfolder, "autounattend.xml"))
    # Insert product key
    xml_insertwindowskey(windows_key, os.path.join(tempunattendfolder, "autounattend.xml"))
if 55 <= args.ostype <= 59:
    shutil.move(os.path.join(tempunattendfolder, "windows10.xml"), os.path.join(tempunattendfolder, "autounattend.xml"))
    # Insert Windows Server product key
    xml_insertwindowskey(windows_key, os.path.join(tempunattendfolder, "autounattend.xml"))
    # Load the xml file
    tree = ET.parse(os.path.join(tempunattendfolder, "autounattend.xml"))
    root = tree.getroot()
    # Insert InstallFrom inside OSImage.
    for element in root.iter():
        if "OSImage" in element.tag:
            infrm_element = ET.SubElement(element, "InstallFrom")
            metadata_subel = ET.SubElement(infrm_element, "MetaData")
            metadata_subel.set("wcm:action", "add")
            key_element = ET.SubElement(metadata_subel, "Key")
            key_element.text = "/IMAGE/INDEX"
            value_element = ET.SubElement(metadata_subel, "Value")
            value_element.text = "INSERTWINOSIMAGE"
    # Write the XML file
    xml_indent(root)
    tree.write(os.path.join(tempunattendfolder, "autounattend.xml"))
if args.ostype == 55:
    CFunc.find_replace(tempunattendfolder, "INSERTWINOSIMAGE", "2", "autounattend.xml")
if args.ostype == 56:
    CFunc.find_replace(tempunattendfolder, "INSERTWINOSIMAGE", "1", "autounattend.xml")


# Write packer json file.
with open(os.path.join(packer_temp_folder, 'file.json'), 'w') as file_json_wr:
    json.dump(data, file_json_wr, indent=2)

# Set debug environment variable
if args.debug:
    os.environ["PACKER_LOG"] = "1"

# Save start time.
beforetime = datetime.now()
# Initiate logger
buildlog_path = os.path.join(vmpath, "{0}.log".format(vmname))
CFunc.log_config(buildlog_path)
# Call packer.
packer_buildcmd = "packer build file.json"
CFunc.subpout_logger(packer_buildcmd)
# Save packer finish time.
packerfinishtime = datetime.now()

# Remove temp folder
os.chdir(vmpath)
output_folder = os.path.join(packer_temp_folder, vmname)
buildlog_sourcepath = os.path.join(packer_temp_folder, "build.log")

# Copy output to VM folder.
if os.path.isdir(output_folder):
    # Remove previous folder, if it exists.
    if os.path.isdir(os.path.join(vmpath, vmname)):
        shutil.rmtree(os.path.join(vmpath, vmname))
    # Remove existing VMs in KVM
    if args.vmtype == 2:
        kvmlist = CFunc.subpout("virsh --connect qemu:///system -q list --all")
        if vmname.lower() in kvmlist.lower():
            subprocess.run('virsh --connect qemu:///system destroy "{0}"'.format(vmname), shell=True)
            subprocess.run('virsh --connect qemu:///system undefine "{0}"'.format(vmname), shell=True)
    # Remove previous file for kvm.
    if args.vmtype == 2 and os.path.isfile(os.path.join(vmpath, vmname + ".qcow2")):
        os.remove(os.path.join(vmpath, vmname + ".qcow2"))
    logging.info("\nCopying {0} to {1}.".format(output_folder, vmpath))
    if args.vmtype != 2:
        shutil.copytree(output_folder, os.path.join(vmpath, vmname))
    # Copy the qcow2 file, and remove the folder entirely for kvm.
    if args.vmtype == 2 and os.path.isfile(os.path.join(output_folder, vmname + ".qcow2")):
        shutil.copy2(os.path.join(output_folder, vmname + ".qcow2"), os.path.join(vmpath, vmname + ".qcow2"))
if args.debug:
    logging.info("Not removing {0}, debug flag is set. Please remove this folder manually.".format(packer_temp_folder))
else:
    logging.info("Removing {0}".format(packer_temp_folder))
    shutil.rmtree(packer_temp_folder)
logging.info("VM successfully output to {0}".format(os.path.join(vmpath, vmname)))
# Save full finish time.
fullfinishtime = datetime.now()

# Attach VM to libvirt
if args.vmtype == 2:
    if 50 <= args.ostype <= 59:
        kvm_video = "qxl"
        kvm_diskinterface = "sata"
        kvm_netdevice = "virtio"
    else:
        kvm_video = "virtio"
        kvm_diskinterface = "virtio"
        kvm_netdevice = "virtio"
    # virt-install manual: https://www.mankier.com/1/virt-install
    # List of os: osinfo-query os
    CREATESCRIPT_KVM = """virt-install --connect qemu:///system --name={vmname} --disk path={fullpathtoimg}.qcow2,bus={kvm_diskinterface} --graphics spice --vcpu={cpus} --ram={memory} --network bridge=virbr0,model={kvm_netdevice} --filesystem source=/,target=root,mode=mapped --os-type={kvm_os} --os-variant={kvm_variant} --import --noautoconsole --noreboot --video={kvm_video} --channel unix,target_type=virtio,name=org.qemu.guest_agent.0 --channel spicevmc,target_type=virtio,name=com.redhat.spice.0""".format(vmname=vmname, memory=args.memory, cpus=CPUCORES, fullpathtoimg=os.path.join(vmpath, vmname), kvm_os=kvm_os, kvm_variant=kvm_variant, kvm_video=kvm_video, kvm_diskinterface=kvm_diskinterface, kvm_netdevice=kvm_netdevice)
    logging.info("KVM launch command: {0}".format(CREATESCRIPT_KVM))
    if args.noprompt is False:
        subprocess.run(CREATESCRIPT_KVM, shell=True)

# Print finish times
logging.info("Packer completed in {0}".format(str(packerfinishtime - beforetime)))
logging.info("Whole thing completed in {0}".format(str(fullfinishtime - beforetime)))
