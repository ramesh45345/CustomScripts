#!/usr/bin/env python3
"""Install Media Player configuration."""

# Python includes.
import os
import shutil
import subprocess
# Custom includes
import CFunc

print("Running {0}".format(__file__))

# Get user details.
usernamevar, usergroup, userhome = CFunc.getnormaluser()

# Exit if root.
CFunc.is_root(False)

########################## Functions ##########################
def cmd_silent(cmd=list):
    """Run a command silently"""
    status = subprocess.run(cmd, check=False, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    return status


######################### Begin Code ##########################

### Smplayer ###
smplayer_fp_cmd = ["flatpak", "run", "--command=smplayer", "info.smplayer.SMPlayer", "-help"]
if shutil.which("flatpak") and cmd_silent(smplayer_fp_cmd) == 0:
    smplayer_config_text = r"""[%General]
add_blackborders_on_fullscreen=false
alang=
audio_equalizer=0, 0, 0, 0, 0, 0, 0, 0, 0, 0
autoload_m4a=true
autoq=6
autosync=false
autosync_factor=100
config_version=5
disable_screensaver=true
driver\audio_output=
driver\vo=
file_settings_method=normal
global_audio_equalizer=true
global_volume=true
mc_value=0
min_step=4
mplayer_bin=mpv
mute=false
osd=1
osd_bar_pos=80
osd_delay=5000
osd_fractions=false
osd_scale=1
osd_show_filename_duration=2000
remember_media_settings=true
remember_stream_settings=true
remember_time_pos=true
slang=
softvol_max=100
subfont_osd_scale=3
tablet_mode=false
use_audio_equalizer=false
use_direct_rendering=false
use_double_buffer=true
use_hwac3=false
use_mc=false
use_scaletempo=-1
use_screenshot=false
screenshot_folder={0}/smplayer_screenshots
screenshot_format=jpg
screenshot_template=cap_%F_%p_%02n
use_slices=false
use_soft_video_eq=false
use_soft_vol=true
vdpau_disable_video_filters=true
vdpau_ffh264vdpau=true
vdpau_ffhevcvdpau=false
vdpau_ffmpeg12vdpau=true
vdpau_ffodivxvdpau=false
vdpau_ffvc1vdpau=true
vdpau_ffwmv3vdpau=true
volume=50

[advanced]
actions_to_run=
autosave_mplayer_log=false
change_video_equalizer_on_startup=true
correct_pts=-1
emulate_mplayer_ab_section=false
log_filter=.*
log_mplayer=true
log_smplayer=true
monitor_aspect=
mplayer_additional_audio_filters=
mplayer_additional_options=
mplayer_additional_video_filters=
mplayer_log_saveto=
mplayer_osd_media_info=
mpv_osd_media_info=
prefer_ipv4=false
repaint_video_background=true
save_smplayer_log=false
show_tag_in_window_title=true
time_to_kill_player=5000
use_edl_files=true
use_idx=false
use_lavf_demuxer=false
use_mplayer_window=false
use_mpris2=true
use_native_open_dialog=true
use_pausing_keep_force=true
use_playlist_option=false
use_short_pathnames=false
verbose_log=false

[gui]
close_on_finish=false
compact_mode=false
delay_left_click=false
dockable_playlist=true
drag_function=1
fullscreen=false
gui=DefaultGUI
hide_video_window_on_audio_files=true
pause_when_hidden=false
precise_seeking=true
qt_style=
relative_seeking=false
reset_stop=false
save_window_size_on_exit=true
iconset=

[history]
recents=@Invalid()
recents\max_items=10
urls=@Invalid()
urls\max_items=50

[instances]
single_instance_enabled=true

[performance]
hard_frame_drop=false
hwdec=auto
threads=1

[streaming]
streaming\youtube\resolution=5
streaming\youtube\use_60fps=true
streaming\youtube\use_av1=false
streaming\youtube\use_dash=true
streaming_type=1

[update_checker]
enabled=false
""".format(userhome)
    # Write smplayer config
    smplayer_config_folder = os.path.join(userhome, ".var", "app", "info.smplayer.SMPlayer", "config", "smplayer")
    smplayer_config_file = os.path.join(smplayer_config_folder, "smplayer.ini")
    os.makedirs(smplayer_config_folder, 0o755, exist_ok=True)
    with open(smplayer_config_file, 'w') as f:
        f.write(smplayer_config_text)
    # Delete smplayer_screenshots folder
    smplayer_sc_fld = os.path.join(userhome, "smplayer_screenshots")
    if os.path.isdir(smplayer_sc_fld):
        shutil.rmtree(smplayer_sc_fld)

### VLC ###
# Check for flatpak
vlc_fp_cmd = ["flatpak", "run", "--command=vlc", "org.videolan.VLC", "--version"]
if shutil.which("flatpak") and cmd_silent(vlc_fp_cmd) == 0:
    vlc_config_fld_data = os.path.join(userhome, ".var", "app", "org.videolan.VLC", "config")
    vlc_config_fld_datavlc = os.path.join(vlc_config_fld_data, "vlc")
    vlc_config_file = os.path.join(vlc_config_fld_datavlc, "vlcrc")
    vlc_config_text = r"""
[qt] # Qt interface

# Resize interface to the native video size (boolean)
qt-video-autoresize=0

# Save the recently played items in the menu (boolean)
qt-recentplay=0

# Ask for network policy at start (boolean)
qt-privacy-ask=0

# Maximum Volume displayed (integer)
qt-max-volume=100
"""
    if os.path.isdir(vlc_config_fld_data):
        os.makedirs(vlc_config_fld_datavlc, exist_ok=True)
        with open(vlc_config_file, 'w') as f:
            f.write(vlc_config_text)

### mpv ###
if os.path.isdir(os.path.join(userhome, ".config")):
    os.makedirs(os.path.join(userhome, ".config", "mpv"), exist_ok=True)
    with open(os.path.join(userhome, ".config", "mpv", "mpv.conf"), 'w') as f:
        f.write("hwdec=auto")
    with open(os.path.join(userhome, ".config", "mpv", "input.conf"), 'w') as f:
        f.write("""
F     script-binding quality_menu/video_formats_toggle
Alt+f script-binding quality_menu/audio_formats_toggle
""")
    os.makedirs(os.path.join(userhome, ".config", "mpv", "scripts"), exist_ok=True)
    os.makedirs(os.path.join(userhome, ".config", "mpv", "script-opts"), exist_ok=True)
    # User Scripts: https://github.com/mpv-player/mpv/wiki/User-Scripts
    # Quality Menu
    CFunc.downloadfile("https://raw.githubusercontent.com/christoph-heinrich/mpv-quality-menu/master/quality-menu.lua", os.path.join(userhome, ".config", "mpv", "scripts"))
    CFunc.downloadfile("https://raw.githubusercontent.com/christoph-heinrich/mpv-quality-menu/master/quality-menu.conf", os.path.join(userhome, ".config", "mpv", "script-opts"))
    # Sponsorblock
    CFunc.downloadfile("https://raw.githubusercontent.com/l-jared/mpv_sponsorblock/master/sponsorblock.lua", os.path.join(userhome, ".config", "mpv", "scripts"))
    os.makedirs(os.path.join(userhome, ".config", "mpv", "scripts", "sponsorblock_shared"), exist_ok=True)
    CFunc.downloadfile("https://raw.githubusercontent.com/l-jared/mpv_sponsorblock/master/sponsorblock_shared/main.lua", os.path.join(userhome, ".config", "mpv", "scripts", "sponsorblock_shared"))
    CFunc.downloadfile("https://raw.githubusercontent.com/l-jared/mpv_sponsorblock/master/sponsorblock_shared/sponsorblock.py", os.path.join(userhome, ".config", "mpv", "scripts", "sponsorblock_shared"))

### Calibre ###
# Check for flatpak
calibre_fp_cmd = ["flatpak", "run", "--command=ebook-viewer", "com.calibre_ebook.calibre", "--version"]
if shutil.which("flatpak") and cmd_silent(calibre_fp_cmd) == 0:
    calibre_config_fld_data = os.path.join(userhome, ".var", "app", "com.calibre_ebook.calibre", "config")
    calibre_config_fld_data_cb = os.path.join(calibre_config_fld_data, "calibre")
    calibre_config_file = os.path.join(calibre_config_fld_data_cb, "viewer-webengine.json")
    calibre_config_text = r"""{
  "old_prefs_migrated": true,
  "session_data": {
    "book_scrollbar": true,
    "footer": {
      "left": "pos-book",
      "middle": "empty",
      "right": "progress"
    },
    "hide_tooltips": null,
    "keyboard_shortcuts": {},
    "paged_taps_scroll_by_screen": true,
    "paged_wheel_scrolls_by_screen": true,
    "standalone_font_settings": {},
    "standalone_misc_settings": {
      "remember_window_geometry": true,
      "save_annotations_in_ebook": false,
      "show_actions_toolbar": true,
      "show_actions_toolbar_in_fullscreen": true
    }
  }
}"""
    if os.path.isdir(calibre_config_fld_data):
        os.makedirs(calibre_config_fld_data_cb, exist_ok=True)
        with open(calibre_config_file, 'w') as f:
            f.write(calibre_config_text)
