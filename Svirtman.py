#!/usr/bin/env python3
"""Install/uninstall libvirt and Virt-Manager."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Get arguments
parser = argparse.ArgumentParser(description='Install/uninstall libvirt and virt-manager.')
parser.add_argument("-e", "--noinstall", help='Skip installing libvirt packages.', action="store_true")
parser.add_argument("-i", "--image", help='Image path, i.e. /mnt/Storage/VMs')
parser.add_argument("-n", "--noprompt", help='Do not prompt to continue.', action="store_true")
parser.add_argument("-u", "--uninstall", help='Uninstall libvirt and virt-manager.', action="store_true")

# Save arguments.
args = parser.parse_args()


# Get non-root user information.
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()
print("Username is:", USERNAMEVAR)
print("Group Name is:", USERGROUP)

# Check if virtualized
vmstate = CFunc.getvmstate()
if vmstate:
    print("NOTE: Virtualized environment detected.")

# Process arguments
if args.uninstall:
    print("Uninstalling libvirt.")
else:
    print("Installing libvirt.")
if args.image and os.path.isdir(args.image):
    ImagePath = os.path.abspath(args.image)
    print("Path to store Images: {0}".format(ImagePath))
else:
    sys.exit("ERROR: Image path {0} is not valid. Please specify a valid folder.".format(args.image))

# Exit if not root.
CFunc.is_root(True)

if args.noprompt is False:
    input("Press Enter to continue.")


### Begin Code ###
# Set universal variables
PolkitPath = os.path.join(os.sep, "etc", "polkit-1")
PolkitRulesPath = os.path.join(PolkitPath, "rules.d")
PolkitUserRulePath = os.path.join(PolkitRulesPath, "80-libvirt.rules")
SysctlAcceptRaPath = os.path.join(os.sep, "etc", "sysctl.d", "99-acceptra.conf")
ipv4_range_addr = "192.168.122"
ipv6_range_addr = "fdab:8ce1:b5cd:fbd5"
if vmstate:
    ipv4_range_addr = "192.168.123"
    ipv6_range_addr = "fdab:8ce1:b5cd:fbd9"
# Installation Code
if args.uninstall is False:
    if args.noinstall is False:
        print("Installing libvirt")
        if shutil.which("dnf"):
            CFunc.dnfinstall("@virtualization")
            CFunc.dnfinstall("python3-libguestfs swtpm swtpm-tools")
            CFunc.sysctl_enable("libvirtd", now=True, error_on_fail=True)
            subprocess.run("usermod -aG libvirt {0}".format(USERNAMEVAR), shell=True, check=True)
        elif shutil.which("apt-get"):
            CFunc.aptinstall("virt-manager qemu-kvm ssh-askpass")
            subprocess.run("usermod -aG libvirt {0}".format(USERNAMEVAR), shell=True, check=True)
            subprocess.run("usermod -aG libvirt-qemu {0}".format(USERNAMEVAR), shell=True, check=True)
        elif shutil.which("pacman"):
            CFunc.pacman_install("libvirt virt-manager edk2-ovmf qemu bridge-utils openbsd-netcat iptables-nft dnsmasq dnsmasq swtpm")
            subprocess.run("usermod -aG libvirt {0}".format(USERNAMEVAR), shell=True, check=True)
            CFunc.sysctl_enable("libvirtd.service", now=True, error_on_fail=True)

    # Remove existing default pool
    subprocess.run("virsh pool-destroy default", shell=True, check=False)
    subprocess.run("virsh pool-undefine default", shell=True, check=False)
    print("List all pools after deletion")
    subprocess.run("virsh pool-list --all", shell=True, check=False)
    # Create new default pool
    subprocess.run('virsh pool-define-as default dir - - - - "{0}"'.format(ImagePath), shell=True, check=True)
    subprocess.run("virsh pool-autostart default", shell=True, check=True)
    subprocess.run("virsh pool-start default", shell=True, check=False)
    print("List all pools after re-creation")
    subprocess.run("virsh pool-list --all", shell=True, check=False)
    subprocess.run("virsh pool-info default", shell=True, check=False)

    # Set config info
    if os.path.isfile("/etc/libvirt/qemu.conf"):
        subprocess.run('''sed -i 's/#user = "root"/user = "{0}"/g' /etc/libvirt/qemu.conf'''.format(USERNAMEVAR), shell=True, check=True)
        subprocess.run('''sed -i 's/#save_image_format = "raw"/save_image_format = "xz"/g' /etc/libvirt/qemu.conf''', shell=True, check=True)
        subprocess.run('''sed -i 's/#dump_image_format = "raw"/dump_image_format = "xz"/g' /etc/libvirt/qemu.conf''', shell=True, check=True)
        subprocess.run('''sed -i 's/#snapshot_image_format = "raw"/snapshot_image_format = "xz"/g' /etc/libvirt/qemu.conf''', shell=True, check=True)

    if os.path.isdir(PolkitPath) and not os.path.isdir(PolkitRulesPath):
        os.makedirs(PolkitRulesPath)
    # https://ask.fedoraproject.org/en/question/45805/how-to-use-virt-manager-as-a-non-root-user/
    with open(PolkitUserRulePath, mode='w') as f:
        f.write("""polkit.addRule(function(action, subject) {
  if (action.id == "org.libvirt.unix.manage" && subject.active && subject.isInGroup("wheel")) {
      return polkit.Result.YES;
  }
});
""")

    # https://wiki.gentoo.org/wiki/QEMU/KVM_IPv6_Support
    zoneinfo = ""
    if shutil.which("firewall-cmd"):
        zoneinfo = r"zone='trusted'"
    NetXMLPath = os.path.join(tempfile.gettempdir(), "default.xml")
    NetXMLText = """<network>
  <name>default</name>
  <forward mode='nat'/>
    <nat ipv6="yes">
      <port start="1024" end="65535"/>
    </nat>
  <bridge name='virbr0' {2} stp='off'/>
  <ip address='{0}.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='{0}.2' end='{0}.254'/>
    </dhcp>
  </ip>
  <ip family='ipv6' address='{1}::1' prefix='96'>
    <dhcp>
      <range start='{1}::1000' end='{1}::2000' />
    </dhcp>
  </ip>
</network>
""".format(ipv4_range_addr, ipv6_range_addr, zoneinfo)
    with open(NetXMLPath, mode='w') as f:
        f.write(NetXMLText)
    subprocess.run("virsh net-destroy default", shell=True, check=False)
    subprocess.run("virsh net-undefine default", shell=True, check=False)
    # Add accept_ra
    # https://superuser.com/questions/1208952/qemu-kvm-libvirt-forwarding
    with open(SysctlAcceptRaPath, mode='w') as f:
        f.write("net.ipv6.conf.all.accept_ra = 2")
    with open("/proc/sys/net/ipv6/conf/all/accept_ra", mode='w') as f:
        f.write("2")
    os.chdir(tempfile.gettempdir())
    subprocess.run("virsh net-define default.xml", shell=True, check=True)
    os.remove(NetXMLPath)
    # Set network info
    subprocess.run("virsh net-autostart default", shell=True, check=True)
    subprocess.run("virsh net-start default", shell=True, check=False)
    # Set firewalld config
    if shutil.which("firewall-cmd"):
        subprocess.run("systemctl restart firewalld", shell=True, check=False)
        subprocess.run("firewall-cmd --permanent --zone=libvirt --add-port=0-65535/udp", shell=True, check=True)
        subprocess.run("firewall-cmd --permanent --zone=libvirt --add-port=0-65535/tcp", shell=True, check=True)
        subprocess.run("firewall-cmd --reload", shell=True, check=True)

# Uninstallation Code
if args.uninstall is True:
    print("Uninstalling libvirt")
    subprocess.run("virsh net-autostart default --disable", shell=True, check=True)
    subprocess.run("virsh net-destroy default", shell=True, check=True)
    if shutil.which("dnf"):
        CFunc.sysctl_disable("libvirtd.service", now=True, error_on_fail=True)
        subprocess.run("dnf remove @virtualization", shell=True, check=True)
    elif shutil.which("apt-get"):
        subprocess.run("apt-get --purge remove virt-manager qemu-kvm ssh-askpass", shell=True, check=True)
    elif shutil.which("pacman"):
        CFunc.sysctl_disable("libvirtd.service", now=True, error_on_fail=True)
        CFunc.pacman_invoke("-Rsn libvirt virt-manager edk2-ovmf qemu bridge-utils openbsd-netcat iptables-nft dnsmasq swtpm")
    if os.path.isfile(PolkitUserRulePath):
        os.remove(PolkitUserRulePath)
    if os.path.isfile(SysctlAcceptRaPath):
        os.remove(SysctlAcceptRaPath)

print("Script completed successfully!")
