# this class is reponsible for appswitch hyprbar module
# This is Gtk4 based component that displays a list of open applications
#
from hyprbar.config import ComponentConfig
from typing import List
from hyprpy import Hyprland
from hyprbar.util import executeCommand
from rich.console import Console
from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import GLib  # pyright: ignore # noqa
from gi.repository import Pango  # pyright: ignore # noqa

cl = Console()


class AppSwitch:
    hyprland = Hyprland()  # instance of Hyprland
    windowsAddresses: List[str] = []
    refresh: int = 100  # 100 miliseconds

    def __init__(self, box: Gtk.Box, config: ComponentConfig) -> None:
        self.box = box
        self.config = config
        # self.updateAppSwitch()
        GLib.timeout_add(
            self.refresh,
            lambda: self.updateAppSwitch(),
        )

    def removeButtonByName(self, name):
        child = self.box.get_first_child()
        while child:
            if child.get_name() == name:
                self.box.remove(child)
                break
            child = child.get_next_sibling()

    def updateAppSwitch(self) -> bool:
        # Get current windows and their addresses
        current_windows = self.hyprland.get_windows()
        current_addresses = [window.address for window in current_windows]

        # Remove buttons for closed windows
        closed_addresses = [
            addr for addr in self.windowsAddresses if addr not in current_addresses
        ]
        for address in closed_addresses:
            self.removeButtonByName(address)
            self.windowsAddresses.remove(address)

        # Add buttons for new windows
        for window in current_windows:
            if window.address not in self.windowsAddresses:
                self.windowsAddresses.append(window.address)
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
                button.set_name(f"{window.address}")
                button.add_css_class("appswitch")
                # Add click event to focus the window
                button.connect(
                    "clicked",
                    lambda _, win_addr=window.address: executeCommand(
                        f"hyprctl dispatch focuswindow address:{win_addr}"
                    ),
                )

                self.box.append(button)

        return True
