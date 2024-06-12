#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess

from setuptools import setup, find_packages


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "eta-cinnamon-greeter.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/eta-cinnamon-greeter.mo"]))
    return mo


changelog = "debian/changelog"
version = "0.1.0"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
 ("/usr/share/applications/", ["data/tr.org.pardus.eta-cinnamon-greeter.desktop"]),
 ("/usr/share/pardus/eta-cinnamon-greeter/data",
  ["data/eta-cinnamon-greeter.svg", "data/discord.svg", "data/github.svg"]),
 ("/usr/share/pardus/eta-cinnamon-greeter/data/css",
  ["data/css/adw.css",
   "data/css/all.css",
   "data/css/base.css"]
  ),
 ("/usr/share/pardus/eta-cinnamon-greeter/src",
  ["src/Main.py",
   "src/MainWindow.py",
   "src/Server.py",
   "src/Stream.py",
   "src/UserSettings.py",
   "src/utils.py",
   "src/WallpaperManager.py",
   "src/ScaleManager.py",
   ]
  ),
 ("/usr/share/pardus/eta-cinnamon-greeter/ui", ["ui/MainWindow.glade"]),
 ("/usr/bin/", ["eta-cinnamon-greeter"]),
 ("/etc/skel/.config/autostart", ["data/tr.org.pardus.eta-cinnamon-greeter.desktop"]),
 ("/usr/share/icons/hicolor/scalable/apps/", ["data/eta-cinnamon-greeter.svg"])
] + create_mo_files()

setup(
    name="ETA Greeter",
    version=version,
    packages=find_packages(),
    scripts=["eta-cinnamon-greeter"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Fatih Altun",
    author_email="fatih.altun@pardus.org.tr",
    description="ETA Greeter at first login.",
    license="GPLv3",
    keywords="start setup settings theme wallpaper",
    url="https://github.com/pardus/eta-cinnamon-greeter",
)
