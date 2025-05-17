# Config File Classes and Functions
#
# This module defines the configuration structure for qtbar using confz.
# confz provides type validation and default values for configuration parameters.
#
from confz import BaseConfig, FileSource
from qtbar.constants import CONFIG_FILE


class WindowConfig(BaseConfig):
    """
    Configuration class for window appearance settings.

    Attributes:
        width (int): The width of the window in pixels. Default: 400
        height (int): The height of the window in pixels. Default: 150
    """

    width: int = 400
    height: int = 150


class qtbarConfig(BaseConfig):
    """
    Main configuration class for qtbar.

    Attributes:
        window (WindowConfig): Window-specific configuration settings
    """

    CONFIG_SOURCES = FileSource(CONFIG_FILE)
    window: WindowConfig
