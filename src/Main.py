#!/usr/bin/env python3

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk

from MainWindow import MainWindow


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="tr.org.pardus.eta-cinnamon-greeter",
                         flags=Gio.ApplicationFlags.NON_UNIQUE, **kwargs)
        self.window = None

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = MainWindow(self)
        self.window.window.present()


app = Application()
app.run()
