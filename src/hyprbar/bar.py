from ctypes import CDLL

CDLL("libgtk4-layer-shell.so")
import gi  # noqa

gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")

from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import Gtk4LayerShell as LayerShell  # pyright: ignore #noqa
from hyprbar.config import HyprbarConfig  # pyright: ignore # noqa
from hyprbar.constants import STYLE_FILE, ANCHOR  # pyright: ignore # noqa


hyprBarConfig = None


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

    # buttonLeft = Gtk.Button(label="Left")
    # buttonLeft.set_name("buttonLeft")
    #
    # buttonCenter = Gtk.Button(label="Center")
    # buttonCenter.set_name("buttonCenter")
    #
    # buttonRight = Gtk.Button(label="Right")
    # buttonRight.set_name("buttonRight")

    leftGtkBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    leftGtkBox.set_halign(Gtk.Align.START)
    centerGtkBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    centerGtkBox.set_halign(Gtk.Align.CENTER)
    rightGtkBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    rightGtkBox.set_halign(Gtk.Align.END)

    mainBox.append(leftGtkBox)
    mainBox.append(centerGtkBox)
    mainBox.append(rightGtkBox)

    populate_box(leftGtkBox, hyprBarConfig.window.left_container.components)  # pyright: ignore # noqa
    populate_box(centerGtkBox, hyprBarConfig.window.center_container.components)  # pyright: ignore # noqa
    populate_box(rightGtkBox, hyprBarConfig.window.right_container.components)  # pyright: ignore # noqa

    # leftGtkBox.append(buttonLeft)
    # centerGtkBox.append(buttonCenter)
    # rightGtkBox.append(buttonRight)

    window.present()


def create_widget(component):
    if component.type == "label":
        return Gtk.Label(label=component.text)
    elif component.type == "button":
        btn = Gtk.Button(label=component.text)
        # Aqui você pode conectar o sinal "clicked" a uma função baseada no on_click
        return btn
    elif component.type == "progressbar":
        pb = Gtk.ProgressBar()
        # Defina o valor conforme necessário
        return pb
    # Adicione outros tipos conforme necessário
    return None


def populate_box(box, components):
    for comp in components:
        widget = create_widget(comp)
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
