from ctypes import CDLL

CDLL("libgtk4-layer-shell.so")
import gi  # noqa

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")

from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import Gtk4LayerShell as LayerShell  # pyright: ignore #noqa
from hyprbar.config import HyprbarConfig  # pyright: ignore # noqa

hyprBarConfig = None


def on_activate(app):
    window = Gtk.Window(application=app)
    window.set_default_size(hyprBarConfig.window.width, hyprBarConfig.window.height)  # pyright: ignore # noqa

    LayerShell.init_for_window(window)
    LayerShell.set_layer(window, LayerShell.Layer.TOP)
    LayerShell.set_anchor(window, LayerShell.Edge.BOTTOM, True)
    LayerShell.set_margin(window, LayerShell.Edge.BOTTOM, 0)
    LayerShell.set_margin(window, LayerShell.Edge.TOP, 20)
    LayerShell.auto_exclusive_zone_enable(window)

    button = Gtk.Button(label="GTK4 Layer Shell with Python")
    button.connect("clicked", lambda _: window.close())

    button2 = Gtk.Button(label="Ahhhhhhhh")

    gtkBbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    gtkBbox.append(button)
    gtkBbox.append(button2)

    window.set_child(gtkBbox)
    window.present()


def runHyprBar(config: HyprbarConfig) -> None:
    """
    HyprBar is a GTK4 Layer Shell bar for Hyprland.
    """
    global hyprBarConfig
    hyprBarConfig = config

    # Create the application
    app = Gtk.Application(application_id="com.antrax.HyprBar")
    app.connect("activate", on_activate)
    app.run(None)
