import os

APP_VERSION = "0.0.2"
APP_NAME = "qtbar"

SPACES_DEFAULT = 15

CONFIG_DIR = os.path.join(os.path.expanduser(path="~"), ".config", f"{APP_NAME}")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
