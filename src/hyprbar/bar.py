from ctypes import CDLL

CDLL("libgtk4-layer-shell.so")
import gi  # noqa

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")

from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import Gtk4LayerShell as LayerShell  # pyright: ignore #noqa
from gi.repository import GLib  # pyright: ignore # noqa

from hyprbar.config import HyprbarConfig  # pyright: ignore # noqa
from hyprbar.constants import STYLE_FILE, ANCHOR  # pyright: ignore # noqa
from hyprbar.widgets import populateBox  # pyright: ignore # noqa
from hyprbar.util import printLog  # pyright: ignore # noqa


hyprBarConfig = None
components = []
index = 0


def onActivate(app):
    printLog("on activate triggered")
    window = Gtk.Window(application=app)
    printLog("window created, setting properties for hyprbar window instance: ")
    window.set_name("hyprbar")
    # Carregar CSS
    printLog("Setting up style with CSS path: " + STYLE_FILE)
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(f"{STYLE_FILE}")
    display = window.get_display()
    Gtk.StyleContext.add_provider_for_display(
        display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
    printLog("CSS provider loaded")

    printLog(
        f"bar size to '{hyprBarConfig.window.width}x{hyprBarConfig.window.height}'"  # pyright: ignore # noqa
    )
    window.set_default_size(hyprBarConfig.window.width, hyprBarConfig.window.height)  # pyright: ignore # noqa

    printLog("Layer Shell initialized")
    LayerShell.init_for_window(window)
    LayerShell.set_layer(window, LayerShell.Layer.TOP)

    # Anchor
    # LayerShell.set_anchor(window, LayerShell.Edge.BOTTOM, True)
    LayerShell.set_anchor(window, ANCHOR[hyprBarConfig.window.anchor], True)  # pyright: ignore # noqa
    # margins
    LayerShell.set_margin(
        window,
        LayerShell.Edge.BOTTOM,
        hyprBarConfig.window.margin_bottom,  # pyright: ignore # noqa
    )
    LayerShell.set_margin(window, LayerShell.Edge.TOP, hyprBarConfig.window.margin_top)  # pyright: ignore # noqa

    mainBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    # faz com que todos os widgets filhos ocupem o mesmo espaço
    # horizontalmente
    printLog("Setting homogeneous to True for mainBox.")
    mainBox.set_homogeneous(True)

    window.set_child(mainBox)

    # Enable Exclusive Zone
    LayerShell.auto_exclusive_zone_enable(window)

    printLog("Creating leftGtkBox for window...")
    leftGtkBox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=hyprBarConfig.window.left_container.hor_spacing,  # pyright: ignore # noqa
    )
    leftGtkBox.set_halign(Gtk.Align.START)
    leftGtkBox.set_valign(Gtk.Align.CENTER)

    printLog("Creating centerGtkBox for window...")
    centerGtkBox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=hyprBarConfig.window.center_container.hor_spacing,  # pyright: ignore # noqa
    )  # pyright: ignore # noqa
    centerGtkBox.set_halign(Gtk.Align.CENTER)
    centerGtkBox.set_valign(Gtk.Align.CENTER)

    printLog("Creating rightGtkBox for window...")
    rightGtkBox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=hyprBarConfig.window.right_container.hor_spacing,  # pyright: ignore # noqa
    )  # pyright: ignore # noqa
    rightGtkBox.set_halign(Gtk.Align.END)
    rightGtkBox.set_valign(Gtk.Align.CENTER)

    mainBox.append(leftGtkBox)
    mainBox.append(centerGtkBox)
    mainBox.append(rightGtkBox)

    printLog("Populate boxes with widgets.")
    populateBox(leftGtkBox, hyprBarConfig.window.left_container.components)  # pyright: ignore # noqa
    populateBox(centerGtkBox, hyprBarConfig.window.center_container.components)  # pyright: ignore # noqa
    populateBox(rightGtkBox, hyprBarConfig.window.right_container.components)  # pyright: ignore # noqa

    printLog("Show the window with all widgets.")
    window.present()


def runHyprBar(config: HyprbarConfig) -> None:
    """
    HyprBar is a GTK4 Layer Shell bar for Hyprland.
    """
    printLog("Instantiate the config Class ")
    global hyprBarConfig
    hyprBarConfig = config

    # Create the application
    printLog("Create a new Application instance with 'com.antrax.HyprBar' as an id")
    app = Gtk.Application(application_id="com.antrax.HyprBar")
    printLog("Connect to the activate signal of the application")
    app.connect("activate", onActivate)
    printLog("Start the GTK main loop with 'app.run()'")
    app.run(None)
