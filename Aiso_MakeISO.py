#!/usr/bin/env python3
"""Create ISOs within VM."""



# SSH into VM, fixed name.
# Run CreateVM script to re-provision, create and/or update chroots.
# Remove existing folders.
# Run scripts.
# Check for ISOs, copy into host using scp.
# Cleanup.

# Arch: Use systemd-nspawn
# Fedora: Use chroot
# Ubuntu: 