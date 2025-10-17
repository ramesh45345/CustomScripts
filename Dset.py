#!/usr/bin/env python3
"""Set Desktop Settings"""

# Python includes
import argparse
import configparser
import functools
import os
import pathlib
import subprocess
import shutil
import sys
import xml.etree.ElementTree as ET
# Custom includes
import CFunc
import CMimeSet

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

print("Running {0}".format(__file__))

### Functions ###
def icon_theme_is_present():
    """Check if the preferred icon theme (Numix-Circle) is present."""
    theme_exists = False
    if os.path.isdir("/usr/share/icons/Numix-Circle") or os.path.isdir("/usr/local/share/icons/Numix-Circle"):
        theme_exists = True
    elif CFunc.is_nixos() is True:
        theme_exists = True
    return theme_exists
def gsettings_set(schema: str, key: str, value: str):
    """Set dconf setting using gsettings."""
    status = subprocess.run(['gsettings', 'set', schema, key, value], check=False).returncode
    if status != 0:
        print("ERROR, failed to run: gsettings set {0} {1} {2}".format(schema, key, value))
def dconf_write(key: str, value: str):
    """Set dconf setting using dconf write."""
    status = subprocess.run(['dconf', 'write', key, value], check=False).returncode
    if status != 0:
        print("ERROR, failed to run: dconf write {0} {1}".format(key, value))
def kwriteconfig(file: str, group, key: str, value: str, type: str = "str"):
    """Set KDE configs using kwriteconfig6."""
    cmd = ['kwriteconfig6', '--file', file]
    # Loop through the group if it is a list.
    if isinstance(group, list):
        for x in group:
            cmd += ["--group", x]
    else:
        cmd += ["--group", group]
    cmd += ["--key", key, "--type", type, value]
    # Run command
    status = subprocess.run(cmd, check=False).returncode
    # Print if error
    if status != 0:
        print(f"ERROR, failed to run: {cmd}")
def xfconf(channel: str, prop: str, var_type: str, value: str, extra_options: list = None):
    """
    Set value to property using xfconf.
    https://docs.xfce.org/xfce/xfconf/xfconf-query
    """
    cmd_list = ['xfconf-query', '--channel', channel, '--property', prop, '--type', var_type, '--set', value, '--create']
    if extra_options:
        cmd_list += extra_options
    status = subprocess.run(cmd_list, check=False).returncode
    if status != 0:
        print("ERROR, failed to run: xfconf-query --channel {channel} --property {prop} --type {var_type} --set {value} --create".format(channel=channel, prop=prop, var_type=var_type, value=value))
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


# Get arguments
parser = argparse.ArgumentParser(description='Set Desktop Settings.')
parser.add_argument("-p", "--disable_powersave", help='Force turning off powersave modes (like for VMs).', action="store_true")
parser.add_argument("-s", "--screens", help='Number of screens (for panels) for Plasma Desktop (default: %(default)s)', type=int, choices=range(1, 6), default=1)

args = parser.parse_args()

# Exit if root.
CFunc.is_root(False)

# Get VM State
vmstatus = CFunc.getvmstate()

# Home folder
USERHOME = str(pathlib.Path.home())


### Begin Code ###
# Mime Settings
CMimeSet.HandlePredefines("text", "codium.desktop")
CMimeSet.HandlePredefines("audio", "org.atheme.audacious.desktop")

# Commented statements to set default text editor
# xdg-mime default pluma.desktop text/plain
# Commented statements to set default file manager
# xdg-mime default nemo.desktop inode/directory
# xdg-mime default caja-browser.desktop inode/directory
# xdg-mime default org.gnome.Nautilus.desktop inode/directory
# To find out default file manager:
# xdg-mime query default inode/directory

# Tilix configuration
if shutil.which("tilix"):
    dconf_write("/com/gexperts/Tilix/Settings/warn-vte-config-issue", "false")
    dconf_write("/com/gexperts/Tilix/Settings/terminal-title-style", "'small'")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/login-shell", "true")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/scrollback-unlimited", "true")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/terminal-bell", "'icon'")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/use-theme-colors", "false")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/background-color", "'#263238'")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/foreground-color", "'#A1B0B8'")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/palette", "['#252525', '#FF5252', '#C3D82C', '#FFC135', '#42A5F5', '#D81B60', '#00ACC1', '#F5F5F5', '#708284', '#FF5252', '#C3D82C', '#FFC135', '#42A5F5', '#D81B60', '#00ACC1', '#F5F5F5']")
    # Set system font used by tilix
    dconf_write("/org/gnome/desktop/interface/monospace-font-name", "'Liberation Mono 11'")
    # Fish config for tilix
    if shutil.which("fish"):
        dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/use-custom-command", "true")
        dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/custom-command", "'{0}'".format(shutil.which("fish")))
    else:
        dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/use-custom-command", "false")

# ptyxis config
if shutil.which("ptyxis"):
    ptyxis_profile = CFunc.subpout("dconf read /org/gnome/Ptyxis/default-profile-uuid").strip("'")
    if ptyxis_profile == "":
        ptyxis_profile = "42252167cc65db90269998256869218d"
        dconf_write("/org/gnome/Ptyxis/default-profile-uuid", f"'{ptyxis_profile}'")
        dconf_write("/org/gnome/Ptyxis/profile-uuids", f"['{ptyxis_profile}']")
    dconf_write("/org/gnome/Ptyxis/restore-window-size", "false")
    dconf_write("/org/gnome/Ptyxis/default-rows", "uint32 25")
    dconf_write("/org/gnome/Ptyxis/default-columns", "uint32 80")
    dconf_write("/org/gnome/Ptyxis/restore-session", "false")
    dconf_write(f"/org/gnome/Ptyxis/Profiles/{ptyxis_profile}/limit-scrollback", "false")
    dconf_write(f"/org/gnome/Ptyxis/Profiles/{ptyxis_profile}/palette", "'nord'")
    dconf_write("/org/gnome/Ptyxis/use-system-font", "false")
    dconf_write("/org/gnome/Ptyxis/font-name", "'Monospace 11'")
    dconf_write("/org/gnome/Ptyxis/interface-style", "'dark'")
    # Fish config
    if shutil.which("fish"):
        dconf_write(f"/org/gnome/Ptyxis/Profiles/{ptyxis_profile}/use-custom-command", "true")
        dconf_write(f"/org/gnome/Ptyxis/Profiles/{ptyxis_profile}/custom-command", "'{0}'".format(shutil.which("fish")))
    else:
        dconf_write(f"/org/gnome/Ptyxis/Profiles/{ptyxis_profile}/use-custom-command", "false")

# Gnome System Monitor
if shutil.which("gnome-system-monitor"):
    dconf_write("/org/gnome/gnome-system-monitor/cpu-stacked-area-chart", "true")
    dconf_write("/org/gnome/gnome-system-monitor/resources-memory-in-iec", "true")
    dconf_write("/org/gnome/gnome-system-monitor/process-memory-in-iec", "true")
    dconf_write("/org/gnome/gnome-system-monitor/proctree/sort-order", "0")
    dconf_write("/org/gnome/gnome-system-monitor/show-whose-processes", "'all'")

# MATE specific settings
if shutil.which("mate-session"):
    gsettings_set("org.mate.pluma", "create-backup-copy", "false")
    gsettings_set("org.mate.pluma", "display-line-numbers", "true")
    gsettings_set("org.mate.pluma", "highlight-current-line", "true")
    gsettings_set("org.mate.pluma", "bracket-matching", "true")
    gsettings_set("org.mate.pluma", "auto-indent", "true")
    gsettings_set("org.mate.pluma", "tabs-size", "4")
    gsettings_set("org.gtk.Settings.FileChooser", "show-hidden", "true")
    gsettings_set("org.mate.caja.preferences", "executable-text-activation", "ask")
    gsettings_set("org.mate.caja.preferences", "enable-delete", "true")
    gsettings_set("org.mate.caja.preferences", "click-policy", "double")
    gsettings_set("org.mate.caja.preferences", "default-folder-viewer", "list-view")
    gsettings_set("org.mate.caja.list-view", "default-zoom-level", "smaller")
    gsettings_set("org.mate.caja.preferences", "preview-sound", "'never'")
    gsettings_set("org.mate.caja.preferences", "show-advanced-permissions", "true")
    gsettings_set("org.mate.caja.preferences", "show-hidden-files", "true")
    gsettings_set("org.mate.caja.preferences", "use-iec-units", "true")
    gsettings_set("org.mate.peripherals-touchpad", "disable-while-typing", "true")
    gsettings_set("org.mate.peripherals-touchpad", "tap-to-click", "true")
    gsettings_set("org.mate.peripherals-touchpad", "horizontal-two-finger-scrolling", "true")
    gsettings_set("org.mate.power-manager", "idle-dim-ac", "false")
    gsettings_set("org.mate.power-manager", "button-lid-ac", "blank")
    gsettings_set("org.mate.power-manager", "button-lid-battery", "blank")
    gsettings_set("org.mate.power-manager", "button-power", "shutdown")
    gsettings_set("org.mate.power-manager", "button-suspend", "suspend")
    if vmstatus or args.disable_powersave:
        gsettings_set("org.mate.power-manager", "sleep-display-ac", "0")
    else:
        gsettings_set("org.mate.power-manager", "sleep-display-ac", "300")
    gsettings_set("org.mate.power-manager", "sleep-display-battery", "300")
    gsettings_set("org.mate.power-manager", "action-critical-battery", "nothing")
    gsettings_set("org.mate.screensaver", "idle-activation-enabled", "false")
    gsettings_set("org.mate.screensaver", "lock-enabled", "false")
    gsettings_set("org.mate.screensaver", "mode", "blank-only")
    gsettings_set("org.mate.font-rendering", "antialiasing", "grayscale")
    gsettings_set("org.mate.font-rendering", "hinting", "slight")
    gsettings_set("org.mate.peripherals-mouse", "middle-button-enabled", "true")
    dconf_write("/org/mate/terminal/profiles/default/scrollback-unlimited", "true")
    dconf_write("/org/mate/panel/objects/clock/prefs/format", "'12-hour'")
    dconf_write("/org/mate/panel/objects/clock/position", "0")
    dconf_write("/org/mate/panel/objects/clock/panel-right-stick", "true")
    dconf_write("/org/mate/panel/objects/clock/locked", "true")
    dconf_write("/org/mate/panel/objects/notification-area/position", "10")
    dconf_write("/org/mate/panel/objects/notification-area/panel-right-stick", "true")
    dconf_write("/org/mate/panel/objects/notification-area/locked", "true")
    gsettings_set("org.mate.Marco.general", "allow-top-tiling", "true")
    gsettings_set("org.mate.Marco.general", "audible-bell", "false")
    # Set Fonts
    gsettings_set("org.mate.interface", "document-font-name", "'Noto Sans 11'")
    gsettings_set("org.mate.interface", "font-name", "'Noto Sans 11'")
    gsettings_set("org.mate.interface", "monospace-font-name", "'Liberation Mono 11'")
    gsettings_set("org.mate.Marco.general", "titlebar-font", "'Noto Sans Bold 11'")
    dconf_write("/org/mate/terminal/profiles/default/use-theme-colors", "false")
    dconf_write("/org/mate/terminal/profiles/default/background-color", "'#00002B2A3635'")
    dconf_write("/org/mate/terminal/profiles/default/foreground-color", "'#838294939695'")
    # Icon theme
    if icon_theme_is_present():
        gsettings_set("org.mate.interface", "icon-theme", "Numix-Circle")
    # Fish config for mate-terminal
    if shutil.which("fish"):
        dconf_write("/org/mate/terminal/profiles/default/use-custom-command", "true")
        dconf_write("/org/mate/terminal/profiles/default/custom-command", "'{0}'".format(shutil.which("fish")))
    else:
        dconf_write("/org/mate/terminal/profiles/default/use-custom-command", "false")

    # System Monitor applet
    sysmon_id = subprocess.check_output(["dconf", "read", "/org/mate/panel/objects/system-monitor/applet-iid"]).decode()
    if "MultiLoadApplet" in sysmon_id:
        # To find the relocatable schemas: gsettings list-relocatable-schemas
        gsettings_set("org.mate.panel.applet.multiload:/org/mate/panel/objects/system-monitor/prefs/", "speed", "1000")
        gsettings_set("org.mate.panel.applet.multiload:/org/mate/panel/objects/system-monitor/prefs/", "view-diskload", "true")
        gsettings_set("org.mate.panel.applet.multiload:/org/mate/panel/objects/system-monitor/prefs/", "view-memload", "true")
        gsettings_set("org.mate.panel.applet.multiload:/org/mate/panel/objects/system-monitor/prefs/", "view-netload", "true")
        gsettings_set("org.mate.panel.applet.multiload:/org/mate/panel/objects/system-monitor/prefs/", "view-swapload", "true")


# PackageKit
# https://ask.fedoraproject.org/en/question/108524/clean-up-packagekit-cache-the-right-way/
if shutil.which("gnome-software"):
    gsettings_set("org.gnome.software", "download-updates", "false")
    gsettings_set("org.gnome.software", "download-updates-notify", "false")
    # Disable updates in Gnome Software for Silverblue / ostree.
    if os.path.isfile(os.path.join(os.sep, "run", "ostree-booted")):
        gsettings_set("org.gnome.software", "allow-updates", "false")


# Gnome specific settings
if shutil.which("gnome-session") or shutil.which("gnome-shell"):
    dconf_write("/org/gnome/gedit/preferences/editor/create-backup-copy", "false")
    dconf_write("/org/gnome/gedit/preferences/editor/display-line-numbers", "true")
    dconf_write("/org/gnome/gedit/preferences/editor/highlight-current-line", "true")
    dconf_write("/org/gnome/gedit/preferences/editor/bracket-matching", "true")
    dconf_write("/org/gnome/gedit/preferences/editor/auto-indent", "true")
    dconf_write("/org/gnome/gedit/preferences/editor/tabs-size", "uint32 4")
    dconf_write("/org/gtk/gtk4/settings/file-chooser/show-hidden", "true")
    dconf_write("/org/gtk/gtk4/settings/file-chooser/sort-directories-first", "true")
    dconf_write("/org/gnome/nautilus/preferences/executable-text-activation", "'ask'")
    dconf_write("/org/gnome/nautilus/preferences/click-policy", "'double'")
    dconf_write("/org/gnome/nautilus/preferences/default-folder-viewer", "'list-view'")
    dconf_write("/org/gnome/nautilus/list-view/use-tree-view", "true")
    dconf_write("/org/gnome/nautilus/list-view/default-zoom-level", "'small'")
    dconf_write("/org/gnome/nautilus/icon-view/default-zoom-level", "'small'")
    dconf_write("/org/gnome/nautilus/list-view/use-tree-view", "true")
    dconf_write("/org/gnome/nautilus/icon-view/captions", r"['size', 'none', 'none']")
    dconf_write("/org/gnome/nautilus/list-view/default-visible-columns", r"['name', 'size', 'type', 'date_modified']")
    dconf_write("/org/gnome/nautilus/compression/default-compression-format", "'7z'")
    gsettings_set("org.gnome.desktop.peripherals.touchpad", "tap-to-click", "true")
    gsettings_set("org.gnome.desktop.peripherals.touchpad", "natural-scroll", "false")
    gsettings_set("org.gnome.desktop.peripherals.touchpad", "click-method", "fingers")
    gsettings_set("org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-timeout", "3600")
    gsettings_set("org.gnome.settings-daemon.plugins.power", "sleep-inactive-ac-type", "nothing")
    gsettings_set("org.gnome.settings-daemon.plugins.power", "sleep-inactive-battery-timeout", "1800")
    gsettings_set("org.gnome.settings-daemon.plugins.power", "sleep-inactive-battery-type", "nothing")
    gsettings_set("org.gnome.desktop.screensaver", "lock-enabled", "false")
    if vmstatus or args.disable_powersave:
        gsettings_set("org.gnome.desktop.session", "idle-delay", "0")
    else:
        gsettings_set("org.gnome.desktop.session", "idle-delay", "300")
    dconf_write("/org/gnome/desktop/interface/font-antialiasing", "'rgba'")
    dconf_write("/org/gnome/desktop/interface/font-hinting", "'full'")
    gsettings_set("org.gnome.shell", "enabled-extensions", "['window-list@gnome-shell-extensions.gcampax.github.com', 'dash-to-dock@micxgx.gmail.com', 'dash-to-panel@jderose9.github.com', 'GPaste@gnome-shell-extensions.gnome.org', 'user-theme@gnome-shell-extensions.gcampax.github.com', 'appindicatorsupport@rgcjonas.gmail.com', 'system-monitor@gnome-shell-extensions.gcampax.github.com']")
    # Check current variable for gnome-system-monitor. If it doesn't exist, set the variable.
    gnome_desktop_read_list = subprocess.run("gsettings get org.gnome.shell favorite-apps", shell=True, check=False, stdout=subprocess.PIPE).stdout.decode().strip()
    gnome_desktop_search_list = ["firefox.desktop", "brave-browser.desktop", "chrome.desktop", 'thunderbird.desktop', 'nautilus.desktop', "ptyxis.desktop", "tilix.desktop", "org.kde.konsole.desktop", 'virt-manager.desktop', 'gnome-system-monitor.desktop', 'org.gnome.SystemMonitor.desktop']
    gnome_desktop_file_list = []
    for d in gnome_desktop_search_list:
        ds = CMimeSet.LocateDesktopFileName(d)
        if ds:
            gnome_desktop_file_list.append(ds)
    gsettings_set("org.gnome.shell", "favorite-apps", str(gnome_desktop_file_list))
    gsettings_set("org.gnome.desktop.wm.preferences", "button-layout", ":minimize,maximize,close")
    gsettings_set("org.gnome.desktop.wm.preferences", "num-workspaces", "1")
    gsettings_set("org.gnome.desktop.interface", "locate-pointer", "true")
    gsettings_set("org.gnome.mutter", "locate-pointer-key", "'Control_R'")
    dconf_write("/org/gnome/mutter/edge-tiling", "true")
    gsettings_set("org.gnome.desktop.datetime", "automatic-timezone", "true")
    gsettings_set("org.gnome.desktop.interface", "clock-format", "12h")
    gsettings_set("org.gnome.desktop.interface", "clock-show-date", "true")
    if icon_theme_is_present():
        gsettings_set("org.gnome.desktop.interface", "icon-theme", "'Numix-Circle'")
    gsettings_set("org.gnome.desktop.thumbnail-cache", "maximum-size", "100")
    gsettings_set("org.gnome.desktop.thumbnail-cache", "maximum-age", "90")
    gsettings_set("org.gnome.desktop.interface", "show-battery-percentage", "true")
    gsettings_set("org.gnome.desktop.interface", "clock-show-weekday", "true")
    gsettings_set("org.gnome.shell.overrides", "workspaces-only-on-primary", "false")
    gsettings_set("org.gnome.FileRoller.UI", "view-sidebar", "true")
    gsettings_set("org.gnome.FileRoller.FileSelector", "show-hidden", "true")
    gsettings_set("org.gnome.FileRoller.General", "compression-level", "maximum")
    # Disabled dash-to-dock until updated for Gnome 40.0
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/intellihide", "true")
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/multi-monitor", "true")
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/show-trash", "false")
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/dock-fixed", "false")
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/intellihide-mode", "'ALL_WINDOWS'")
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/require-pressure-to-show", "true")
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/pressure-threshold", "50.0")
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/hide-delay", "1.0")
    dconf_write("/org/gnome/shell/extensions/window-list/show-on-all-monitors", "true")
    # Set gnome-terminal scrollback
    dconf_write("/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-5262-4d8d-a863-c897e6d979b9/scrollback-unlimited", "true")
    # Fish config for gnome terminal
    if shutil.which("fish"):
        dconf_write("/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-5262-4d8d-a863-c897e6d979b9/custom-command", "'{0}'".format(shutil.which("fish")))

    # Set Fonts
    gsettings_set("org.gnome.desktop.interface", "document-font-name", "'Noto Sans 11'")
    gsettings_set("org.gnome.desktop.interface", "font-name", "'Noto Sans 11'")
    gsettings_set("org.gnome.desktop.interface", "monospace-font-name", "'Liberation Mono 11'")
    gsettings_set("org.gnome.desktop.wm.preferences", "titlebar-font", "'Noto Sans Bold 11'")
    # Dash to panel settings
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/panel-element-positions-monitors-sync", "true")

    dashtopanel_panel_positions = dashtopanel_panel_size = "'{"
    for x in range(args.screens):
        dashtopanel_panel_positions += f'"{x}":"TOP"'
        dashtopanel_panel_size += f'"{x}":24'
        if (x + 1) != args.screens:
            dashtopanel_panel_positions += ","
            dashtopanel_panel_size += ","
    dashtopanel_panel_positions += "}'"
    dashtopanel_panel_size += "}'"
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/panel-positions", dashtopanel_panel_positions)
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/panel-sizes", dashtopanel_panel_size)

    dconf_write("/org/gnome/shell/extensions/dash-to-panel/appicon-margin", "4")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/appicon-padding", "2")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/dot-position", "'BOTTOM'")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/dot-style-focused", "'DASHES'")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/dot-style-unfocused", "'DOTS'")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/primary-monitor", "1")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/multi-monitors", "true")
    # System Monitor
    dconf_write("/org/gnome/shell/extensions/system-monitor/show-swap", "false")

    # This section enables custom keybindings.
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "binding", "'<Super>e'")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "command", "'gnome-control-center display'")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "name", "'Gnome Display Settings'")
    # No Fish config for gnome-terminal, does not change folders when using "Open in Terminal"
    # Determine default archive program
    CMimeSet.HandlePredefines("archive", "org.gnome.FileRoller.desktop")

# Gnome Console
if shutil.which("kgx"):
    dconf_write("/org/gnome/Console/ignore-scrollback-limit", "true")
    dconf_write("/org/gnome/Console/custom-font", "'Liberation Mono 11'")

# Dconf editor
if shutil.which("dconf-editor"):
    dconf_write("/ca/desrt/dconf-editor/show-warning", "false")


# KDE/Plasma specific Settings
# https://askubuntu.com/questions/839647/gsettings-like-tools-for-kde#839773
# https://manned.org/kwriteconfig/d47c2de0
if shutil.which("kwriteconfig6") and shutil.which("plasma_session"):
    # Archiver settings
    CMimeSet.HandlePredefines("archive", "org.kde.ark.desktop")
    # Dolphin settings
    if shutil.which("dolphin"):
        kwriteconfig("dolphinrc", "General", "GlobalViewProps", "true")
        kwriteconfig("dolphinrc", "General", "OpenNewTabAfterLastTab", "true")
        kwriteconfig("dolphinrc", "General", "ShowFullPath", "true")
        kwriteconfig("dolphinrc", "General", "ShowZoomSlider", "false")
        kwriteconfig("dolphinrc", "IconsMode", "PreviewSize", "32")
        kwriteconfig("dolphinrc", "DetailsMode", "PreviewSize", "22")
        kwriteconfig("dolphinrc", "CompactMode", "PreviewSize", "16")
        subprocess.run('kwriteconfig6 --file dolphinrc --group "MainWindow" --group "Toolbar mainToolBar" --key ToolButtonStyle "IconOnly"', shell=True, check=False)
    # KDE Globals
    subprocess.run('kwriteconfig6 --file kdeglobals --group KDE --key SingleClick --type bool false', shell=True, check=False)
    os.makedirs("{0}/.kde/share/config".format(USERHOME), exist_ok=True)
    if icon_theme_is_present():
        subprocess.run('kwriteconfig6 --file kdeglobals --group Icons --key Theme "Numix-Circle"', shell=True, check=False)
        subprocess.run('kwriteconfig6 --file ~/.kde/share/config/kdeglobals --group Icons --key Theme "Numix-Circle"', shell=True, check=False)
    # Keyboard shortcuts
    kwriteconfig("kglobalshortcutsrc", "kwin", "Window Maximize", "Meta+Up,Meta+PgUp,Maximize Window")
    kwriteconfig("kglobalshortcutsrc", "kwin", "Window Minimize", "Meta+Down,Meta+PgDown,Minimize Window")
    # Workaround for kwriteconfig escaping \t as \\t. Without quotes, \t is escaped as only t.
    subprocess.run("sed -i 's@\\\\t@\\t@g' $HOME/.config/kglobalshortcutsrc", shell=True, check=False)
    kwriteconfig("kglobalshortcutsrc", "kwin", "Window Quick Tile Left", "Meta+Left,none,Quick Tile Window to the Left")
    kwriteconfig("kglobalshortcutsrc", "kwin", "Window Quick Tile Right", "Meta+Right,none,Quick Tile Window to the Right")
    kwriteconfig("kglobalshortcutsrc", "kwin", "Window Quick Tile Bottom", "Meta+PgDown,Meta+Down,Quick Tile Window to the Bottom")
    kwriteconfig("kglobalshortcutsrc", "kwin", "Window Quick Tile Top", "Meta+PgUp,Meta+Up,Quick Tile Window to the Top")
    kwriteconfig("kglobalshortcutsrc", "kwin", "ExposeAll", "Meta+C\tCtrl+F10\tLaunch (C),Ctrl+F10\tLaunch (C),Toggle Present Windows (All desktops)")
    kwriteconfig("kglobalshortcutsrc", "kwin", "TrackMouse", "Meta+Ctrl+Z,none,Track mouse")
    # Window Manager
    kwriteconfig("kwinrc", "Plugins", "kwin4_effect_translucencyEnabled", "false")
    kwriteconfig("kwinrc", "Plugins", "slidingpopupsEnabled", "false")
    kwriteconfig("kwinrc", "Plugins", "trackmouseEnabled", "true")
    kwriteconfig("kwinrc", "Windows", "ElectricBorderCornerRatio", "0.1")
    # Lock Screen and Power Management
    kwriteconfig("powerdevilrc", ["AC", "Display"], "DimDisplayWhenIdle", "false")
    if vmstatus or args.disable_powersave:
        kwriteconfig("powerdevilrc", ["AC", "Display"], "TurnOffDisplayWhenIdle", "false")
    else:
        kwriteconfig("powerdevilrc", ["AC", "Display"], "TurnOffDisplayWhenIdle", "true")
    kwriteconfig("powerdevilrc", ["AC", "Display"], "TurnOffDisplayIdleTimeoutWhenLockedSec", "20")
    kwriteconfig("powerdevilrc", ["AC", "SuspendAndShutdown"], "AutoSuspendAction", "0")
    kwriteconfig("powerdevilrc", ["AC", "SuspendAndShutdown"], "LidAction", "64")
    kwriteconfig("powerdevilrc", ["AC", "SuspendAndShutdown"], "PowerButtonAction", "8")

    kwriteconfig("powerdevilrc", ["Battery", "Display"], "DimDisplayWhenIdle", "false")
    kwriteconfig("powerdevilrc", ["Battery", "Display"], "TurnOffDisplayIdleTimeoutWhenLockedSec", "20")
    kwriteconfig("powerdevilrc", ["Battery", "SuspendAndShutdown"], "PowerButtonAction", "1")
    kwriteconfig("powerdevilrc", ["LowBattery", "Display"], "TurnOffDisplayIdleTimeoutWhenLockedSec", "0")
    subprocess.run('kwriteconfig6 --file kscreenlockerrc --group Daemon --key Autolock --type bool false', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file kscreenlockerrc --group Daemon --key LockOnResume --type bool false', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file kscreenlockerrc --group Daemon --key Timeout 10', shell=True, check=False)
    kwriteconfig("ksmserverrc", "General", "confirmLogout", "false")
    kwriteconfig("ksmserverrc", "General", "offerShutdown", "true")
    kwriteconfig("ksmserverrc", "General", "loginMode", "emptySession")
    # Clipboard settings
    kwriteconfig("klipperrc", "General", "MaxClipItems", "20")
    # Fonts
    kwriteconfig("kcmfonts", "General", "forceFontDPI", "96")
    # User Feedback
    kwriteconfig("PlasmaUserFeedback", "Global", "FeedbackLevel", "48")
    # System bell
    kwriteconfig("kaccessrc", "Bell", "SystemBell", "false")
    # Trash
    kwriteconfig("ktrashrc", "{0}/.local/share/Trash".format(USERHOME), "Days", "15")
    kwriteconfig("ktrashrc", "{0}/.local/share/Trash".format(USERHOME), "LimitReachedAction", "1")
    kwriteconfig("ktrashrc", "{0}/.local/share/Trash".format(USERHOME), "Percent", "2")
    kwriteconfig("ktrashrc", "{0}/.local/share/Trash".format(USERHOME), "UseSizeLimit", "true")
    kwriteconfig("ktrashrc", "{0}/.local/share/Trash".format(USERHOME), "UseTimeLimit", "true")

    # Notification settings
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/Textcompletion: no match" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/Textcompletion: no match" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/Textcompletion: no match" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/Trash: emptied" --key "Action" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/Trash: emptied" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/Trash: emptied" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/Trash: emptied" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/beep" --key "Action" "Execute"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/beep" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/beep" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/beep" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/catastrophe" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/catastrophe" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/catastrophe" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/catastrophe" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/fatalerror" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/fatalerror" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/fatalerror" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/fatalerror" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageCritical" --key "Action" "Taskbar"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageCritical" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageCritical" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageCritical" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageInformation" --key "Action" "Taskbar"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageInformation" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageInformation" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageInformation" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageWarning" --key "Action" "Taskbar"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageWarning" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageWarning" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageWarning" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageboxQuestion" --key "Action" "Taskbar"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageboxQuestion" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageboxQuestion" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/messageboxQuestion" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/notification" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/notification" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/notification" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/notification" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/printerror" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/printerror" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/printerror" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/printerror" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/startkde" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/startkde" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/startkde" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/warning" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/warning" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/warning" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma_workspace.notifyrc --group "Event/warning" --key "TTS" ""', shell=True, check=False)
    kwriteconfig("plasmanotifyrc", "Jobs", "PermanentPopups", "false")
    # Turn off monitors on lock screen
    # Currently not implemented in plasma6: https://bugs.kde.org/show_bug.cgi?id=481069
    kwriteconfig("ksmserver.notifyrc", "Event/locked", "Action", "Execute")
    kwriteconfig("ksmserver.notifyrc", "Event/locked", "Execute", os.path.join(sys.path[0], "whloffscreen.py"))
    kwriteconfig("ksmserver.notifyrc", "Event/unlocked", "Action", "Execute")
    kwriteconfig("ksmserver.notifyrc", "Event/unlocked", "Execute", '{0} $(pgrep -f "whloffscreen.py")'.format(shutil.which("kill")))

    if shutil.which("qdbus"):
        # Reload kwin.
        subprocess.run('qdbus org.kde.KWin /KWin reconfigure', shell=True, check=False)

    # Panel Positions
    # Config information and example: https://github.com/shalva97/kde-configuration-files
    # Convert kde config to kwriteconfig line: https://gist.github.com/shalva97/a705590f2c0e309374cccc7f6bd667cb
    if os.path.isfile(os.path.join(USERHOME, ".config", "plasmashellrc")):
        os.remove(os.path.join(USERHOME, ".config", "plasmashellrc"))
    subprocess.run('kwriteconfig6 --file plasmashellrc --group "PlasmaTransientsConfig" --key "PreloadWeight" "34"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasmashellrc --group "PlasmaViews" --group "Panel 2" --group "Defaults" --key "thickness" "28"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasmashellrc --group "PlasmaViews" --group "Panel 2" --key "floating" "0"', shell=True, check=False)

    # Panels
    if os.path.isfile(os.path.join(USERHOME, ".config", "plasma-org.kde.plasma.desktop-appletsrc")):
        os.remove(os.path.join(USERHOME, ".config", "plasma-org.kde.plasma.desktop-appletsrc"))
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "ActionPlugins" --group "0" --key "MiddleButton;NoModifier" "org.kde.paste"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "ActionPlugins" --group "0" --key "RightButton;NoModifier" "org.kde.contextmenu"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "ActionPlugins" --group "0" --key "wheel:Vertical;NoModifier" "org.kde.switchdesktop"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "ActionPlugins" --group "1" --key "RightButton;NoModifier" "org.kde.contextmenu"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "activityId" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "formfactor" "2"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "lastScreen" "0"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "location" "3"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "plugin" "org.kde.panel"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "wallpaperplugin" "org.kde.image"', shell=True, check=False)
    toppanel_appletgroup_id = 3
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.kickoff"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "100"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Configuration/General" --key "showAppsByName" "true"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "General" --key "favoritesPortedToKAstats" "true"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Shortcuts" --key "global" "Alt+F1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Shortcuts" --key "global" "Alt+F1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.pager"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "42"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.icontasks"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "42"'.format(toppanel_appletgroup_id), shell=True, check=False)

    plasma_desktop_string = ""
    plasma_desktop_search_list = ["firefox.desktop", "brave-browser.desktop", "chrome.desktop", 'thunderbird.desktop', 'kde.dolphin.desktop', "org.kde.konsole.desktop", 'virt-manager.desktop', 'org.kde.plasma-systemmonitor.desktop', 'gnome-system-monitor.desktop', 'gnome-system-monitor-kde.desktop', 'org.gnome.SystemMonitor.desktop']
    plasma_desktop_file_list = []
    for d in plasma_desktop_search_list:
        ds = CMimeSet.LocateDesktopFileName(d)
        if ds:
            plasma_desktop_file_list.append("applications:" + ds)
    plasma_desktop_string = ','.join(plasma_desktop_file_list)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "General" --key "launchers" "{1}"'.format(toppanel_appletgroup_id, plasma_desktop_string), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.marginsseparator"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "42"'.format(toppanel_appletgroup_id), shell=True, check=False)
    # System monitor applets
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemmonitor"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "100"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "chartFace" "org.kde.ksysguard.linechart"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "title" "CPU Usage"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "updateRateLimit" "1000"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "highPrioritySensorIds" "[\\"cpu/all/usage\\"]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "totalSensors" "[cpu/all/usage]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "cpu/all/usage" "85,255,255"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "historyAmount" "30"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "rangeAutoY" "false"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemmonitor"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "70"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "chartFace" "org.kde.ksysguard.linechart"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "title" "Memory Usage"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "updateRateLimit" "1000"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "highPrioritySensorIds" "[\\"memory/physical/usedPercent\\",\\"memory/swap/usedPercent\\"]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "memory/physical/usedPercent" "0,255,0"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "memory/swap/usedPercent" "255,0,0"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorLabels" --key "memory/physical/usedPercent" "Physical"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorLabels" --key "memory/swap/usedPercent" "Swap"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "rangeAutoY" "false"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemmonitor"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "100"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "chartFace" "org.kde.ksysguard.linechart"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "title" "I/O Rate"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "updateRateLimit" "1000"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "highPrioritySensorIds" "[\\"disk/all/read\\",\\"disk/all/write\\"]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "disk/all/read" "233,61,217"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "disk/all/write" "160,233,61"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "historyAmount" "30"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemmonitor"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "55"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "chartFace" "org.kde.ksysguard.linechart"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "title" "Network"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "updateRateLimit" "1000"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "highPrioritySensorIds" "[\\"network/all/download\\",\\"network/all/upload\\"]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "network/all/download" "0,255,0"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "network/all/upload" "255,170,255"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "historyAmount" "30"'.format(toppanel_appletgroup_id), shell=True, check=False)
    # Battery widget
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.battery"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    # System Tray
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemtray"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "57"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "SystrayContainmentId" "8"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.digitalclock"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "52"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.minimizeall"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "42"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)

    toppanel_appletgroup_list = []
    for x in range(3, toppanel_appletgroup_id):
        toppanel_appletgroup_list.append(str(x))
    toppanel_appletgroup_string = ';'.join(toppanel_appletgroup_list)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "General" --key "AppletOrder" "{0}"'.format(toppanel_appletgroup_string), shell=True, check=False)

    # Create multiple panels for each screen.
    extrapanel_id = 50
    extrapanel_appletid = extrapanel_id + 1
    for x in range(args.screens):
        extrapanel_appletid = extrapanel_id + 1
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "activityId" ""'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "formfactor" "2"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "immutability" "1"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "lastScreen" "{1}"'.format(extrapanel_id, x), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "location" "4"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "plugin" "org.kde.panel"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "wallpaperplugin" "org.kde.image"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --key "immutability" "1"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --key "plugin" "org.kde.plasma.taskmanager"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "groupedTaskVisualization" "1"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "maxStripes" "1"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "showOnlyCurrentScreen" "true"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "showOnlyCurrentDesktop" "false"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "showOnlyCurrentActivity" "false"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "launchers" ""'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "General" --key "AppletOrder" "{1}"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasmashellrc --group "PlasmaViews" --group "Panel {0}" --group "Defaults" --key "thickness" "24"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig6 --file plasmashellrc --group "PlasmaViews" --group "Panel {0}" --key "floating" "0"'.format(extrapanel_id), shell=True, check=False)
        extrapanel_id = extrapanel_appletid + 1

    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "activityId" ""', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "formfactor" "2"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "lastScreen" "0"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "location" "3"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "plugin" "org.kde.plasma.private.systemtray"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "wallpaperplugin" "org.kde.image"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "10" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "10" --key "plugin" "org.kde.kdeconnect"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "10" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "11" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "11" --key "plugin" "org.kde.plasma.devicenotifier"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "11" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "12" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "12" --key "plugin" "org.kde.plasma.printmanager"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "12" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "13" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "13" --key "plugin" "org.kde.plasma.volume"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "13" --group "Configuration" --group "General" --key "showVirtualDevices" "true"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "13" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "14" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "14" --key "plugin" "org.kde.plasma.notifications"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "14" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "15" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "15" --key "plugin" "org.kde.plasma.keyboardindicator"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "15" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "16" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "16" --key "plugin" "org.kde.plasma.vault"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "16" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "17" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "17" --key "plugin" "org.kde.plasma.nightcolorcontrol"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "17" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "20" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "20" --key "plugin" "org.kde.plasma.battery"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "20" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "21" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "21" --key "plugin" "org.kde.plasma.networkmanagement"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "21" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "9" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "9" --key "plugin" "org.kde.plasma.clipboard"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "9" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "General" --key "extraItems" "org.kde.plasma.networkmanagement,org.kde.plasma.clipboard,org.kde.kdeconnect,org.kde.plasma.devicenotifier,org.kde.plasma.printmanager,org.kde.plasma.bluetooth,org.kde.plasma.battery,org.kde.plasma.volume,org.kde.plasma.keyboardlayout,org.kde.kupapplet,org.kde.plasma.notifications,org.kde.plasma.keyboardindicator,org.kde.plasma.vault,org.kde.plasma.mediacontroller,org.kde.plasma.nightcolorcontrol"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "General" --key "knownItems" "org.kde.plasma.networkmanagement,org.kde.plasma.clipboard,org.kde.kdeconnect,org.kde.plasma.devicenotifier,org.kde.plasma.printmanager,org.kde.plasma.bluetooth,org.kde.plasma.battery,org.kde.plasma.volume,org.kde.plasma.keyboardlayout,org.kde.kupapplet,org.kde.plasma.notifications,org.kde.plasma.keyboardindicator,org.kde.plasma.vault,org.kde.plasma.mediacontroller,org.kde.plasma.nightcolorcontrol"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file plasma-org.kde.plasma.desktop-appletsrc --group "ScreenMapping" --key "itemsOnDisabledScreens" ""', shell=True, check=False)
    print('Use "nohup plasmashell --replace > /dev/null &" to refresh plasma shell.')
# Dolphin bookmarks
places_xml_path = os.path.join(USERHOME, ".local", "share", "user-places.xbel")
if os.path.isfile(places_xml_path):
    # Register the namespace to avoid nsX in namespace.
    ET.register_namespace('bookmark', 'http://www.freedesktop.org/standards/desktop-bookmarks')
    ET.register_namespace('kdepriv', 'http://www.kde.org/kdepriv')
    ET.register_namespace('mime', 'http://www.freedesktop.org/standards/shared-mime-info')

    # Get the xml.
    tree = ET.parse(places_xml_path)
    root = tree.getroot()
    # Bookmarks to delete.
    search_list = ["Videos", "Music", "Documents", "Downloads", "Pictures"]
    # Search through the bookmarks in the xml.
    for bmark in root.findall('bookmark'):
        # If a bookmark title matches the list, delete it.
        if bmark.find('title').text in search_list:
            root.remove(bmark)
    # Hide the "Search For" section
    for x in root.iter('GroupState-SearchFor-IsHidden'):
        x.text = "true"
    # Hide the "Recently" section
    for x in root.iter('GroupState-RecentlySaved-IsHidden'):
        x.text = "true"

    # Write the XML file
    xml_indent(root)
    tree.write(places_xml_path)

if shutil.which("konsole"):
    # Konsole settings
    kwriteconfig("konsolerc", "Desktop Entry", "DefaultProfile", "Profile 1.profile")
    kwriteconfig("konsolerc", "KonsoleWindow", "RememberWindowSize", "false")
    kwriteconfig("konsolerc", "TabBar", "CloseTabOnMiddleMouseButton", "true")
    kwriteconfig("konsolerc", "TabBar", "ExpandTabWidth", "true")
    kwriteconfig("konsolerc", "TabBar", "NewTabButton", "true")
    kwriteconfig("konsolerc", "TabBar", "TabBarPosition", "Top")
    kwriteconfig("konsolerc", "TabBar", "TabBarVisibility", "AlwaysShowTabBar")
    subprocess.run('kwriteconfig6 --file konsolerc --group "MainWindow" --group "Toolbar mainToolBar" --key ToolButtonStyle "IconOnly"', shell=True, check=False)
    subprocess.run('kwriteconfig6 --file konsolerc --group "MainWindow" --group "Toolbar sessionToolbar" --key ToolButtonStyle "IconOnly"', shell=True, check=False)
    # Konsole profile settings
    os.makedirs("{0}/.local/share/konsole".format(USERHOME), exist_ok=True)
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "General", "Name", "Profile 1")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "General", "Parent", "FALLBACK/")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "Scrolling", "HistoryMode", "2")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "Appearance", "ColorScheme", "Breeze")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "Appearance", "Font", "Liberation Mono,11,-1,5,50,0,0,0,0,0,Regular")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "General", "TerminalColumns", "85")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "General", "TerminalRows", "30")
    # Fish config for konsole
    if shutil.which("fish"):
        subprocess.run('kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile "Profile 1.profile"', shell=True, check=False)
        subprocess.run('kwriteconfig6 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Name "Profile 1"', shell=True, check=False)
        subprocess.run('kwriteconfig6 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Parent "FALLBACK/"', shell=True, check=False)
        subprocess.run('kwriteconfig6 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Command "$(which fish)"', shell=True, check=False)

# Konsole session
konsolesession_xml_path = os.path.join(USERHOME, ".local", "share", "kxmlgui5", "konsole", "sessionui.rc")
if os.path.isfile(konsolesession_xml_path):
    # Get the xml.
    tree = ET.parse(konsolesession_xml_path)
    root = tree.getroot()

    found_key = False
    # Elements to be added
    action_left_right = ET.Element("Action", {"name": "split-view-left-right"})
    action_top_bottom = ET.Element("Action", {"name": "split-view-top-bottom"})

    for element in root.iter():
        # Search for the toolbar tag.
        if "ToolBar" in element.tag:
            # Search for the name of the attribute, to see if it has already been added.
            for a in element.iter():
                if a.attrib.get('name') == "split-view-left-right":
                    found_key = True
            # If the existing key wasn't found, add it.
            if found_key is False:
                print("Modifying Konsole xml")
                # Insert the elements at the 0 and 1 position.
                element.insert(0, action_left_right)
                element.insert(1, action_top_bottom)

    # Write the XML file
    xml_indent(root)
    tree.write(konsolesession_xml_path, xml_declaration=True, encoding='UTF-8')


# Xfce settings
if shutil.which("xfconf-query") and shutil.which("xfce4-panel"):
    if icon_theme_is_present():
        xfconf("xsettings", "/Net/IconThemeName", "string", "Numix-Circle")
    xfconf("xfwm4", "/general/workspace_count", "int", "1")
    # Fonts
    xfconf("xfwm4", "/general/title_font", "string", "Noto Sans Bold 11")
    xfconf("xsettings", "/Gtk/FontName", "string", "Noto Sans 10")
    xfconf("xsettings", "/Gtk/MonospaceFontName", "string", "Liberation Mono 10")
    xfconf("xsettings", "/Xft/Antialias", "int", "1")
    xfconf("xsettings", "/Xft/Hinting", "int", "1")
    xfconf("xsettings", "/Xft/HintStyle", "string", "hintfull")
    xfconf("xsettings", "/Xft/RGBA", "string", "rgb")
    xfconf("xsettings", "/Xft/DPI", "int", "-1")
    # Launch Gnome services (for keyring)
    xfconf("xfce4-session", "/compat/LaunchGNOME", "bool", "true")
    # Keyboard Shortcuts
    xfconf("xfce4-keyboard-shortcuts", "/commands/custom/Super_L", "string", "xfce4-popup-whiskermenu")
    xfconf("xfce4-keyboard-shortcuts", "/commands/custom/Print", "string", "xfce4-screenshooter")
    # Lock Screen and Power Management
    xfconf("xfce4-screensaver", "/saver/enabled", "bool", "true")
    xfconf("xfce4-screensaver", "/saver/idle-activation/enabled", "bool", "false")
    xfconf("xfce4-screensaver", "/saver/fullscreen-inhibit", "bool", "true")
    if vmstatus or args.disable_powersave:
        xfconf("xfce4-power-manager", "/xfce4-power-manager/blank-on-ac", "int", "0")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-off", "int", "0")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-sleep", "int", "0")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-enabled", "bool", "false")
        # xfce-screensaver settings
        xfconf("xfce4-screensaver", "/lock/enabled", "bool", "false")
    else:
        xfconf("xfce4-screensaver", "/lock/enabled", "bool", "true")
        xfconf("xfce4-screensaver", "/saver/idle-activation/delay", "int", "10")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/blank-on-ac", "int", "10")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-off", "int", "10")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-sleep", "int", "10")

    # Thunar settings
    xfconf("thunar", "/default-view", "string", "ThunarDetailsView")
    xfconf("thunar", "/last-view", "string", "ThunarDetailsView")
    xfconf("thunar", "/last-icon-view-zoom-level", "string", "THUNAR_ZOOM_LEVEL_50_PERCENT")
    xfconf("thunar", "/last-details-view-zoom-level", "string", "THUNAR_ZOOM_LEVEL_38_PERCENT")
    xfconf("thunar", "/last-show-hidden", "bool", "true")
    xfconf("thunar", "/misc-show-delete-action", "bool", "true")
    xfconf("thunar", "/misc-single-click", "bool", "false")
    xfconf("thunar", "/misc-middle-click-in-tab", "bool", "true")
    xfconf("thunar", "/misc-date-style", "string", "THUNAR_DATE_STYLE_SHORT")
    # Task manager settings
    xfconf("xfce4-taskmanager", "/interface/show-all-processes", "bool", "true")
    xfconf("xfce4-taskmanager", "/interface/refresh-rate", "int", "1000")
    xfconf("xfce4-taskmanager", "/columns/column-uid", "bool", "true")

    # List panels
    # xfconf-query -c xfce4-panel -p /panels -lv
    # Setup 2 panels
    subprocess.run("xfconf-query -c xfce4-panel -p /panels -t int -s 1 -t int -s 2 -a", shell=True, check=False)
    # Panel settings
    xfconf("xfce4-panel", "/panels/panel-1/length", "int", "100")
    xfconf("xfce4-panel", "/panels/panel-2/length", "int", "100")
    xfconf("xfce4-panel", "/panels/panel-1/size", "int", "30")
    xfconf("xfce4-panel", "/panels/panel-2/size", "int", "30")
    xfconf("xfce4-panel", "/panels/panel-1/position-locked", "bool", "true")
    xfconf("xfce4-panel", "/panels/panel-2/position-locked", "bool", "true")
    xfconf("xfce4-panel", "/panels/panel-1/autohide-behavior", "int", "0")
    xfconf("xfce4-panel", "/panels/panel-2/autohide-behavior", "int", "0")
    # Put panel 1 on the top of the screen
    xfconf("xfce4-panel", "/panels/panel-1/position", "string", "p=6;x=0;y=0")
    # Put panel 2 on the bottom of the screen
    xfconf("xfce4-panel", "/panels/panel-2/position", "string", "p=10;x=0;y=0")

    # List plugins
    # xfconf-query -c xfce4-panel -p /plugins -lv
    # Delete all existing plugin ids
    subprocess.run("xfconf-query -c xfce4-panel -p /plugins --reset --recursive", shell=True, check=False)
    # Recreate plugin ids
    xfconf("xfce4-panel", "/plugins/plugin-1", "string", "applicationsmenu")
    xfconf("xfce4-panel", "/plugins/plugin-2", "string", "actions")
    xfconf("xfce4-panel", "/plugins/plugin-3", "string", "tasklist")
    xfconf("xfce4-panel", "/plugins/plugin-5", "string", "clock")
    xfconf("xfce4-panel", "/plugins/plugin-5/digital-format", "string", "%a %b %d | %r")
    xfconf("xfce4-panel", "/plugins/plugin-6", "string", "systray")
    xfconf("xfce4-panel", "/plugins/plugin-7", "string", "showdesktop")
    xfconf("xfce4-panel", "/plugins/plugin-8", "string", "separator")
    xfconf("xfce4-panel", "/plugins/plugin-9", "string", "whiskermenu")
    xfconf("xfce4-panel", "/plugins/plugin-10", "string", "directorymenu")
    xfconf("xfce4-panel", "/plugins/plugin-10/base-directory", "string", USERHOME)
    xfconf("xfce4-panel", "/plugins/plugin-11", "string", "separator")
    xfconf("xfce4-panel", "/plugins/plugin-11/expand", "bool", "true")
    xfconf("xfce4-panel", "/plugins/plugin-11/style", "int", "0")
    xfconf("xfce4-panel", "/plugins/plugin-12", "string", "systemload")
    xfconf("xfce4-panel", "/plugins/plugin-13", "string", "diskperf")
    xfconf("xfce4-panel", "/plugins/plugin-14", "string", "xfce4-clipman-plugin")
    xfconf("xfce4-panel", "/plugins/plugin-15", "string", "pulseaudio")
    # Panel shortcuts
    xfce_search_list = ["firefox.desktop", "brave-browser.desktop", "chrome.desktop", 'thunderbird.desktop', 'thunar.desktop', "ptyxis.desktop", "tilix.desktop", "xfce4-terminal.desktop", 'virt-manager.desktop', 'xfce4-taskmanager.desktop', 'gnome-system-monitor.desktop', 'org.gnome.SystemMonitor.desktop']
    xfce_file_list = []
    xfce_panel_string = ""
    xfce_panel_id = 20
    for d in xfce_search_list:
        ds = CMimeSet.LocateDesktopFileName(d)
        if ds:
            xfconf("xfce4-panel", "/plugins/plugin-{0}".format(xfce_panel_id), "string", "launcher")
            xfconf("xfce4-panel", "/plugins/plugin-{0}/items".format(xfce_panel_id), "string", ds, extra_options=['--force-array'])
            xfce_panel_string += " -t int -s {0}".format(xfce_panel_id)
            xfce_panel_id = xfce_panel_id + 1

    # List existing array
    # xfconf-query -c xfce4-panel -p /panels/panel-2/plugin-ids
    # Delete existing plugin arrays
    subprocess.run("xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -rR", shell=True, check=False)
    subprocess.run("xfconf-query -c xfce4-panel -p /panels/panel-2/plugin-ids -rR", shell=True, check=False)
    # Create plugins for panels
    subprocess.run("xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -t int -s 9 -t int -s 1 -t int{0} -s 11 -t int -s 12 -t int -s 13 -t int -s 14 -t int -s 15 -t int -s 6 -t int -s 5 -t int -s 2 --force-array --create".format(xfce_panel_string), shell=True, check=False)
    subprocess.run("xfconf-query -c xfce4-panel -p /panels/panel-2/plugin-ids -t int -s 3 --force-array --create", shell=True, check=False)

    # Reset the panel
    if subprocess.run(["pgrep", "xfce4-panel"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0:
        subprocess.Popen("xfce4-panel -r &", shell=True)
# Xfce4 terminal
if shutil.which("xfce4-terminal"):
    xfterm_config_basefolder = os.path.join(USERHOME, ".config", "xfce4", "terminal")
    xfterm_config_file = os.path.join(xfterm_config_basefolder, "terminalrc")
    os.makedirs(xfterm_config_basefolder, exist_ok=True)
    xfterm_config_text = """[Configuration]
MiscAlwaysShowTabs=FALSE
MiscBell=FALSE
MiscBellUrgent=FALSE
MiscBordersDefault=TRUE
MiscCursorBlinks=FALSE
MiscCursorShape=TERMINAL_CURSOR_SHAPE_BLOCK
MiscDefaultGeometry=80x24
MiscInheritGeometry=FALSE
MiscMenubarDefault=TRUE
MiscMouseAutohide=FALSE
MiscMouseWheelZoom=TRUE
MiscToolbarDefault=FALSE
MiscConfirmClose=TRUE
MiscCycleTabs=TRUE
MiscTabCloseButtons=TRUE
MiscTabCloseMiddleClick=TRUE
MiscTabPosition=GTK_POS_TOP
MiscHighlightUrls=TRUE
MiscMiddleClickOpensUri=FALSE
MiscCopyOnSelect=TRUE
MiscShowRelaunchDialog=TRUE
MiscRewrapOnResize=TRUE
MiscUseShiftArrowsToScroll=FALSE
MiscSlimTabs=FALSE
MiscNewTabAdjacent=FALSE
MiscSearchDialogOpacity=100
MiscShowUnsafePasteDialog=FALSE
Encoding=UTF-8
ScrollingUnlimited=TRUE
ColorPalette=#000000;#cc0000;#4e9a06;#c4a000;#3465a4;#75507b;#06989a;#d3d7cf;#555753;#ef2929;#8ae234;#fce94f;#739fcf;#ad7fa8;#34e2e2;#eeeeec
"""
    if shutil.which("fish"):
        xfterm_config_text += """RunCustomCommand=TRUE
CustomCommand={0}
""".format(shutil.which("fish"))
    with open(xfterm_config_file, 'w') as f:
        f.write(xfterm_config_text)

# lxqt
if shutil.which("lxqt-panel"):
    lxqt_config_basefolder = os.path.join(USERHOME, ".config", "lxqt")
    lxqt_configfile_panel = os.path.join(lxqt_config_basefolder, "panel.conf")
    os.makedirs(lxqt_config_basefolder, exist_ok=True)

    # Panel shortcuts
    lxqt_search_list = ["firefox.desktop", "brave-browser.desktop", "chrome.desktop", 'thunderbird.desktop', 'pcmanfm-qt.desktop', "konsole.desktop", "tilix.desktop", 'virt-manager.desktop', "org.gnome.SystemMonitor.desktop"]
    lxqt_file_list = []
    lxqt_panel_string = ""
    lxqt_panel_id = 0
    for d in lxqt_search_list:
        ds = CMimeSet.LocateDesktopFile(d)
        if ds:
            if lxqt_panel_id != 0:
                lxqt_panel_string += "\n"
            lxqt_panel_id += 1
            lxqt_panel_string += f"apps\\{lxqt_panel_id}\\desktop={ds[-1]}"
    lxqt_panel_string += f"\napps\\size={lxqt_panel_id}"

    # Panel config
    lxqt_configfile_panel_text = r"""[General]
__userfile__=true
iconTheme=
panels=panel1, panel2

[fancymenu]
alignment=Left
favorites\size=0
type=fancymenu

[mount]
alignment=Right
type=mount

[panel1]
alignment=-1
animation-duration=0
background-color=@Variant(\0\0\0\x43\0\xff\xff\0\0\0\0\0\0\0\0)
background-image=
desktop=0
font-color=@Variant(\0\0\0\x43\0\xff\xff\0\0\0\0\0\0\0\0)
hidable=false
hide-on-overlap=false
iconSize=22
lineCount=1
lockPanel=false
opacity=100
panelSize=32
plugins=fancymenu, quicklaunch, spacer, statusnotifier, tray, mount, volume, worldclock, showdesktop
position=Top
reserve-space=true
show-delay=0
visible-margin=true
width=100
width-percent=true

[panel2]
alignment=-1
animation-duration=0
background-color=@Variant(\0\0\0\x43\0\xff\xff\0\0\0\0\0\0\0\0)
background-image=
desktop=0
font-color=@Variant(\0\0\0\x43\0\xff\xff\0\0\0\0\0\0\0\0)
hidable=false
hide-on-overlap=false
iconSize=22
lineCount=1
lockPanel=false
opacity=100
panelSize=24
plugins=taskbar2
position=Bottom
reserve-space=true
show-delay=0
visible-margin=true
width=100
width-percent=true

[quicklaunch]
alignment=Left
{0}
type=quicklaunch

[showdesktop]
alignment=Right
type=showdesktop

[statusnotifier]
alignment=Right
type=statusnotifier

[taskbar]
alignment=Left
type=taskbar

[taskbar2]
alignment=Left
type=taskbar

[tray]
alignment=Right
type=tray

[volume]
alignment=Right
type=volume

[worldclock]
alignment=Right
autoRotate=true
customFormat="'<b>'h:mm:ss A'</b><br/><font size=\"-2\">'ddd, yyyy-MM-dd t'</font>'"
dateFormatType=custom
dateLongNames=false
datePadDay=false
datePosition=below
dateShowDoW=false
dateShowYear=false
defaultTimeZone=
formatType=custom-timeonly
showDate=false
showTimezone=false
showTooltip=false
showWeekNumber=true
timeAMPM=false
timePadHour=false
timeShowSeconds=false
timeZones\size=0
timezoneFormatType=iana
timezonePosition=below
type=worldclock
useAdvancedManualFormat=true
""".format(lxqt_panel_string)
    with open(lxqt_configfile_panel, 'w') as f:
        f.write(lxqt_configfile_panel_text)

    # lxqt config
    lxqt_configfile_general_text = r"""
[General]
__userfile__=true
icon_follow_color_scheme=true
icon_theme=Numix-Circle
theme=KDE-Plasma
tool_bar_icon_size=24
wallpaper_override=false

[Qt]
font="Noto Sans,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
style=Fusion
"""
    lxqt_configfile_general = os.path.join(lxqt_config_basefolder, "lxqt.conf")
    with open(lxqt_configfile_general, 'w') as f:
        f.write(lxqt_configfile_general_text)

# Pcmanfm-qt
if shutil.which("pcmanfm-qt"):
    pcmanfm_basefolder = os.path.join(USERHOME, ".config", "pcmanfm-qt", "lxqt")
    pcmanfm_configfile = os.path.join(pcmanfm_basefolder, "settings.conf")
    os.makedirs(pcmanfm_basefolder, exist_ok=True)

    # Preserve case: https://stackoverflow.com/a/23836686 and https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.optionxform
    config = configparser.RawConfigParser()
    config.optionxform = str

    config.sections()
    # Read the ini file
    config.read(pcmanfm_configfile)

    # Config modifications
    # Behavior
    config['Behavior'] = {}
    config['Behavior']['BookmarkOpenMethod'] = "current_tab"
    config['Behavior']['ConfirmDelete'] = "true"
    config['Behavior']['ConfirmTrash'] = "true"
    config['Behavior']['NoUsbTrash'] = "true"
    config['Behavior']['SingleWindowMode'] = "true"
    config['Behavior']['UseTrash'] = "false"
    # Folderview
    config['FolderView'] = {}
    config['FolderView']['BackupAsHidden'] = 'false'
    config['FolderView']['BigIconSize'] = '48'
    config['FolderView']['Mode'] = 'detailed'
    config['FolderView']['NoItemTooltip'] = 'false'
    config['FolderView']['ScrollPerPixel'] = 'true'
    config['FolderView']['ShadowHidden'] = 'true'
    config['FolderView']['ShowFilter'] = 'false'
    config['FolderView']['ShowFullNames'] = 'true'
    config['FolderView']['ShowHidden'] = 'true'
    config['FolderView']['SidePaneIconSize'] = '24'
    config['FolderView']['SmallIconSize'] = '24'
    config['FolderView']['SortCaseSensitive'] = 'false'
    config['FolderView']['SortFolderFirst'] = 'true'
    config['FolderView']['SortHiddenLast'] = 'false'
    config['FolderView']['SortOrder'] = 'ascending'
    config['FolderView']['ThumbnailIconSize'] = '128'
    # Search
    config['Search'] = {}
    config['Search']['searchContentCaseInsensitive'] = 'true'
    config['Search']['searchContentRegexp'] = 'true'
    config['Search']['searchNameCaseInsensitive'] = 'true'
    config['Search']['searchNameRegexp'] = 'true'
    config['Search']['searchRecursive'] = 'true'
    config['Search']['searchhHidden'] = 'true'
    # System
    config['System'] = {}
    if shutil.which("konsole"):
        config['System']['Terminal'] = "konsole"
    elif shutil.which("tilix"):
        config['System']['Terminal'] = "tilix"
    # Thumbnail
    config['Thumbnail'] = {}
    config['Thumbnail']['MaxThumbnailFileSize'] = "8192"
    config['Thumbnail']['ShowThumbnails'] = "true"
    config['Thumbnail']['ThumbnailLocalFilesOnly'] = "false"
    # Window
    config['Window'] = {}
    config['Window']['AlwaysShowTabs'] = "true"
    config['Window']['FixedHeight'] = "600"
    config['Window']['FixedWidth'] = "800"
    config['Window']['LastWindowMaximized'] = "false"
    config['Window']['PathBarButtons'] = "true"
    config['Window']['RememberWindowSize'] = "true"
    config['Window']['ReopenLastTabs'] = "true"
    config['Window']['ShowMenuBar'] = "true"
    config['Window']['ShowTabClose'] = "true"
    config['Window']['SidePaneMode'] = "places"
    config['Window']['SidePaneVisible'] = "true"
    config['Window']['SplitView'] = "false"
    config['Window']['SwitchToNewTab'] = "true"

    # Write the ini file
    with open(pcmanfm_configfile, 'w') as configfile:
        config.write(configfile)

# xscreensaver
if shutil.which("xscreensaver"):
    xscreensaver_file = os.path.join(USERHOME, ".xscreensaver")
    # Panel config
    xscreensaver_text = """
timeout:        0:10:00
cycle:          0:10:00
lock:           False
lockTimeout:    0:00:00
passwdTimeout:  0:00:30
verbose:        False
splash:         True
splashDuration: 0:00:05
demoCommand:    xscreensaver-settings
nice:           10
fade:           True
unfade:         False
fadeSeconds:    0:00:10
ignoreUninstalledPrograms:False
dpmsQuickOff:   True
dpmsStandby:    0:15:00
dpmsSuspend:    0:15:00
dpmsOff:        0:15:00
selected:       -1
"""
    if vmstatus or args.disable_powersave:
        xscreensaver_text += """
mode:           off
dpmsEnabled:    False
"""
    else:
        xscreensaver_text += """
mode:           blank
dpmsEnabled:    True
"""
    with open(xscreensaver_file, 'w') as f:
        f.write(xscreensaver_text)
