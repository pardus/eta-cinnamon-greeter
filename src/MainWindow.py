#!/usr/bin/env python3

import os
import subprocess
import threading
import time

import dbus
import gi

import utils
from utils import ErrorDialog

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('Cvc', '1.0')
from gi.repository import Gio, Gtk, GdkPixbuf, GLib, Gdk, Gst, Cvc
import locale
from locale import gettext as _
from pathlib import Path
from configparser import ConfigParser
from locale import getlocale
from UserSettings import UserSettings

# Translation Constants:
APPNAME = "eta-cinnamon-greeter"
TRANSLATIONS_PATH = "/usr/share/locale"
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)


def get_current_desktop():
    if "XDG_CURRENT_DESKTOP" in os.environ:
        return os.environ["XDG_CURRENT_DESKTOP"].lower()
    elif "DESKTOP_SESSION" in os.environ:
        return os.environ["DESKTOP_SESSION"].lower()
    elif "SESSION" in os.environ:
        return os.environ["SESSION"].lower()
    else:
        return ""


# current_desktop = get_current_desktop()
# if "cinnamon" not in current_desktop:
#     ErrorDialog(_("Error"), _("Your desktop environment is not supported."))
#     exit(0)

import WallpaperManager as WallpaperManager
import ThemeManager as ThemeManager

from Server import Server
from Stream import Stream

autostart_file = str(Path.home()) + "/.config/autostart/tr.org.pardus.eta-cinnamon-greeter.desktop"

# Let the application greet the user only on the first boot
try:
    if os.path.exists(autostart_file):
        os.remove(autostart_file)
except OSError:
    pass

# In live mode, the application should not welcome the user
if utils.check_live() and os.path.isfile(autostart_file):
    exit(0)


class MainWindow:
    def __init__(self, application):
        self.Application = application

        # Gtk Builder
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade")
        self.builder.connect_signals(self)

        # Translate things on glade:
        self.builder.set_translation_domain(APPNAME)

        # Add Window
        self.window = self.builder.get_object("window")
        self.window.set_application(application)
        self.window.connect('destroy', self.onDestroy)

        # self.control_display()

        self.user_locale = self.get_user_locale()

        self.set_css()

        self.define_components()
        self.define_variables()

        self.get_monitor_resolution()
        self.add_sound_devices()

        self.user_settings()
        self.UserSettings.set_autostart(self.UserSettings.config_autostart)
        self.chkbtn_autostart.set_active(self.UserSettings.config_autostart)

        # Put Wallpapers on a Grid
        thread = threading.Thread(target=self.add_wallpapers, args=(WallpaperManager.get_wallpapers(),))
        thread.daemon = True
        thread.start()

        # set pardus-software apps
        self.set_pardussoftware_apps()

        self.set_active_theme()

        self.set_initial_nightlight_status()

        # Show Screen:
        self.window.show_all()

        # Hide widgets:
        self.hide_widgets()

        self.set_signals()

        thread_sound = threading.Thread(target=self.select_sound_device)
        thread_sound.daemon = True
        thread_sound.start()

    def get_user_locale(self):
        try:
            user_locale = os.getenv("LANG").split(".")[0].split("_")[0]
        except Exception as e:
            print("{}".format(e))
            try:
                user_locale = getlocale()[0].split("_")[0]
            except Exception as e:
                print("{}".format(e))
                user_locale = "en"
        if user_locale != "tr" and user_locale != "en":
            user_locale = "en"
        return user_locale

    def set_css(self):
        settings = Gtk.Settings.get_default()
        theme_name = "{}".format(settings.get_property('gtk-theme-name')).lower().strip()
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path(os.path.dirname(os.path.abspath(__file__)) + "/../data/css/style.css")
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def control_display(self):
        width = 815
        height = 650
        s = 1
        w = 1920
        h = 1080
        try:
            display = Gdk.Display.get_default()
            monitor = display.get_primary_monitor()
            geometry = monitor.get_geometry()
            w = geometry.width
            h = geometry.height
            s = Gdk.Monitor.get_scale_factor(monitor)

            if w > 1920 or h > 1080:
                width = int(w / 2.258)
                height = int(h / 1.661)

            self.window.resize(width, height)

        except Exception as e:
            print("Error in controlDisplay: {}")
            print("{}".format(e))

        print("window w:{} h:{} | monitor w:{} h:{} s:{}".format(width, height, w, h, s))

    def user_settings(self):
        self.UserSettings = UserSettings()
        self.UserSettings.createDefaultConfig()
        self.UserSettings.readConfig()

        print("{} {}".format("config_autostart", self.UserSettings.config_autostart))

    def define_components(self):
        def get_ui(str):
            return self.builder.get_object(str)

        # about dialog
        self.ui_about_dialog = self.builder.get_object("ui_about_dialog")
        self.ui_about_dialog.set_program_name(_("ETA Greeter"))
        if self.ui_about_dialog.get_titlebar() is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("About ETA Greeter"))
            about_headerbar.pack_start(Gtk.Image.new_from_icon_name("eta-cinnamon-greeter", Gtk.IconSize.LARGE_TOOLBAR))
            about_headerbar.show_all()
            self.ui_about_dialog.set_titlebar(about_headerbar)
        # Set version
        # If not getted from __version__ file then accept version in MainWindow.glade file
        try:
            version = open(os.path.dirname(os.path.abspath(__file__)) + "/__version__").readline()
            self.ui_about_dialog.set_version(version)
        except:
            pass

        # - Navigation:
        self.lbl_headerTitle = get_ui("lbl_headerTitle")
        self.stk_pages = get_ui("stk_pages")
        self.stk_btn_next = get_ui("stk_btn_next")
        self.btn_next = get_ui("btn_next")
        self.btn_prev = get_ui("btn_prev")
        self.btn_close = get_ui("btn_close")
        self.box_progressDots = get_ui("box_progressDots")

        # - Stack Pages:
        self.page_welcome = get_ui("page_welcome")
        self.page_theme = get_ui("page_theme")
        self.page_wallpaper = get_ui("page_wallpaper")
        self.page_display = get_ui("page_display")
        self.page_sound = get_ui("page_sound")
        self.page_applications = get_ui("page_applications")
        self.page_support = get_ui("page_support")
        self.page_nightlight = get_ui("page_nightlight")

        # FIX this solution later. Because we are not getting stack title in this gtk version.
        self.page_welcome.name = _("Welcome")
        self.page_wallpaper.name = _("Select Wallpaper")
        self.page_theme.name = _("Select Theme")
        self.page_display.name = _("Display Settings")
        self.page_sound.name = _("Sound Settings")
        self.page_applications.name = _("Applications")
        self.page_support.name = _("Support & Community")
        self.page_nightlight.name = _("Night Light")

        # - Display Settings:
        self.flow_wallpapers = get_ui("flow_wallpapers")
        self.lbl_current_res = get_ui("lbl_current_res")

        self.btn_4k = get_ui("btn_4k")
        self.btn_fullhd = get_ui("btn_fullhd")

        # - Night Light:
        self.ui_night_switch = get_ui("ui_night_switch")
        self.ui_temp_box = get_ui("ui_temp_box")
        self.ui_temp_adjusment = get_ui("ui_temp_adjusment")
        self.ui_nightlight_settings_box = get_ui("ui_nightlight_settings_box")
        self.ui_temp_box = get_ui("ui_temp_box")
        self.ui_nightlight_stack = get_ui("ui_nightlight_stack")
        self.ui_temp_low_button = get_ui("ui_temp_low_button")
        self.ui_temp_medium_button = get_ui("ui_temp_medium_button")
        self.ui_temp_high_button = get_ui("ui_temp_high_button")

        self.chkbtn_autostart = get_ui("chkbtn_autostart")

        tabTitle = self.stk_pages.get_visible_child().name
        self.lbl_headerTitle.set_text(tabTitle)

        self.ui_apps_flowbox = get_ui("ui_apps_flowbox")
        self.ui_apps_error_label = get_ui("ui_apps_error_label")
        self.ui_apps_stack = get_ui("ui_apps_stack")

        self.sound_listbox = get_ui("sound_listbox")

        self.img_lightTheme = get_ui("img_lightTheme")
        self.img_darkTheme = get_ui("img_darkTheme")

        self.rb_darkTheme = get_ui("rb_darkTheme")
        self.rb_lightTheme = get_ui("rb_lightTheme")

        self.img_nightlight = get_ui("img_nightlight")

        self.img_lightTheme.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(
            os.path.dirname(os.path.abspath(__file__)) + "/../data/theme-light.png", 350, 276, False))
        self.img_darkTheme.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(
            os.path.dirname(os.path.abspath(__file__)) + "/../data/theme-dark.png", 350, 276, False))

        self.img_nightlight.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(
            os.path.dirname(os.path.abspath(__file__)) + "/../data/pardus-night-light-ss.png", 500, 222, False))

    def define_variables(self):
        self.currentpage = 0
        self.stk_len = 0
        for row in self.stk_pages:
            self.stk_len += 1

        self.apps_url = "https://apps.pardus.org.tr/api/greeter"
        self.non_tls_tried = False

        self.current_res = ""
        self.current_scale = ""
        self.hidpi_found = False
        self.fullhd_found = False
        self.hidpi_res = None
        self.fullhd_res = None

        self.temp_color = {"low": 5500, "medium": 4000, "high": 2500}

    # =========== UI Preparing functions:
    def hide_widgets(self):

        self.btn_prev.set_sensitive(self.currentpage != 0)
        self.btn_fullhd.set_sensitive(self.fullhd_found)
        self.btn_4k.set_sensitive(self.hidpi_found)
        self.ui_temp_box.set_visible(self.config_nightlight_status)

    def set_signals(self):
        self.rb_lightTheme.connect("clicked", self.on_rb_lightTheme_clicked)
        self.rb_darkTheme.connect("clicked", self.on_rb_darkTheme_clicked)
        self.ui_night_switch.connect("state-set", self.on_ui_night_switch_state_set)

    def set_active_theme(self):
        try:
            theme = ThemeManager.get_gtk_theme()
            if theme == "eta":
                self.rb_lightTheme.set_active(True)
            elif theme == "eta-dark":
                self.rb_darkTheme.set_active(True)
            else:
                self.rb_lightTheme.set_active(False)
                self.rb_darkTheme.set_active(False)
        except Exception as e:
            print("{}".format(e))

    def get_locale(self):
        try:
            user_locale = os.getenv("LANG").split(".")[0].split("_")[0]
        except Exception as e:
            print("{}".format(e))
            try:
                user_locale = getlocale()[0].split("_")[0]
            except Exception as e:
                print("{}".format(e))
                user_locale = "en"
        if user_locale != "tr" and user_locale != "en":
            user_locale = "en"
        return user_locale

    # =========== Settings Functions:

    # Add wallpapers to the grid:
    def add_wallpapers(self, wallpaper_list):
        for i in range(len(wallpaper_list)):
            # Image
            bitmap = GdkPixbuf.Pixbuf.new_from_file(wallpaper_list[i])
            bitmap = bitmap.scale_simple(240, 135, GdkPixbuf.InterpType.BILINEAR)

            img_wallpaper = Gtk.Image.new_from_pixbuf(bitmap)
            img_wallpaper.img_path = wallpaper_list[i]

            tooltip = wallpaper_list[i]
            try:
                tooltip = os.path.basename(tooltip)
                tooltip = os.path.splitext(tooltip)[0]
                if "pardus23-0_" in tooltip:
                    tooltip = tooltip.split("pardus23-0_")[1]
                    tooltip = tooltip.replace("-", " ")
                elif "pardus23-" in tooltip and "_" in tooltip:
                    tooltip = tooltip.split("_")[1]
                    tooltip = tooltip.replace("-", " ")
            except Exception as e:
                print("{}".format(e))
                pass
            img_wallpaper.set_tooltip_text(tooltip)

            GLib.idle_add(self.flow_wallpapers.insert, img_wallpaper, -1)
            GLib.idle_add(self.flow_wallpapers.show_all)

    def get_monitor_resolution(self):
        self.bus = dbus.SessionBus()
        self.display_config_name = "org.cinnamon.Muffin.DisplayConfig"
        self.display_config_path = "/org/cinnamon/Muffin/DisplayConfig"
        if "gnome" in get_current_desktop():
            self.display_config_name = "org.gnome.Mutter.DisplayConfig"
            self.display_config_path = "/org/gnome/Mutter/DisplayConfig"

        display_config_proxy = self.bus.get_object(self.display_config_name, self.display_config_path)
        display_config_interface = dbus.Interface(display_config_proxy, dbus_interface=self.display_config_name)
        serial, physical_monitors, logical_monitors, properties = display_config_interface.GetCurrentState()
        availables = []
        for x, y, scale, transform, primary, linked_monitors_info, props in logical_monitors:
            for linked_monitor_connector, linked_monitor_vendor, linked_monitor_product, linked_monitor_serial in linked_monitors_info:
                for monitor_info, monitor_modes, monitor_properties in physical_monitors:
                    monitor_connector, monitor_vendor, monitor_product, monitor_serial = monitor_info
                    if linked_monitor_connector == monitor_connector:
                        for mode_id, mode_width, mode_height, mode_refresh, mode_preferred_scale, mode_supported_scales, mode_properties in monitor_modes:
                            availables.append(mode_id)
                            # print("available: {}".format(mode_id))
                            if mode_properties.get("is-current", False):
                                print("current: " + mode_id)
                                self.current_res = mode_id
                                self.current_scale = scale


        for res in availables:
            if "3840x2160" in res and not self.hidpi_found:
                self.hidpi_found = True
                self.hidpi_res = res
                print("hidpi_found: {}".format(res))
            if "1920x1080" in res and not self.fullhd_found:
                self.fullhd_found = True
                self.fullhd_res = res
                print("fullhd_found: {}".format(res))

        self.lbl_current_res.set_text("{} (%{})".format(self.current_res, int(self.current_scale * 100)))

    def set_pardussoftware_apps(self):

        self.stream = Stream()
        self.stream.StreamGet = self.StreamGet
        self.server_response = None
        self.server = Server()
        self.server.ServerGet = self.ServerGet
        self.server.get(self.apps_url)

    def StreamGet(self, pixbuf, data):
        lang = f"pretty_{self.user_locale}"

        pretty_name = data[lang]
        package_name = data["name"]

        icon = Gtk.Image.new()
        icon.set_from_pixbuf(pixbuf)

        label = Gtk.Label.new()
        label.set_text("{}".format(pretty_name))
        label.set_line_wrap(True)
        label.set_max_width_chars(21)

        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        box.pack_start(icon, False, True, 0)
        box.pack_start(label, False, True, 0)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(3)
        box.set_margin_bottom(3)
        box.set_spacing(8)

        listbox = Gtk.ListBox.new()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.get_style_context().add_class("pardus-software-listbox")
        listbox.add(box)
        listbox.name = package_name

        frame = Gtk.Frame.new()
        frame.get_style_context().add_class("pardus-software-frame")
        frame.add(listbox)

        self.ui_apps_flowbox.get_style_context().add_class("pardus-software-flowbox")
        GLib.idle_add(self.ui_apps_flowbox.insert, frame, GLib.PRIORITY_DEFAULT_IDLE)

        GLib.idle_add(self.ui_apps_flowbox.show_all)

    def ServerGet(self, response):
        if "error" not in response.keys():
            self.ui_apps_stack.set_visible_child_name("apps")
            datas = response["greeter"]["suggestions"]
            if len(datas) > 0:
                for data in datas:
                    if self.non_tls_tried:
                        data["icon"] = data["icon"].replace("https", "http")
                    self.stream.fetch(data)
        else:
            if "tlserror" in response.keys() and not self.non_tls_tried:
                self.non_tls_tried = True
                self.apps_url = self.apps_url.replace("https", "http")
                print("trying {}".format(self.apps_url))
                self.server.get(self.apps_url)
            else:
                error_message = response["message"]
                print(error_message)
                self.ui_apps_stack.set_visible_child_name("error")
                self.ui_apps_error_label.set_text(error_message)

    def on_sound_device_added(self, c, deviceId, direction):
        device = getattr(self.controller, "lookup_" + direction + "_id")(deviceId)
        print("Sound Device: {}".format(device.get_description()))
        self.add_sound_device_to_ui(device)

    def on_sound_default_sink_changed(self, c, deviceId):
        default_sink = self.controller.get_default_sink()
        if default_sink is None:
            return
        print(f"default sink_changed to: {c.get_default_sink().get_description()}")
        max_norm = self.controller.get_vol_max_norm()
        stream = self.controller.lookup_stream_id(deviceId)
        denormalized_volume = max_norm
        stream.change_is_muted(False)
        stream.set_volume(denormalized_volume)
        stream.push_volume()

    def add_sound_devices(self):
        self.controller = Cvc.MixerControl.new("mixer-control")
        self.controller.open()

        self.controller.connect("output-added", self.on_sound_device_added, "output")
        self.controller.connect("default_sink_changed", self.on_sound_default_sink_changed)

    def select_sound_device(self):
        time.sleep(3)
        # If hdmi in list then make it default
        for row in self.sound_listbox:
            if "hdmi" in row.name.get_description().lower():
                GLib.idle_add(self.sound_listbox.select_row, row)

    def add_sound_device_to_ui(self, device):
        row = Gtk.ListBoxRow()
        row.set_margin_top(3)
        row.set_margin_bottom(3)
        row.set_margin_start(3)
        row.set_margin_end(3)

        label = Gtk.Label(label="{}".format(device.get_description()))

        image = Gtk.Image.new_from_icon_name("audio-speakers-symbolic", Gtk.IconSize.BUTTON)

        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
        box.set_margin_top(13)
        box.set_margin_bottom(13)
        box.set_margin_start(5)
        box.set_margin_end(5)

        box.pack_start(image, False, True, 0)
        box.pack_start(label, False, True, 0)

        row.add(box)
        row.name = device
        self.sound_listbox.add(row)
        GLib.idle_add(self.sound_listbox.show_all)

    def set_initial_nightlight_status(self):
        self.config_nightlight_status = False
        self.config_nightlight_temp = 5500
        self.nightlight_config_file = "{}/pardus/pardus-night-light/settings.ini".format(GLib.get_user_config_dir())
        if os.path.isfile(self.nightlight_config_file):
            try:
                self.nightlight_config = ConfigParser(strict=False)
                self.nightlight_config.read(self.nightlight_config_file)
                self.config_nightlight_status = self.nightlight_config.getboolean('Main', 'status')
                self.config_nightlight_temp = self.nightlight_config.getint('Main', 'temp')
            except Exception as e:
                print("{}".format(e))

            self.ui_night_switch.set_state(self.config_nightlight_status)
            if self.config_nightlight_temp == self.temp_color["low"]:
                self.ui_temp_low_button.get_style_context().add_class("suggested-action")
                self.ui_temp_medium_button.get_style_context().remove_class("suggested-action")
                self.ui_temp_high_button.get_style_context().remove_class("suggested-action")
            elif self.config_nightlight_temp == self.temp_color["medium"]:
                self.ui_temp_low_button.get_style_context().remove_class("suggested-action")
                self.ui_temp_medium_button.get_style_context().add_class("suggested-action")
                self.ui_temp_high_button.get_style_context().remove_class("suggested-action")
            elif self.config_nightlight_temp == self.temp_color["high"]:
                self.ui_temp_low_button.get_style_context().remove_class("suggested-action")
                self.ui_temp_medium_button.get_style_context().remove_class("suggested-action")
                self.ui_temp_high_button.get_style_context().add_class("suggested-action")
            else:
                self.ui_temp_low_button.get_style_context().remove_class("suggested-action")
                self.ui_temp_medium_button.get_style_context().remove_class("suggested-action")
                self.ui_temp_high_button.get_style_context().remove_class("suggested-action")

        if self.is_app_installed("tr.org.pardus.night-light.desktop"):
            self.ui_nightlight_stack.set_visible_child_name("installed")
        else:
            self.ui_nightlight_stack.set_visible_child_name("notinstalled")

    # - stack prev and next page controls
    def get_next_page(self, page):
        increase = 0
        for i in range(0, self.stk_len):
            increase += 1
            if self.stk_pages.get_child_by_name("{}".format(page + increase)) != None:
                return page + increase
        return None

    def get_prev_page(self, page):
        increase = 0
        for i in range(0, self.stk_len):
            increase += -1
            if self.stk_pages.get_child_by_name("{}".format(page + increase)) != None:
                return page + increase
        return None

    def is_app_installed(self, app_id):
        try:
            return Gio.DesktopAppInfo.new(app_id) is not None
        except:
            return False

    # =========== SIGNALS:    
    def onDestroy(self, b):
        self.window.get_application().quit()

    def on_ui_about_button_clicked(self, button):
        self.ui_about_dialog.run()
        self.ui_about_dialog.hide()

    # - NAVIGATION:
    def on_btn_next_clicked(self, btn):
        self.stk_pages.set_visible_child_name("{}".format(self.get_next_page(self.currentpage)))

        self.currentpage = int(self.stk_pages.get_visible_child_name())

        nextButtonPage = "next" if self.get_next_page(self.currentpage) != None else "close"
        self.stk_btn_next.set_visible_child_name(nextButtonPage)
        self.btn_next.grab_focus() if nextButtonPage == "next" else self.btn_close.grab_focus()

        self.btn_prev.set_sensitive(self.currentpage != 0)

        # Set Header Title
        tabTitle = self.stk_pages.get_visible_child().name
        self.lbl_headerTitle.set_text(tabTitle)

    def on_btn_prev_clicked(self, btn):
        self.stk_pages.set_visible_child_name("{}".format(self.get_prev_page(self.currentpage)))

        self.currentpage = int(self.stk_pages.get_visible_child_name())

        self.stk_btn_next.set_visible_child_name("next")
        self.btn_prev.set_sensitive(self.currentpage != 0)

        # Set Header Title
        tabTitle = self.stk_pages.get_visible_child().name
        self.lbl_headerTitle.set_text(tabTitle)

    # - Wallpaper Select:
    def on_wallpaper_selected(self, flowbox, wallpaper):
        filename = str(wallpaper.get_children()[0].img_path)
        WallpaperManager.change_wallpaper(filename)

    def on_ui_apps_flowbox_child_activated(self, flow_box, child):
        package_name = child.get_children()[0].get_children()[0].name
        try:
            subprocess.Popen(["pardus-software", "-d", package_name])
        except Exception as e:
            ErrorDialog(_("Error"), "{}".format(e))

    def on_ui_pardus_software_button_clicked(self, button):
        try:
            subprocess.Popen(["pardus-software"])
        except Exception as e:
            ErrorDialog(_("Error"), "{}".format(e))

    def on_ui_system_settings_button_clicked(self, button):
        try:
            subprocess.Popen(["cinnamon-settings"])
        except Exception as e:
            ErrorDialog(_("Error"), "{}".format(e))

    def on_btn_4k_clicked(self, button):
        try:
            subprocess.Popen(["eta-resolution", "-s", "0"])
        except Exception as e:
            ErrorDialog(_("Error"), "{}".format(e))
            return
        self.lbl_current_res.set_text("{}".format(self.hidpi_res))

    def on_btn_fullhd_clicked(self, button):
        try:
            subprocess.Popen(["eta-resolution", "-s", "1"])
        except Exception as e:
            ErrorDialog(_("Error"), "{}".format(e))
            return
        self.lbl_current_res.set_text("{}".format(self.fullhd_res))

    def on_chkbtn_autostart_toggled(self, button):
        state = button.get_active()
        print(state)
        self.UserSettings.set_autostart(state)
        user_autostart = self.UserSettings.config_autostart
        if state != user_autostart:
            self.UserSettings.writeConfig(state)
            self.user_settings()

    def on_sound_listbox_row_selected(self, listbox, row):
        device = row.name
        print(f"Selected Device: {device.get_description()}")
        GLib.idle_add(self.controller.change_output, device)

    def on_play_button_clicked(self, button):
        Gst.init(None)
        self.player = Gst.ElementFactory.make('playbin', 'player')
        self.player.set_property('uri', 'file://' + (os.path.dirname(os.path.abspath(__file__)) + "/../data/sample.m4a"))
        self.player.set_state(Gst.State.PLAYING)

    def on_rb_lightTheme_clicked(self, rb):
        if rb.get_active():

            GLib.idle_add(ThemeManager.set_gtk_theme, "eta")
            GLib.idle_add(ThemeManager.set_icon_theme, "eta")
            GLib.idle_add(ThemeManager.set_cinnamon_theme, "eta")

    def on_rb_darkTheme_clicked(self, rb):
        if rb.get_active():
            GLib.idle_add(ThemeManager.set_gtk_theme, "eta-dark")
            GLib.idle_add(ThemeManager.set_icon_theme, "eta-dark")
            GLib.idle_add(ThemeManager.set_cinnamon_theme, "eta-dark")

    def on_ui_temp_button_clicked(self, button):
        print("on_ui_temp_adjusment_value_changed", self.temp_color[button.get_name()])
        subprocess.Popen(["pardus-night-light", "-c", "{}".format(self.temp_color[button.get_name()])],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL,
                         close_fds=True,
                         start_new_session=True)
        for row_button in self.ui_temp_box:
            row_button.get_style_context().remove_class("suggested-action")
        button.get_style_context().add_class("suggested-action")

    def on_ui_night_switch_state_set(self, switch, state):
        self.ui_temp_box.set_visible(state)
        subprocess.Popen(["pardus-night-light", "-s", "1" if state else "0"],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL,
                         close_fds=True,
                         start_new_session=True)

    def on_ui_nightlight_install_button_clicked(self, button):
        subprocess.Popen(["pardus-software", "-d", "pardus-night-light"])
