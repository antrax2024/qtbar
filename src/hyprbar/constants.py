import os
from gi.repository import Gtk4LayerShell as LayerShell  # pyright: ignore #noqa

APP_VERSION = "0.0.3"
APP_NAME = "hyprbar"

SPACES_DEFAULT = 15

CONFIG_DIR = os.path.join(os.path.expanduser(path="~"), ".config", f"{APP_NAME}")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
STYLE_FILE = os.path.join(CONFIG_DIR, "styles.css")


ANCHORS = [
    {"top": LayerShell.Edge.TOP},
    {"bottom": LayerShell.Edge.BOTTOM},
]
