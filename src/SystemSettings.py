#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from configparser import ConfigParser
from pathlib import Path


class SystemSettings(object):
    def __init__(self):
        self.configfile = "/etc/pardus/eta-cinnamon-greeter.conf"
        self.configdir = "/etc/pardus/eta-cinnamon-greeter.conf.d"

        self.default_enabled_pages = [
            "welcome",
            "display",
            "sound",
            "theme",
            "wallpaper",
            "nightlight",
            "password",
            "apps",
            "support",
        ]

        self.default_light_gtk_theme = "eta"
        self.default_light_icon_theme = "eta"
        self.default_light_cinnamon_theme = "eta"

        self.default_dark_gtk_theme = "eta-dark"
        self.default_dark_icon_theme = "eta-dark"
        self.default_dark_cinnamon_theme = "eta-dark"

        self.default_select_hdmi_sound = True

        self.config = ConfigParser(strict=False)

        self.enabled_pages = self.default_enabled_pages.copy()

        self.light_gtk_theme = self.default_light_gtk_theme
        self.light_icon_theme = self.default_light_icon_theme
        self.light_cinnamon_theme = self.default_light_cinnamon_theme

        self.dark_gtk_theme = self.default_dark_gtk_theme
        self.dark_icon_theme = self.default_dark_icon_theme
        self.dark_cinnamon_theme = self.default_dark_cinnamon_theme

        self.select_hdmi_sound = self.default_select_hdmi_sound

    def readConfig(self):
        config_files = []

        main_config = Path(self.configfile)

        if main_config.is_file():
            config_files.append(str(main_config))

        config_dir = Path(self.configdir)

        if config_dir.is_dir():
            config_files.extend(
                str(path)
                for path in sorted(config_dir.glob("*.conf"))
                if path.is_file()
            )

        if not config_files:
            print("No system configuration file found.")
            return

        try:
            self.config.read(config_files)

            # Pages
            pages = self.config.get(
                "Greeter",
                "enabled_pages",
                fallback=""
            )

            if pages:
                self.enabled_pages = [
                    page.strip()
                    for page in pages.split(",")
                    if page.strip()
                ]

            # Light theme
            self.light_gtk_theme = self.config.get(
                "Greeter",
                "light_gtk_theme",
                fallback=self.default_light_gtk_theme
            )

            self.light_icon_theme = self.config.get(
                "Greeter",
                "light_icon_theme",
                fallback=self.default_light_icon_theme
            )

            self.light_cinnamon_theme = self.config.get(
                "Greeter",
                "light_cinnamon_theme",
                fallback=self.default_light_cinnamon_theme
            )

            # Dark theme
            self.dark_gtk_theme = self.config.get(
                "Greeter",
                "dark_gtk_theme",
                fallback=self.default_dark_gtk_theme
            )

            self.dark_icon_theme = self.config.get(
                "Greeter",
                "dark_icon_theme",
                fallback=self.default_dark_icon_theme
            )

            self.dark_cinnamon_theme = self.config.get(
                "Greeter",
                "dark_cinnamon_theme",
                fallback=self.default_dark_cinnamon_theme
            )

            self.select_hdmi_sound = self.config.getboolean(
                "Greeter",
                "select_hdmi_sound",
                fallback=self.default_select_hdmi_sound
            )

            print("System config files: {}".format(config_files))
            print("Enabled pages: {}".format(self.enabled_pages))

            print("Light GTK theme: {}".format(self.light_gtk_theme))
            print("Light icon theme: {}".format(self.light_icon_theme))
            print("Light Cinnamon theme: {}".format(self.light_cinnamon_theme))

            print("Dark GTK theme: {}".format(self.dark_gtk_theme))
            print("Dark icon theme: {}".format(self.dark_icon_theme))
            print("Dark Cinnamon theme: {}".format(self.dark_cinnamon_theme))

            print("Select HDMI sound: {}".format(self.select_hdmi_sound))


        except Exception as e:
            print("System config read error: {}".format(e))

            self.enabled_pages = self.default_enabled_pages.copy()

            self.light_gtk_theme = self.default_light_gtk_theme
            self.light_icon_theme = self.default_light_icon_theme
            self.light_cinnamon_theme = self.default_light_cinnamon_theme

            self.dark_gtk_theme = self.default_dark_gtk_theme
            self.dark_icon_theme = self.default_dark_icon_theme
            self.dark_cinnamon_theme = self.default_dark_cinnamon_theme

            self.select_hdmi_sound = self.default_select_hdmi_sound

    def is_page_enabled(self, page_name):
        return page_name in self.enabled_pages
