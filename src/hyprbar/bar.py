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
from hyprbar.widgets import createWidget  # pyright: ignore # noqa


hyprBarConfig = None
components = []
index = 0


def on_activate(app):
    window = Gtk.Window(application=app)
    window.set_name("hyprbar")
    # Carregar CSS
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(f"{STYLE_FILE}")
    display = window.get_display()
    Gtk.StyleContext.add_provider_for_display(
        display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    window.set_default_size(hyprBarConfig.window.width, hyprBarConfig.window.height)  # pyright: ignore # noqa

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
    mainBox.set_homogeneous(True)

    window.set_child(mainBox)

    # Enable Exclusive Zone
    LayerShell.auto_exclusive_zone_enable(window)

    leftGtkBox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=hyprBarConfig.window.left_container.hor_spacing,  # pyright: ignore # noqa
    )
    leftGtkBox.set_halign(Gtk.Align.START)
    leftGtkBox.set_valign(Gtk.Align.CENTER)

    centerGtkBox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=hyprBarConfig.window.center_container.hor_spacing,  # pyright: ignore # noqa
    )  # pyright: ignore # noqa
    centerGtkBox.set_halign(Gtk.Align.CENTER)
    centerGtkBox.set_valign(Gtk.Align.CENTER)
    rightGtkBox = Gtk.Box(
        orientation=Gtk.Orientation.HORIZONTAL,
        spacing=hyprBarConfig.window.right_container.hor_spacing,  # pyright: ignore # noqa
    )  # pyright: ignore # noqa
    rightGtkBox.set_halign(Gtk.Align.END)
    rightGtkBox.set_valign(Gtk.Align.CENTER)

    mainBox.append(leftGtkBox)
    mainBox.append(centerGtkBox)
    mainBox.append(rightGtkBox)

    populateBox(leftGtkBox, hyprBarConfig.window.left_container.components)  # pyright: ignore # noqa
    populateBox(centerGtkBox, hyprBarConfig.window.center_container.components)  # pyright: ignore # noqa
    populateBox(rightGtkBox, hyprBarConfig.window.right_container.components)  # pyright: ignore # noqa

    window.present()


# TODO: função necessária
#  GLib.timeout_add_seconds(component.refresh, update_label)
def populateBox(box, components):
    for comp in components:
        widget = createWidget(comp)
        widget.set_name(comp.css_id)  # pyright: ignore # noqa
        # if Markup: Ok, set_markup
        if comp.markup:
            widget.set_markup(comp.markup)

        # HACK: Se há refresh precisa criar uma thread aqui
        if comp.refresh > 0:
            pass
        if widget:
            box.append(widget)  # Para GTK4, use append


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
