from ctypes import CDLL

CDLL("libgtk4-layer-shell.so")
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gtk4LayerShell


class StatusBarApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        window = Gtk.ApplicationWindow(application=app)
        label = Gtk.Label(label="GTK4 Layer Shell com Python!")
        window.set_child(label)

        # Inicialize a janela com Layer Shell
        Gtk4LayerShell.init_for_window(window)
        Gtk4LayerShell.auto_exclusive_zone_enable(window)
        Gtk4LayerShell.set_margin(window, Gtk4LayerShell.Edge.TOP, 0)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_anchor(window, Gtk4LayerShell.Edge.RIGHT, True)

        window.present()


if __name__ == "__main__":
    app = StatusBarApp(application_id="com.example.StatusBar")
    app.run()
