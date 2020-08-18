#!/usr/bin/env python3
"""Set Desktop Settings"""

# Python includes
import argparse
import os
import pathlib
import subprocess
import shutil
# Custom includes
import CFunc

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
    if setting in prefs_txt:
        # If the preference exists, change the setting in the file.
        subprocess.run('''sed -i 's/user_pref("{0}",.*);/user_pref("{0}", {1});/' {2}'''.format(setting, value, prefsjs_filepath), shell=True, check=False)
    else:
        # If the pref doesn't exist, add to the bottom.
        with open(prefsjs_filepath, 'a') as f:
            f.write('user_pref("{0}", {1});\n'.format(setting, value))


# Get arguments
parser = argparse.ArgumentParser(description='Set Desktop Settings.')
parser.add_argument("-p", "--disable_powersave", help='Force turning off powersave modes (like for VMs).', action="store_true")
args = parser.parse_args()

# Exit if root.
CFunc.is_root(False)

# Get VM State
vmstatus = CFunc.getvmstate()

# Home folder
USERHOME = str(pathlib.Path.home())


### Begin Code ###
# Editor settings
if shutil.which("code"):
    subprocess.run("xdg-mime default code.desktop text/x-shellscript", shell=True, check=True)
    subprocess.run("xdg-mime default code.desktop text/plain", shell=True, check=True)
elif shutil.which("atom"):
    subprocess.run("xdg-mime default atom.desktop text/x-shellscript", shell=True, check=True)
    subprocess.run("xdg-mime default atom.desktop text/plain", shell=True, check=True)

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
    gsettings_set("org.gnome.shell", "enabled-extensions", "['window-list@gnome-shell-extensions.gcampax.github.com', 'dash-to-dock@micxgx.gmail.com', 'GPaste@gnome-shell-extensions.gnome.org', 'user-theme@gnome-shell-extensions.gcampax.github.com', 'shell-volume-mixer@derhofbauer.at', 'TopIcons@phocean.net', 'ubuntu-appindicators@ubuntu.com', 'donotdisturb@kylecorry31.github.io']")
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
    dconf_write("/org/gnome/shell/extensions/dash-to-dock/intellihide", "true")
    dconf_write("/org/gnome/shell/extensions/dash-to-dock/multi-monitor", "true")
    # Blocked by https://github.com/micheleg/dash-to-dock/issues/1025
    # dconf_write("/org/gnome/shell/extensions/dash-to-dock/show-mounts", "false")
    dconf_write("/org/gnome/shell/extensions/dash-to-dock/show-trash", "false")
    dconf_write("/org/gnome/shell/extensions/dash-to-dock/dock-fixed", "false")
    dconf_write("/org/gnome/shell/extensions/dash-to-dock/intellihide-mode", "'ALL_WINDOWS'")
    dconf_write("/org/gnome/shell/extensions/dash-to-dock/require-pressure-to-show", "true")
    dconf_write("/org/gnome/shell/extensions/dash-to-dock/pressure-threshold", "50.0")
    dconf_write("/org/gnome/shell/extensions/dash-to-dock/hide-delay", "1.0")
    dconf_write("/org/gnome/shell/extensions/window-list/show-on-all-monitors", "true")
    # Set gnome-terminal scrollback
    dconf_write("/org/gnome/terminal/legacy/profiles:/:b1dcc9dd-5262-4d8d-a863-c897e6d979b9/scrollback-unlimited", "true")
    # Set Fonts
    gsettings_set("org.gnome.desktop.interface", "document-font-name", "'Noto Sans 11'")
    gsettings_set("org.gnome.desktop.interface", "font-name", "'Roboto 11'")
    gsettings_set("org.gnome.desktop.interface", "monospace-font-name", "'Liberation Mono 11'")
    gsettings_set("org.gnome.desktop.wm.preferences", "titlebar-font", "'Roboto Bold 11'")

    # This section enables custom keybindings.
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", "['/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/']")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "binding", "'<Super>e'")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "command", "'gnome-control-center display'")
    gsettings_set("org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/", "name", "'Gnome Display Settings'")
    # No Fish config for gnome-terminal, does not change folders when using "Open in Terminal"
    if shutil.which("file-roller"):
        # Run "xdg-mime query default <mime type>" to get current association.
        subprocess.run("xdg-mime default org.gnome.FileRoller.desktop application/x-7z-compressed", shell=True, check=False)
        subprocess.run("xdg-mime default org.gnome.FileRoller.desktop application/x-xz-compressed-tar", shell=True, check=False)
        subprocess.run("xdg-mime default org.gnome.FileRoller.desktop application/zip", shell=True, check=False)
        subprocess.run("xdg-mime default org.gnome.FileRoller.desktop application/x-compressed-tar", shell=True, check=False)
        subprocess.run("xdg-mime default org.gnome.FileRoller.desktop application/x-bzip-compressed-tar", shell=True, check=False)
        subprocess.run("xdg-mime default org.gnome.FileRoller.desktop application/x-tar", shell=True, check=False)
        subprocess.run("xdg-mime default org.gnome.FileRoller.desktop application/x-xz", shell=True, check=False)


# KDE/Plasma specific Settings
# https://askubuntu.com/questions/839647/gsettings-like-tools-for-kde#839773
# https://manned.org/kwriteconfig/d47c2de0
if shutil.which("kwriteconfig5") and shutil.which("plasma_session"):
    # Dolphin settings
    if shutil.which("dolphin"):
        subprocess.run('kwriteconfig5 --file dolphinrc --group General --key GlobalViewProps --type bool true', shell=True, check=False)
    # KDE Globals
    subprocess.run('kwriteconfig5 --file kdeglobals --group KDE --key SingleClick --type bool false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kdeglobals --group General    --key XftSubPixel "rgb"', shell=True, check=False)
    # kwriteconfig5 --file kdeglobals --group General    --key fixed "Liberation Mono,10,-1,5,50,0,0,0,0,0,Regular"
    os.makedirs("{0}/.kde/share/config".format(USERHOME), exist_ok=True)
    if icon_theme_is_present():
        subprocess.run('kwriteconfig5 --file kdeglobals --group Icons --key Theme "Numix-Circle"', shell=True, check=False)
        subprocess.run('kwriteconfig5 --file ~/.kde/share/config/kdeglobals --group Icons --key Theme "Numix-Circle"', shell=True, check=False)
    # Keyboard shortcuts
    subprocess.run('kwriteconfig5 --file kglobalshortcutsrc --group kwin --key MoveZoomDown ",Meta+Down,Move Zoomed Area Downwards"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kglobalshortcutsrc --group kwin --key MoveZoomLeft ",Meta+Left,Move Zoomed Area to Left"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kglobalshortcutsrc --group kwin --key MoveZoomRight ",Meta+Right,Move Zoomed Area to Right"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kglobalshortcutsrc --group kwin --key MoveZoomUp ",Meta+Up,Move Zoomed Area Upwards"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "Window Maximize" "Meta+Up\tMeta+Down,none,Maximize Window"', shell=True, check=False)
    # Workaround for kwriteconfig escaping \t as \\t. Without quotes, \t is escaped as only t.
    subprocess.run("sed -i 's@\\\\t@\\t@g' $HOME/.config/kglobalshortcutsrc", shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "Window Quick Tile Left" "Meta+Left,none,Quick Tile Window to the Left"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "Window Quick Tile Right" "Meta+Right,none,Quick Tile Window to the Right"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kglobalshortcutsrc --group kwin --key "Show Desktop" "Meta+m,none,Show Desktop"', shell=True, check=False)
    # Lock Screen and Power Management
    if vmstatus or args.disable_powersave:
        subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group DPMSControl --key idleTime 300000', shell=True, check=False)
    else:
        subprocess.run('kwriteconfig5 --file powermanagementprofilesrc --group AC --group DPMSControl --key idleTime 600', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kscreenlockerrc --group Daemon --key Autolock --type bool false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kscreenlockerrc --group Daemon --key LockOnResume --type bool false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file kscreenlockerrc --group Daemon --key Timeout 10', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file ksmserverrc --group General --key confirmLogout false', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file ksmserverrc --group General --key offerShutdown true', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file konsolerc --group "Desktop Entry" --key DefaultProfile "Profile 1.profile"', shell=True, check=False)
    os.makedirs("{0}/.local/share/konsole".format(USERHOME), exist_ok=True)
    subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Name "Profile 1"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Parent "FALLBACK/"', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "Scrolling" --key HistoryMode 2', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "Appearance" --key ColorScheme Solarized', shell=True, check=False)
    subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "Appearance" --key Font "Liberation Mono,11,-1,5,50,0,0,0,0,0,Regular"', shell=True, check=False)

    # Fish config for konsole
    if shutil.which("fish"):
        subprocess.run('kwriteconfig5 --file konsolerc --group "Desktop Entry" --key DefaultProfile "Profile 1.profile"', shell=True, check=False)
        subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Name "Profile 1"', shell=True, check=False)
        subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Parent "FALLBACK/"', shell=True, check=False)
        subprocess.run('kwriteconfig5 --file "$HOME/.local/share/konsole/Profile 1.profile" --group "General" --key Command "$(which fish)"', shell=True, check=False)

    if shutil.which("qdbus"):
        # Reload kwin.
        subprocess.run('qdbus org.kde.KWin /KWin reconfigure', shell=True, check=False)


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


# Firefox settings.
# If prefs.js for firefox was created, set the profile information.
firefox_profiles_path = os.path.join(USERHOME, ".mozilla", "firefox")
if os.path.isdir(firefox_profiles_path):
    # Find profile folders
    with os.scandir(firefox_profiles_path) as it:
        for entry in it:
            firefox_profilefolder = os.path.join(firefox_profiles_path, entry.name)
            if "default" in entry.name and os.path.isdir(firefox_profilefolder):
                prefsjs_file = os.path.join(firefox_profilefolder, "prefs.js")
                # Find a prefs.js in a potential profile folder
                if os.path.isfile(prefsjs_file):
                    os.chdir(firefox_profilefolder)
                    print("Editing Firefox preferences in {0}.".format(prefsjs_file))
                    firefox_modify_settings("general.autoScroll", "true", prefsjs_file)
                    firefox_modify_settings("extensions.pocket.enabled", "false", prefsjs_file)
                    firefox_modify_settings("browser.tabs.drawInTitlebar", "true", prefsjs_file)
                    firefox_modify_settings("general.warnOnAboutConfig", "false", prefsjs_file)
                    firefox_modify_settings("browser.download.useDownloadDir", "false", prefsjs_file)
                    firefox_modify_settings("app.shield.optoutstudies.enabled", "false", prefsjs_file)
                    firefox_modify_settings("browser.newtabpage.activity-stream.showSponsored", "false", prefsjs_file)
                    # DNS-over-HTTPS
                    firefox_modify_settings("network.trr.mode", "2", prefsjs_file)
                    firefox_modify_settings("network.trr.bootstrapAddress", '"1.1.1.1"', prefsjs_file)
                    # Disable notifications
                    firefox_modify_settings("dom.webnotifications.enabled", "false", prefsjs_file)
                    # Autoplay (5 blocks audio and video for all sites by default)
                    firefox_modify_settings("media.autoplay.default", "5", prefsjs_file)

                    # Install firefox gnome theme.
                    if os.getenv('XDG_CURRENT_DESKTOP') == "GNOME":
                        firefox_gnometheme_path = os.path.join(USERHOME, "firefox-gnome-theme")
                        CFunc.gitclone("https://github.com/rafaelmardojai/firefox-gnome-theme/", firefox_gnometheme_path)
                        if os.path.isdir(firefox_gnometheme_path):
                            subprocess.run("{0}/scripts/install.sh -p {1}".format(firefox_gnometheme_path, entry.name), shell=True, check=False)
