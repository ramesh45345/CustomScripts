#!/usr/bin/env python3
"""Set Desktop Settings"""

# Python includes
import argparse
import os
import pathlib
import subprocess
import shutil
import sys
import xml.etree.ElementTree as ET
# Custom includes
import CFunc
import CMimeSet

print("Running {0}".format(__file__))

### Functions ###
def icon_theme_is_present():
    """Check if the preferred icon theme (Numix-Circle) is present."""
    theme_exists = False
    if os.path.isdir("/usr/share/icons/Numix-Circle") or os.path.isdir("/usr/local/share/icons/Numix-Circle"):
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
def kwriteconfig(file: str, group: str, key: str, value: str):
    """Set KDE configs using kwriteconfig5."""
    status = subprocess.run(['kwriteconfig5', '--file', file, "--group", group, "--key", key, value], check=False).returncode
    if status != 0:
        print("ERROR, failed to run: kwriteconfig5 --file {0} --group {1} --key {2} {3}".format(file, group, key, value))
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
def firefox_modify_settings(setting: str, value: str, prefsjs_filepath: str):
    """Modify a setting in the firefox prefs.js file."""
    # Read prefs.js
    with open(prefsjs_filepath, 'r') as f:
        prefs_txt = f.read()
    # Find the preference in prefs.js.
    if '"{0}"'.format(setting) in prefs_txt:
        # If the preference exists, change the setting in the file.
        subprocess.run('''sed -i 's/user_pref("{0}",.*);/user_pref("{0}", {1});/' {2}'''.format(setting, value, prefsjs_filepath), shell=True, check=False)
    else:
        # If the pref doesn't exist, add to the bottom.
        with open(prefsjs_filepath, 'a') as f:
            f.write('user_pref("{0}", {1});\n'.format(setting, value))
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
CMimeSet.HandlePredefines("text", "code-oss.desktop")
CMimeSet.HandlePredefines("text", "code.desktop")

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
    gsettings_set("com.gexperts.Tilix.Settings", "warn-vte-config-issue", "false")
    gsettings_set("com.gexperts.Tilix.Settings", "terminal-title-style", "small")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/login-shell", "true")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/scrollback-unlimited", "true")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/terminal-bell", "'icon'")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/use-theme-colors", "false")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/background-color", "'#263238'")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/foreground-color", "'#A1B0B8'")
    dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/palette", "['#252525', '#FF5252', '#C3D82C', '#FFC135', '#42A5F5', '#D81B60', '#00ACC1', '#F5F5F5', '#708284', '#FF5252', '#C3D82C', '#FFC135', '#42A5F5', '#D81B60', '#00ACC1', '#F5F5F5']")
    # Fish config for tilix
    if shutil.which("fish"):
        dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/use-custom-command", "true")
        dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/custom-command", "'{0}'".format(shutil.which("fish")))
    else:
        dconf_write("/com/gexperts/Tilix/profiles/2b7c4080-0ddd-46c5-8f23-563fd3ba789d/use-custom-command", "false")


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
    gsettings_set("org.mate.interface", "font-name", "'Roboto 11'")
    gsettings_set("org.mate.interface", "monospace-font-name", "'Liberation Mono 11'")
    gsettings_set("org.mate.Marco.general", "titlebar-font", "'Roboto Bold 11'")
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
if shutil.which("gnome-session"):
    gsettings_set("org.gnome.gedit.preferences.editor", "create-backup-copy", "false")
    gsettings_set("org.gnome.gedit.preferences.editor", "display-line-numbers", "true")
    gsettings_set("org.gnome.gedit.preferences.editor", "highlight-current-line", "true")
    gsettings_set("org.gnome.gedit.preferences.editor", "bracket-matching", "true")
    gsettings_set("org.gnome.gedit.preferences.editor", "auto-indent", "true")
    gsettings_set("org.gnome.gedit.preferences.editor", "tabs-size", "4")
    gsettings_set("org.gtk.Settings.FileChooser", "show-hidden", "true")
    gsettings_set("org.gtk.Settings.FileChooser", "sort-directories-first", "true")
    gsettings_set("org.gnome.nautilus.preferences", "executable-text-activation", "ask")
    gsettings_set("org.gnome.nautilus.preferences", "click-policy", "double")
    gsettings_set("org.gnome.nautilus.preferences", "default-folder-viewer", "list-view")
    gsettings_set("org.gnome.nautilus.list-view", "use-tree-view", "true")
    gsettings_set("org.gnome.nautilus.list-view", "default-zoom-level", "small")
    gsettings_set("org.gnome.nautilus.icon-view", "default-zoom-level", "small")
    gsettings_set("org.gnome.nautilus.list-view", "use-tree-view", "true")
    gsettings_set("org.gnome.nautilus.icon-view", "captions", "['size', 'none', 'none']")
    gsettings_set("org.gnome.nautilus.list-view", "default-visible-columns", "['name', 'size', 'type', 'date_modified']")
    gsettings_set("org.gnome.nautilus.compression", "default-compression-format", "'7z'")
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
    gsettings_set("org.gnome.settings-daemon.plugins.xsettings", "antialiasing", "rgba")
    gsettings_set("org.gnome.settings-daemon.plugins.xsettings", "hinting", "full")
    gsettings_set("org.gnome.desktop.interface", "text-scaling-factor", "1.0")
    gsettings_set("org.gnome.desktop.interface", "clock-show-date", "true")
    gsettings_set("org.gnome.shell", "enabled-extensions", "['window-list@gnome-shell-extensions.gcampax.github.com', 'dash-to-dock@micxgx.gmail.com', 'dash-to-panel@jderose9.github.com', 'GPaste@gnome-shell-extensions.gnome.org', 'user-theme@gnome-shell-extensions.gcampax.github.com', 'sound-output-device-chooser@kgshank.net', 'volume-mixer@evermiss.net', 'appindicatorsupport@rgcjonas.gmail.com']")
    # Check current variable for gnome-system-monitor. If it doesn't exist, set the variable.
    gnome_desktop_read_list = subprocess.run("gsettings get org.gnome.shell favorite-apps", shell=True, check=False, stdout=subprocess.PIPE).stdout.decode().strip()
    if "gnome-system-monitor.desktop" not in gnome_desktop_read_list:
        gnome_desktop_search_list = ["firefox.desktop", "UngoogledChromium.desktop", "chrome.desktop", 'evolution.desktop', 'nautilus.desktop', "tilix.desktop", 'virt-manager.desktop', 'gnome-system-monitor.desktop']
        gnome_desktop_file_list = []
        for d in gnome_desktop_search_list:
            ds = CMimeSet.LocateDesktopFileName(d)
            if ds:
                gnome_desktop_file_list.append(ds)
        gsettings_set("org.gnome.shell", "favorite-apps", str(gnome_desktop_file_list))
    gsettings_set("org.gnome.desktop.wm.preferences", "button-layout", ":minimize,maximize,close")
    gsettings_set("org.gnome.desktop.interface", "locate-pointer", "true")
    gsettings_set("org.gnome.mutter", "locate-pointer-key", "'Control_R'")
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
    gsettings_set("org.gnome.gnome-system-monitor", "show-whose-processes", "all")
    gsettings_set("org.freedesktop.Tracker.Miner.Files", "crawling-interval", "-2")
    gsettings_set("org.freedesktop.Tracker.Miner.Files", "enable-monitors", "false")
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
    # Set Fonts
    gsettings_set("org.gnome.desktop.interface", "document-font-name", "'Noto Sans 11'")
    gsettings_set("org.gnome.desktop.interface", "font-name", "'Roboto 11'")
    gsettings_set("org.gnome.desktop.interface", "monospace-font-name", "'Liberation Mono 11'")
    gsettings_set("org.gnome.desktop.wm.preferences", "titlebar-font", "'Roboto Bold 11'")
    # Dash to panel settings
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/panel-positions", r"""'{"0":"TOP"}'""")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/panel-sizes", r"""'{"0":32}'""")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/appicon-margin", "4")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/appicon-padding", "2")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/dot-position", "'BOTTOM'")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/dot-style-focused", "'DASHES'")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/dot-style-unfocused", "'DOTS'")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/primary-monitor", "1")
    dconf_write("/org/gnome/shell/extensions/dash-to-panel/multi-monitors", "false")

    # This section enables custom keybindings.
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "binding", "'<Super>e'")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "command", "'gnome-control-center display'")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "name", "'Gnome Display Settings'")
    # No Fish config for gnome-terminal, does not change folders when using "Open in Terminal"
    # Determine default archive program
    CMimeSet.HandlePredefines("archive", "org.gnome.FileRoller.desktop")


# KDE/Plasma specific Settings
# https://askubuntu.com/questions/839647/gsettings-like-tools-for-kde#839773
# https://manned.org/kwriteconfig/d47c2de0
if shutil.which("kwriteconfig5") and shutil.which("plasma_session"):
    # Dolphin settings
    if shutil.which("dolphin"):
        kwriteconfig("dolphinrc", "General", "GlobalViewProps", "true")
        kwriteconfig("dolphinrc", "General", "ShowZoomSlider", "false")
        kwriteconfig("dolphinrc", "IconsMode", "PreviewSize", "32")
        kwriteconfig("dolphinrc", "DetailsMode", "PreviewSize", "22")
        kwriteconfig("dolphinrc", "CompactMode", "PreviewSize", "16")
    # KDE Globals
    subprocess.run('kwriteconfig5 --file kdeglobals --group KDE --key SingleClick --type bool false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kdeglobals --group General    --key XftSubPixel "rgb"', shell=True, check=False)
    os.makedirs("{0}/.kde/share/config".format(USERHOME), exist_ok=True)
    if icon_theme_is_present():
        subprocess.run('kwriteconfig5 --file kdeglobals --group Icons --key Theme "Numix-Circle"', shell=True, check=False)
        subprocess.run('kwriteconfig5 --file ~/.kde/share/config/kdeglobals --group Icons --key Theme "Numix-Circle"', shell=True, check=False)
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
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group HandleButtonEvents --key lidAction 64', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group HandleButtonEvents --key powerButtonAction 8', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group HandleButtonEvents --key powerDownAction 16', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group HandleButtonEvents --key triggerLidActionWhenExternalMonitorPresent false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group DimDisplay --key idleTime --delete', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group Battery --group HandleButtonEvents --key lidAction 1', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group Battery --group HandleButtonEvents --key powerButtonAction 1', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group Battery --group HandleButtonEvents --key powerDownAction 16', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group Battery --group HandleButtonEvents --key triggerLidActionWhenExternalMonitorPresent false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group Battery --group DimDisplay --key idleTime --delete', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group DPMSControl --key idleTime 300', shell=True, check=False)
    if vmstatus or args.disable_powersave:
        subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group DPMSControl --key idleTime 300000', shell=True, check=False)
    else:
        subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group DPMSControl --key idleTime 600', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kscreenlockerrc --group Daemon --key Autolock --type bool false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kscreenlockerrc --group Daemon --key LockOnResume --type bool false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kscreenlockerrc --group Daemon --key Timeout 10', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file ksmserverrc --group General --key confirmLogout false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file ksmserverrc --group General --key offerShutdown true', shell=True, check=False)
    # Konsole settings
    kwriteconfig("konsolerc", "Desktop Entry", "DefaultProfile", "Profile 1.profile")
    kwriteconfig("konsolerc", "KonsoleWindow", "SaveGeometryOnExit", "false")
    kwriteconfig("konsolerc", "TabBar", "CloseTabOnMiddleMouseButton", "true")
    kwriteconfig("konsolerc", "TabBar", "ExpandTabWidth", "true")
    kwriteconfig("konsolerc", "TabBar", "NewTabButton", "true")
    kwriteconfig("konsolerc", "TabBar", "TabBarPosition", "Top")
    kwriteconfig("konsolerc", "TabBar", "TabBarVisibility", "AlwaysShowTabBar")
    subprocess.run('kwriteconfig5 --file konsolerc --group "MainWindow" --group "Toolbar mainToolBar" --key ToolButtonStyle "IconOnly"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file konsolerc --group "MainWindow" --group "Toolbar sessionToolbar" --key ToolButtonStyle "IconOnly"', shell=True, check=False)
    # Konsole profile settings
    os.makedirs("{0}/.local/share/konsole".format(USERHOME), exist_ok=True)
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "General", "Name", "Profile 1")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "General", "Parent", "FALLBACK/")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "Scrolling", "HistoryMode", "2")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "Appearance", "ColorScheme", "Breeze")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "Appearance", "Font", "Liberation Mono,11,-1,5,50,0,0,0,0,0,Regular")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "General", "TerminalColumns", "85")
    kwriteconfig(os.path.join(USERHOME, ".local", "share", "konsole", "Profile 1.profile"), "General", "TerminalRows", "30")
    # Clipboard settings
    kwriteconfig("klipperrc", "General", "MaxClipItems", "20")
    # Fonts
    kwriteconfig("kcmfonts", "General", "forceFontDPI", "96")
    # User Feedback
    kwriteconfig("PlasmaUserFeedback", "Global", "FeedbackLevel", "48")
    # System bell
    kwriteconfig("kaccessrc", "Bell", "SystemBell", "false")

    # Notification settings
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/Textcompletion: no match" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/Textcompletion: no match" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/Textcompletion: no match" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/Trash: emptied" --key "Action" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/Trash: emptied" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/Trash: emptied" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/Trash: emptied" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/beep" --key "Action" "Execute"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/beep" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/beep" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/beep" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/catastrophe" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/catastrophe" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/catastrophe" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/catastrophe" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/fatalerror" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/fatalerror" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/fatalerror" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/fatalerror" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageCritical" --key "Action" "Taskbar"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageCritical" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageCritical" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageCritical" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageInformation" --key "Action" "Taskbar"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageInformation" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageInformation" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageInformation" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageWarning" --key "Action" "Taskbar"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageWarning" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageWarning" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageWarning" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageboxQuestion" --key "Action" "Taskbar"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageboxQuestion" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageboxQuestion" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/messageboxQuestion" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/notification" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/notification" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/notification" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/notification" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/printerror" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/printerror" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/printerror" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/printerror" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/startkde" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/startkde" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/startkde" --key "TTS" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/warning" --key "Action" "Popup"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/warning" --key "Execute" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/warning" --key "Logfile" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma_workspace.notifyrc --group "Event/warning" --key "TTS" ""', shell=True, check=False)
    kwriteconfig("plasmanotifyrc", "Jobs", "PermanentPopups", "false")
    # Turn off monitors on lock screen
    kwriteconfig("ksmserver.notifyrc", "Event/locked", "Action", "Execute")
    kwriteconfig("ksmserver.notifyrc", "Event/locked", "Execute", os.path.join(sys.path[0], "whloffscreen.py"))
    kwriteconfig("ksmserver.notifyrc", "Event/unlocked", "Action", "Execute")
    kwriteconfig("ksmserver.notifyrc", "Event/unlocked", "Execute", '{0} $(pgrep -f "whloffscreen.py")'.format(shutil.which("kill")))

    # Fish config for konsole
    if shutil.which("fish"):
        subprocess.run('kwriteconfig5 --file konsolerc --group "Desktop Entry" --key DefaultProfile "Profile 1.profile"', shell=True, check=False)
        subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Name "Profile 1"', shell=True, check=False)
        subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Parent "FALLBACK/"', shell=True, check=False)
        subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Command "$(which fish)"', shell=True, check=False)

    if shutil.which("qdbus"):
        # Reload kwin.
        subprocess.run('qdbus org.kde.KWin /KWin reconfigure', shell=True, check=False)

    # Panel Positions
    # Config information and example: https://github.com/shalva97/kde-configuration-files
    # Convert kde config to kwriteconfig line: https://gist.github.com/shalva97/a705590f2c0e309374cccc7f6bd667cb
    if os.path.isfile(os.path.join(USERHOME, ".config", "plasmashellrc")):
        os.remove(os.path.join(USERHOME, ".config", "plasmashellrc"))
    subprocess.run('kwriteconfig5 --file plasmashellrc --group "PlasmaTransientsConfig" --key "PreloadWeight" "34"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasmashellrc --group "PlasmaViews" --group "Panel 2" --group "Defaults" --key "thickness" "28"', shell=True, check=False)

    # Panels
    if os.path.isfile(os.path.join(USERHOME, ".config", "plasma-org.kde.plasma.desktop-appletsrc")):
        os.remove(os.path.join(USERHOME, ".config", "plasma-org.kde.plasma.desktop-appletsrc"))
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "ActionPlugins" --group "0" --key "MiddleButton;NoModifier" "org.kde.paste"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "ActionPlugins" --group "0" --key "RightButton;NoModifier" "org.kde.contextmenu"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "ActionPlugins" --group "0" --key "wheel:Vertical;NoModifier" "org.kde.switchdesktop"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "ActionPlugins" --group "1" --key "RightButton;NoModifier" "org.kde.contextmenu"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "activityId" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "formfactor" "2"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "lastScreen" "0"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "location" "3"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "plugin" "org.kde.panel"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --key "wallpaperplugin" "org.kde.image"', shell=True, check=False)
    toppanel_appletgroup_id = 3
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.kickoff"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "100"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Configuration/General" --key "showAppsByName" "true"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "General" --key "favoritesPortedToKAstats" "true"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Shortcuts" --key "global" "Alt+F1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Shortcuts" --key "global" "Alt+F1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.pager"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "42"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.icontasks"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "42"'.format(toppanel_appletgroup_id), shell=True, check=False)

    plasma_desktop_string = ""
    plasma_desktop_search_list = ["firefox.desktop", "UngoogledChromium.desktop", "chrome.desktop", 'thunderbird.desktop', 'kde.dolphin.desktop', "tilix.desktop", "org.kde.konsole.desktop", 'virt-manager.desktop', 'org.kde.plasma-systemmonitor.desktop']
    plasma_desktop_file_list = []
    for d in plasma_desktop_search_list:
        ds = CMimeSet.LocateDesktopFileName(d)
        if ds:
            plasma_desktop_file_list.append("applications:" + ds)
    plasma_desktop_string = ','.join(plasma_desktop_file_list)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "General" --key "launchers" "{1}"'.format(toppanel_appletgroup_id, plasma_desktop_string), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.marginsseparator"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "42"'.format(toppanel_appletgroup_id), shell=True, check=False)
    # System monitor applets
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemmonitor"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "100"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "chartFace" "org.kde.ksysguard.linechart"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "title" "CPU Usage"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "updateRateLimit" "1000"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "highPrioritySensorIds" "[\\"cpu/all/usage\\"]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "totalSensors" "[cpu/all/usage]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "cpu/all/usage" "85,255,255"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "historyAmount" "30"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "rangeAutoY" "false"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemmonitor"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "70"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "chartFace" "org.kde.ksysguard.linechart"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "title" "Memory Usage"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "updateRateLimit" "1000"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "highPrioritySensorIds" "[\\"memory/physical/usedPercent\\",\\"memory/swap/usedPercent\\"]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "memory/physical/usedPercent" "0,255,0"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "memory/swap/usedPercent" "255,0,0"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorLabels" --key "memory/physical/usedPercent" "Physical"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorLabels" --key "memory/swap/usedPercent" "Swap"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "rangeAutoY" "false"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemmonitor"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "100"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "chartFace" "org.kde.ksysguard.linechart"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "title" "I/O Rate"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "updateRateLimit" "1000"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "highPrioritySensorIds" "[\\"disk/all/read\\",\\"disk/all/write\\"]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "disk/all/read" "233,61,217"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "disk/all/write" "160,233,61"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "historyAmount" "30"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemmonitor"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "55"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "chartFace" "org.kde.ksysguard.linechart"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "title" "Network"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Appearance" --key "updateRateLimit" "1000"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "Sensors" --key "highPrioritySensorIds" "[\\"network/all/download\\",\\"network/all/upload\\"]"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "network/all/download" "0,255,0"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "SensorColors" --key "network/all/upload" "255,170,255"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --group "org.kde.ksysguard.linechart" --group "General" --key "historyAmount" "30"'.format(toppanel_appletgroup_id), shell=True, check=False)
    # Battery widget
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.battery"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    # System Tray
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.systemtray"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "57"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "SystrayContainmentId" "8"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.digitalclock"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "52"'.format(toppanel_appletgroup_id), shell=True, check=False)
    toppanel_appletgroup_id = toppanel_appletgroup_id + 1
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "immutability" "1"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --key "plugin" "org.kde.plasma.minimizeall"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Applets" --group "{0}" --group "Configuration" --key "PreloadWeight" "42"'.format(toppanel_appletgroup_id), shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)

    toppanel_appletgroup_list = []
    for x in range(3, toppanel_appletgroup_id):
        toppanel_appletgroup_list.append(str(x))
    toppanel_appletgroup_string = ';'.join(toppanel_appletgroup_list)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "2" --group "General" --key "AppletOrder" "{0}"'.format(toppanel_appletgroup_string), shell=True, check=False)

    # Create multiple panels for each screen.
    extrapanel_id = 50
    extrapanel_appletid = extrapanel_id + 1
    for x in range(args.screens):
        extrapanel_appletid = extrapanel_id + 1
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "activityId" ""'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "formfactor" "2"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "immutability" "1"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "lastScreen" "{1}"'.format(extrapanel_id, x), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "location" "4"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "plugin" "org.kde.panel"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "wallpaperplugin" "org.kde.image"'.format(extrapanel_id), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --key "immutability" "1"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --key "plugin" "org.kde.plasma.taskmanager"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "maxStripes" "1"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "showOnlyCurrentScreen" "true"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "Applets" --group "{1}" --group "Configuration" --group "General" --key "launchers" ""'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --group "General" --key "AppletOrder" "{1}"'.format(extrapanel_id, extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasmashellrc --group "PlasmaViews" --group "Panel {0}" --group "Defaults" --key "thickness" "24"'.format(extrapanel_id), shell=True, check=False)
        extrapanel_appletid = extrapanel_appletid + 1
        # Use desktop view instead of folder view.
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "activityId" "aecca071-25ec-4ff1-be05-9f6468e20095"'.format(extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "formfactor" "0"'.format(extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "immutability" "1"'.format(extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "lastScreen" "{1}"'.format(extrapanel_appletid, x), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "location" "0"'.format(extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "plugin" "org.kde.desktopcontainment"'.format(extrapanel_appletid), shell=True, check=False)
        subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "{0}" --key "wallpaperplugin" "org.kde.image"'.format(extrapanel_appletid), shell=True, check=False)
        extrapanel_id = extrapanel_appletid + 1

    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "activityId" ""', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "formfactor" "2"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "lastScreen" "0"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "location" "3"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "plugin" "org.kde.plasma.private.systemtray"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --key "wallpaperplugin" "org.kde.image"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "10" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "10" --key "plugin" "org.kde.kdeconnect"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "10" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "11" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "11" --key "plugin" "org.kde.plasma.devicenotifier"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "11" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "12" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "12" --key "plugin" "org.kde.plasma.printmanager"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "12" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "13" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "13" --key "plugin" "org.kde.plasma.volume"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "13" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "14" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "14" --key "plugin" "org.kde.plasma.notifications"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "14" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "15" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "15" --key "plugin" "org.kde.plasma.keyboardindicator"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "15" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "16" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "16" --key "plugin" "org.kde.plasma.vault"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "16" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "17" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "17" --key "plugin" "org.kde.plasma.nightcolorcontrol"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "17" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "20" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "20" --key "plugin" "org.kde.plasma.battery"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "20" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "21" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "21" --key "plugin" "org.kde.plasma.networkmanagement"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "21" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "9" --key "immutability" "1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "9" --key "plugin" "org.kde.plasma.clipboard"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Applets" --group "9" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "Configuration" --key "PreloadWeight" "42"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "General" --key "extraItems" "org.kde.plasma.networkmanagement,org.kde.plasma.clipboard,org.kde.kdeconnect,org.kde.plasma.devicenotifier,org.kde.plasma.printmanager,org.kde.plasma.bluetooth,org.kde.plasma.battery,org.kde.plasma.volume,org.kde.plasma.keyboardlayout,org.kde.kupapplet,org.kde.plasma.notifications,org.kde.plasma.keyboardindicator,org.kde.plasma.vault,org.kde.plasma.mediacontroller,org.kde.plasma.nightcolorcontrol"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "Containments" --group "8" --group "General" --key "knownItems" "org.kde.plasma.networkmanagement,org.kde.plasma.clipboard,org.kde.kdeconnect,org.kde.plasma.devicenotifier,org.kde.plasma.printmanager,org.kde.plasma.bluetooth,org.kde.plasma.battery,org.kde.plasma.volume,org.kde.plasma.keyboardlayout,org.kde.kupapplet,org.kde.plasma.notifications,org.kde.plasma.keyboardindicator,org.kde.plasma.vault,org.kde.plasma.mediacontroller,org.kde.plasma.nightcolorcontrol"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file plasma-org.kde.plasma.desktop-appletsrc --group "ScreenMapping" --key "itemsOnDisabledScreens" ""', shell=True, check=False)
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


# Xfce settings
if shutil.which("xfconf-query") and shutil.which("xfce4-panel"):
    if icon_theme_is_present():
        xfconf("xsettings", "/Net/IconThemeName", "string", "Numix-Circle")
    xfconf("xfwm4", "/general/workspace_count", "int", "1")
    # Fonts
    xfconf("xfwm4", "/general/title_font", "string", "Roboto Bold 11")
    xfconf("xsettings", "/Gtk/FontName", "string", "Roboto 10")
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
    if vmstatus or args.disable_powersave:
        xfconf("xfce4-power-manager", "/xfce4-power-manager/blank-on-ac", "int", "0")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-off", "int", "0")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-sleep", "int", "0")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-enabled", "bool", "false")
        # xfce-screensaver settings
        xfconf("xfce4-screensaver", "/lock/enabled", "bool", "false")
        xfconf("xfce4-screensaver", "/saver/enabled", "bool", "false")
    else:
        xfconf("xfce4-power-manager", "/xfce4-power-manager/blank-on-ac", "int", "10")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-off", "int", "10")
        xfconf("xfce4-power-manager", "/xfce4-power-manager/dpms-on-ac-sleep", "int", "10")

    # Thunar settings
    xfconf("xfce4-panel", "/default-view", "string", "ThunarDetailsView")
    xfconf("xfce4-panel", "/last-view", "string", "ThunarDetailsView")
    xfconf("xfce4-panel", "/last-icon-view-zoom-level", "string", "THUNAR_ZOOM_LEVEL_75_PERCENT")
    xfconf("xfce4-panel", "/last-show-hidden", "bool", "true")
    xfconf("xfce4-panel", "/misc-show-delete-action", "bool", "true")
    xfconf("xfce4-panel", "/misc-single-click", "bool", "false")
    xfconf("xfce4-panel", "/misc-middle-click-in-tab", "bool", "true")

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
    xfconf("xfce4-panel", "/plugins/plugin-20", "string", "launcher")
    xfconf("xfce4-panel", "/plugins/plugin-20/items", "string", "firefox.desktop", extra_options=['--force-array'])
    xfconf("xfce4-panel", "/plugins/plugin-21", "string", "launcher")
    if os.path.isfile("/usr/share/applications/Thunar.desktop"):
        xfconf("xfce4-panel", "/plugins/plugin-21/items", "string", "Thunar.desktop", extra_options=['--force-array'])
    else:
        xfconf("xfce4-panel", "/plugins/plugin-21/items", "string", "thunar.desktop", extra_options=['--force-array'])
    xfconf("xfce4-panel", "/plugins/plugin-22", "string", "launcher")
    xfconf("xfce4-panel", "/plugins/plugin-22/items", "string", "xfce4-terminal.desktop", extra_options=['--force-array'])
    xfconf("xfce4-panel", "/plugins/plugin-23", "string", "launcher")
    xfconf("xfce4-panel", "/plugins/plugin-23/items", "string", "com.gexperts.Tilix.desktop", extra_options=['--force-array'])

    # List existing array
    # xfconf-query -c xfce4-panel -p /panels/panel-2/plugin-ids
    # Delete existing plugin arrays
    subprocess.run("xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -rR", shell=True, check=False)
    subprocess.run("xfconf-query -c xfce4-panel -p /panels/panel-2/plugin-ids -rR", shell=True, check=False)
    # Create plugins for panels
    subprocess.run("xfconf-query -c xfce4-panel -p /panels/panel-1/plugin-ids -t int -s 9 -t int -s 1 -t int -s 20 -t int -s 21 -t int -s 22 -t int -s 23 -t int -s 11 -t int -s 12 -t int -s 13 -t int -s 14 -t int -s 15 -t int -s 6 -t int -s 5 -t int -s 2 --force-array --create", shell=True, check=False)
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


# Firefox settings.
# If prefs.js for firefox was created, set the profile information. Search for natively installed firefox, flatpak firefox, and flatpak librewolf.
firefox_profiles_paths = [os.path.join(USERHOME, ".mozilla", "firefox"), os.path.join(USERHOME, ".var", "app", "org.mozilla.firefox", ".mozilla", "firefox"), os.path.join(USERHOME, ".var", "app", "io.gitlab.librewolf-community", ".librewolf")]
for ff_path in firefox_profiles_paths:
    if os.path.isdir(ff_path):
        # Find profile folders
        with os.scandir(ff_path) as it:
            for entry in it:
                firefox_profilefolder = os.path.join(ff_path, entry.name)
                if "default" in entry.name and os.path.isdir(firefox_profilefolder):
                    prefsjs_file = os.path.join(firefox_profilefolder, "prefs.js")
                    # Find a prefs.js in a potential profile folder
                    if os.path.isfile(prefsjs_file):
                        os.chdir(firefox_profilefolder)
                        print("Editing Firefox preferences in {0}.".format(prefsjs_file))
                        firefox_modify_settings("general.autoScroll", "true", prefsjs_file)
                        firefox_modify_settings("extensions.pocket.enabled", "false", prefsjs_file)
                        firefox_modify_settings("browser.tabs.drawInTitlebar", "true", prefsjs_file)
                        firefox_modify_settings("browser.aboutConfig.showWarning", "false", prefsjs_file)
                        firefox_modify_settings("browser.download.useDownloadDir", "false", prefsjs_file)
                        firefox_modify_settings("browser.startup.page", "3", prefsjs_file)
                        firefox_modify_settings("app.shield.optoutstudies.enabled", "false", prefsjs_file)
                        firefox_modify_settings("browser.newtabpage.activity-stream.showSponsored", "false", prefsjs_file)
                        firefox_modify_settings("browser.newtabpage.enabled", "false", prefsjs_file)
                        firefox_modify_settings("browser.startup.homepage", '"about:blank"', prefsjs_file)
                        # DNS-over-HTTPS
                        firefox_modify_settings("network.trr.mode", "2", prefsjs_file)
                        firefox_modify_settings("network.trr.bootstrapAddress", '"1.1.1.1"', prefsjs_file)
                        # Disable notifications
                        firefox_modify_settings("dom.webnotifications.enabled", "false", prefsjs_file)
                        # Autoplay (5 blocks audio and video for all sites by default)
                        firefox_modify_settings("media.autoplay.default", "5", prefsjs_file)
                        # Sponsored suggest
                        firefox_modify_settings("browser.urlbar.suggest.quicksuggest.sponsored", "false", prefsjs_file)
                        if "librewolf" in ff_path:
                            firefox_modify_settings("network.dns.disableIPv6", "false", prefsjs_file)
                            firefox_modify_settings("webgl.disabled", "false", prefsjs_file)
                            firefox_modify_settings("identity.fxaccounts.enabled", "true", prefsjs_file)
                            firefox_modify_settings("privacy.clearOnShutdown.history", "false", prefsjs_file)
                            firefox_modify_settings("privacy.clearOnShutdown.downloads", "false", prefsjs_file)
                            firefox_modify_settings("privacy.sanitize.sanitizeOnShutdown", "false", prefsjs_file)
                            firefox_modify_settings("security.OCSP.require", "false", prefsjs_file)
