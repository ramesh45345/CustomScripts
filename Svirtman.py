#!/usr/bin/env python3
"""Install/uninstall libvirt and Virt-Manager."""

import argparse
import functools
import os
import shutil
import subprocess
import sys
import tempfile
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

### Functions ###
def libvirt_network_create(network: str, xml: str):
    """Create a libvirt network."""
    original_working_folder = os.getcwd()
    os.chdir(tempfile.gettempdir())
    # Remove networks before creating them
    libvirt_network_undef(network)

    NetXMLPath = os.path.join(tempfile.gettempdir(), f"{network}.xml")
    # Write xml
    with open(NetXMLPath, mode='w') as f:
        f.write(xml)
    # Define network
    subprocess.run(f"virsh net-define {network}.xml", shell=True, check=True)
    os.remove(NetXMLPath)
    # Start Network
    subprocess.run(f"virsh net-autostart {network}", shell=True, check=True)
    subprocess.run(f"virsh net-start {network}", shell=True, check=False)
    os.chdir(original_working_folder)
    return
def libvirt_network_undef(network: str):
    """Undefine/destroy a libvirt network."""
    subprocess.run(f"virsh net-autostart {network} --disable", shell=True, check=False)
    subprocess.run(f"virsh net-destroy {network}", shell=True, check=False)
    subprocess.run(f"virsh net-undefine {network}", shell=True, check=False)
    return


if __name__ == '__main__':
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
    ipv4_range_addr_default = "192.168.122"
    ipv4_range_addr_isolated = "192.168.123"
    if vmstate:
        ipv4_range_addr_default = "192.168.124"
        ipv4_range_addr_isolated = "192.168.125"
    # Installation Code
    if args.uninstall is False:
        if args.noinstall is False:
            print("Installing libvirt")
            if shutil.which("dnf"):
                CFunc.dnfinstall("@virtualization")
                CFunc.dnfinstall("python3-libguestfs swtpm swtpm-tools virtiofsd")
                CFunc.sysctl_enable("libvirtd", now=True, error_on_fail=True)
                subprocess.run("usermod -aG libvirt {0}".format(USERNAMEVAR), shell=True, check=True)
            elif shutil.which("apt-get"):
                CFunc.aptinstall("virt-manager qemu-kvm ssh-askpass python3-passlib virtiofsd")
                CFunc.AddUserToGroup("libvirt", USERNAMEVAR)
                CFunc.AddUserToGroup("libvirt-qemu", USERNAMEVAR)
                CFunc.AddUserToGroup("kvm", USERNAMEVAR)
            elif shutil.which("pacman"):
                CFunc.pacman_install("libvirt virt-manager edk2-ovmf qemu bridge-utils openbsd-netcat iptables-nft dnsmasq dnsmasq swtpm virtiofsd")
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

        # Add accept_ra
        # https://superuser.com/questions/1208952/qemu-kvm-libvirt-forwarding
        with open(SysctlAcceptRaPath, mode='w') as f:
            f.write("net.ipv6.conf.all.accept_ra = 2")
        with open("/proc/sys/net/ipv6/conf/all/accept_ra", mode='w') as f:
            f.write("2")

        # Create networks
        zoneinfo = ""
        if shutil.which("firewall-cmd"):
            zoneinfo = r"zone='trusted'"
        libvirt_network_create("default", f"""<network>
    <name>default</name>
    <forward mode='nat'/>
        <nat>
        <port start="1024" end="65535"/>
        </nat>
    <bridge name='virbr0' {zoneinfo} stp='off'/>
    <ip address='{ipv4_range_addr_default}.1' netmask='255.255.255.0'>
        <dhcp>
            <range start='{ipv4_range_addr_default}.2' end='{ipv4_range_addr_default}.254'/>
        </dhcp>
    </ip>
</network>""")
        libvirt_network_create("isolated", f"""<network>
    <name>isolated</name>
    <bridge name='virbr1' {zoneinfo} stp='off'/>
    <ip address='{ipv4_range_addr_isolated}.1' netmask='255.255.255.0'>
        <dhcp>
            <range start='{ipv4_range_addr_isolated}.2' end='{ipv4_range_addr_isolated}.254'/>
        </dhcp>
    </ip>
</network>""")
        # Set firewalld config
        if shutil.which("firewall-cmd"):
            subprocess.run("systemctl restart firewalld", shell=True, check=False)
            subprocess.run("firewall-cmd --permanent --zone=libvirt --add-port=0-65535/udp", shell=True, check=True)
            subprocess.run("firewall-cmd --permanent --zone=libvirt --add-port=0-65535/tcp", shell=True, check=True)
            subprocess.run("firewall-cmd --reload", shell=True, check=True)

    # Uninstallation Code
    if args.uninstall is True:
        print("Uninstalling libvirt")
        libvirt_network_undef("default")
        libvirt_network_undef("isolated")
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
