from hyprbar.config import ComponentConfig
from rich.console import Console
from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import GLib  # pyright: ignore # noqa


cl = Console()


class Tray:
    refresh: int = 1000  # 100 milliseconds

    def __init__(self, box: Gtk.Box, config: ComponentConfig) -> None:
        self.box = box
        self.config = config

        GLib.timeout_add(
            self.refresh,
            lambda: self.updateTray(),
        )

    def updateTray(self):
        return True
