from gi.repository import Gtk, GLib, Gio  # pyright: ignore # noqa
from hyprbar.config import ComponentConfig
from rich.console import Console


cl = Console()


class Tray:
    refresh: int = 1000  # 100 milliseconds

    def __init__(self, box: Gtk.Box, config: ComponentConfig) -> None:
        # 1. Conecte ao barramento da sessão D-Bus
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.box = box
        self.config = config

        GLib.timeout_add(
            self.refresh,
            lambda: self.updateTray(),
        )

    def updateTray(self):
        return True
