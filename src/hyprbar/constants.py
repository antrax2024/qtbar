import os

APP_VERSION = "0.0.3"
APP_NAME = "hyprbar"

SPACES_DEFAULT = 15

CONFIG_DIR = os.path.join(os.path.expanduser(path="~"), ".config", f"{APP_NAME}")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")

WINDOW_RULES = [
    "hyprctl dispatch focuswindow class:hyprbar",
    "hyprctl dispatch togglefloating",
]
