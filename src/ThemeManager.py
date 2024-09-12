#!/usr/bin/env python3

import subprocess


def set_gtk_theme(theme):
    subprocess.call([
        "gsettings",
        "set",
        "org.cinnamon.desktop.interface",
        "gtk-theme",
        f"'{theme}'"
    ])


def set_icon_theme(theme):
    subprocess.call([
        "gsettings",
        "set",
        "org.cinnamon.desktop.interface",
        "icon-theme",
        f"'{theme}'"
    ])


def set_cinnamon_theme(theme):
    subprocess.call([
        "gsettings",
        "set",
        "org.cinnamon.theme",
        "name",
        f"'{theme}'"
    ])


def get_gtk_theme():
    return subprocess.check_output([
        "gsettings",
        "get",
        "org.cinnamon.desktop.interface",
        "gtk-theme"
    ]).decode("utf-8").rstrip()


def get_icon_theme(theme):
    return subprocess.check_output([
        "gsettings",
        "get",
        "org.cinnamon.desktop.interface",
        "icon-theme"
    ]).decode("utf-8").rstrip()


def get_cinnamon_theme(theme):
    return subprocess.check_output([
        "gsettings",
        "get",
        "org.cinnamon.theme",
        "name"
    ]).decode("utf-8").rstrip()
