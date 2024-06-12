#!/usr/bin/env python3

import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib


def val_to_variant(val):
    if isinstance(val, float):
        return GLib.Variant.new_double(val)
    if isinstance(val, str):
        return GLib.Variant.new_string(val)
    if isinstance(val, int):
        return GLib.Variant.new_int32(val)
    if isinstance(val, GLib.Variant):
        return val


def gsettings_set(schema, key, value):
    gio_val = val_to_variant(value)
    settings = Gio.Settings.new(schema)
    return settings.set_value(key, gio_val)


def gsettings_get(schema, key):
    settings = Gio.Settings.new(schema)
    return settings.get_value(key)


def change_wallpaper(picture_uri):
    theme_schema = "org.cinnamon.desktop.background"
    theme_keys = ["picture-uri"]
    for theme in theme_keys:
        gsettings_set(theme_schema, theme, "file://" + picture_uri)
    return True


def get_wallpapers():
    wallpaper_dir = "/usr/share/backgrounds"
    wallpapers = []
    for root, dirs, files in os.walk(wallpaper_dir):
        dirs.clear()
        for file_name in files:
            path = os.path.join(root, file_name)
            wallpapers.append(path)
    return wallpapers

