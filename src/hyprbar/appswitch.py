# this class is reponsible for appswitch hyprbar module
# This is Gtk4 based component that displays a list of open applications
#
from hyprpy.components import workspaces
from hyprbar.config import ComponentConfig
from typing import List, Tuple
from hyprpy import Hyprland
from hyprbar.util import executeCommand
from rich.console import Console
from rich import inspect
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
        # get current workspace
        workspace = self.hyprland.get_active_workspace()
        numberOfWindows = 0
        for window in workspace.windows:
            numberOfWindows += 1
            # cl.print(f"Window: {window.__dict__}")
            # determine if workspace id and window.id exists on self.overview
            # feed self.overview with workspace id and number of windows
            # if window.address exits in self.overview, remove it
            if (workspace.id, window.address) not in self.overview:
                self.overview.append((workspace.id, window.address))
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
                button.set_name(f"{window.pid}")
                button.add_css_class("appswitch")
                # Add click event to focus the window
                button.connect(
                    "clicked",
                    lambda _, win_addr=window.address: executeCommand(
                        f"hyprctl dispatch focuswindow address:{win_addr}"
                    ),
                )

                self.box.append(button)

            if len(self.overview) > workspace.window_count:
                lastChild = self.box.get_last_child()
                if lastChild:
                    self.box.remove(lastChild)
                    self.overview.pop()

        return True
