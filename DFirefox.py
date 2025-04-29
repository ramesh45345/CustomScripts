#!/usr/bin/env python3
"""Set Firefox Settings"""

# Python includes
import functools
import os
import subprocess
# Custom includes
import CFunc

# Disable buffered stdout (to ensure prints are in order)
print = functools.partial(print, flush=True)

# Home folder
USERNAMEVAR, USERGROUP, USERHOME = CFunc.getnormaluser()

firefox_profiles_paths = [os.path.join(USERHOME, ".mozilla", "firefox"),
                          os.path.join(USERHOME, ".var", "app", "org.mozilla.firefox", ".mozilla", "firefox"),
                          os.path.join(USERHOME, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),
                          os.path.join(USERHOME, ".librewolf"),
                          os.path.join(USERHOME, ".var", "app", "io.gitlab.librewolf-community", ".librewolf")]
for ff_path in firefox_profiles_paths:
    if os.path.isdir(ff_path):
        # Find profile folders
        with os.scandir(ff_path) as it:
            for entry in it:
                firefox_profilefolder = os.path.join(ff_path, entry.name)
                # If prefs.js exists, then its the correct folder.
                prefsjs_file = os.path.join(firefox_profilefolder, "prefs.js")
                if "default" in entry.name and os.path.isdir(firefox_profilefolder) and os.path.isfile(prefsjs_file):
                    # print("Editing Firefox preferences in {0}.".format(prefsjs_file))
                    print(f"\nRunning arkenfox on {firefox_profilefolder}\n")

                    if CFunc.is_windows():
                        arkenfox_updater = os.path.join(firefox_profilefolder, "updater.bat")
                        arkenfox_cleaner = os.path.join(firefox_profilefolder, "prefsCleaner.bat")
                        CFunc.downloadfile("https://raw.githubusercontent.com/arkenfox/user.js/master/prefsCleaner.bat", firefox_profilefolder)
                        CFunc.downloadfile("https://raw.githubusercontent.com/arkenfox/user.js/master/updater.bat", firefox_profilefolder)
                    else:
                        arkenfox_updater = os.path.join(firefox_profilefolder, "updater.sh")
                        arkenfox_cleaner = os.path.join(firefox_profilefolder, "prefsCleaner.sh")
                        CFunc.downloadfile("https://raw.githubusercontent.com/arkenfox/user.js/master/prefsCleaner.sh", firefox_profilefolder)
                        CFunc.downloadfile("https://raw.githubusercontent.com/arkenfox/user.js/master/updater.sh", firefox_profilefolder)
                        os.chmod(arkenfox_updater, 0o777)
                        os.chmod(arkenfox_cleaner, 0o777)

                    # Add overrides
                    # https://github.com/arkenfox/user.js/wiki/2.1-User.js
                    # https://github.com/yokoffing/Betterfox/blob/main/user.js
                    userjs_file = os.path.join(firefox_profilefolder, "user-overrides.js")
                    userjs_text = """
/** GFX ***/
user_pref("gfx.webrender.all", true);
// https://wiki.archlinux.org/title/Firefox#Hardware_video_acceleration
// https://fedoraproject.org/wiki/Firefox_Hardware_acceleration
user_pref("layers.gpu-process.enabled", true);
user_pref("media.hardware-video-decoding.enabled", true);
user_pref("gfx.canvas.accelerated", true);
/** MOZILLA ***/
user_pref("browser.tabs.firefox-view", false);
user_pref("privacy.resistFingerprinting.letterboxing", false);
user_pref("privacy.resistFingerprinting", false);
user_pref("privacy.window.maxInnerHeight", 0);
user_pref("privacy.window.maxInnerWidth", 0);
/** MOZILLA UI ***/
user_pref("browser.preferences.moreFromMozilla", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
/*** POCKET ***/
user_pref("extensions.pocket.enabled", false);
/** DOWNLOADS ***/
user_pref("browser.download.useDownloadDir", false);

user_pref("dom.webnotifications.enabled", false);
user_pref("general.autoScroll", true);
user_pref("browser.tabs.drawInTitlebar", true);
user_pref("browser.aboutConfig.showWarning", false);
user_pref("browser.startup.page", 3);
// Autoplay (5 blocks audio and video for all sites by default)
user_pref("media.autoplay.default", 5);
// Enable vaapi
user_pref("media.ffmpeg.vaapi.enabled", true);
// Password and autofill
user_pref("extensions.formautofill.addresses.enabled", false);
user_pref("extensions.formautofill.creditCards.enabled", false);
user_pref("signon.rememberSignons", false);
// Search
user_pref("browser.urlbar.suggest.quicksuggest.nonsponsored", false);
user_pref("browser.urlbar.suggest.quicksuggest.sponsored", false);
// Toolbar
user_pref("identity.fxaccounts.toolbar.pxiToolbarEnabled.monitorEnabled", false);
user_pref("identity.fxaccounts.toolbar.pxiToolbarEnabled.relayEnabled", false);
user_pref("identity.fxaccounts.toolbar.pxiToolbarEnabled.vpnEnabled", false);

/*** From Librewolf ***/
user_pref("privacy.clearOnShutdown.cache", false);
user_pref("privacy.clearOnShutdown.cookies", false);
user_pref("privacy.clearOnShutdown.download", false);
user_pref("privacy.clearOnShutdown.formdata", false);
user_pref("privacy.clearOnShutdown.history", false);
user_pref("privacy.clearOnShutdown.offlineApps", false);
user_pref("privacy.clearOnShutdown.openWindows", false);
user_pref("privacy.clearOnShutdown.sessions", false);
user_pref("privacy.clearOnShutdown.siteSettings", false);
user_pref("privacy.sanitize.sanitizeOnShutdown", false);
user_pref("identity.fxaccounts.enabled", true);
user_pref("network.dns.disableIPv6", false);
user_pref("privacy.resistFingerprinting.autoDeclineNoUserInputCanvasPrompts", false);
user_pref("webgl.disabled", false);
user_pref("security.OCSP.require", false);
"""
                    # Write the user-overrides.js file.
                    print("Writing Firefox user-overrides.js preferences in {0}.".format(userjs_file))
                    with open(userjs_file, 'w') as f:
                        f.write(userjs_text)

                    if CFunc.is_windows():
                        # Run updater
                        subprocess.run([arkenfox_updater, "-unattended", "-singlebackup"], shell=False, check=True)
                        # Run cleaner
                        subprocess.run([arkenfox_cleaner, "-unattended"], shell=False, check=True)
                    else:
                        # Run updater
                        subprocess.run([arkenfox_updater, "-s", "-b"], shell=False, check=True)
                        # Run cleaner
                        subprocess.run([arkenfox_cleaner, "-s"], shell=False, check=True)
