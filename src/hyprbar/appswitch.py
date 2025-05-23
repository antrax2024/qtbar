# this class is reponsible for appswitch hyprbar module
#
#
from hyprbar.config import ComponentConfig
from typing import List, Tuple
from hyprpy import Hyprland
from rich.console import Console
from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import GLib  # pyright: ignore # noqa
from gi.repository import Pango  # pyright: ignore # noqa

cl = Console()


class AppSwitch:
    hyprland = Hyprland()  # instance of Hyprland
    overview: List[
        Tuple
    ] = []  # array of tuples with workspace id and number of windows
    refresh: int = 300  # 300 miliseconds

    def init__(self, config: ComponentConfig) -> None:
        self.config = config
        self.updateAppSwitch()  # call updateAppSwitch to initialize the app switch

    def updateAppSwitch(self) -> bool:
        # get current workspace
        workspace = self.hyprland.get_active_workspace()
        for window in workspace.windows:
            cl.print(f"Window: {window.__dict__}")
            app_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            # Try to get app icon
            icon = Gtk.Image()
            icon.set_from_icon_name(window.wm_class.lower())
            # Create label for app title
            label = Gtk.Label(label=window.title)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_max_width_chars(20)

            # Pack icon and label into app_box
            app_box.append(icon)
            app_box.append(label)

            # Create button with the box as content
            button = Gtk.Button()
            button.set_child(app_box)
            button.set_name(f"app-{window.pid}")
            button.add_css_class("appswitch")
            # Add click event to focus the window
            button.connect(
                "clicked",
                lambda btn, win_addr=window.address: executeCommand(
                    f"hyprctl dispatch focuswindow address:{win_addr}"
                ),
            )

            box.append(button)

        return True
