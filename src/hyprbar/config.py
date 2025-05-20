# Config File Classes and Functions
#
# This module defines the configuration structure for qtbar using confz.
# confz provides type validation and default values for configuration parameters.
#
from confz import BaseConfig, FileSource
from hyprbar.constants import CONFIG_FILE
from typing import List, Optional


class ComponentConfig(BaseConfig):
    type: str  # label, button, progressbar, etc.
    text: Optional[str] = None
    value: Optional[str] = None  # Para progressbar, etc.
    on_click: Optional[str] = None  # Para ações de botão


class ContainerConfig(BaseConfig):
    components: List[ComponentConfig] = []


class WindowConfig(BaseConfig):
    """
    Configuration class for window appearance settings.

    Attributes:
        width (int): The width of the window in pixels. Default: 400
        height (int): The height of the window in pixels. Default: 150
    """

    anchor: str
    margin_bottom: int
    margin_top: int
    width: int
    height: int

    left_container: ContainerConfig
    center_container: ContainerConfig
    right_container: ContainerConfig


class HyprbarConfig(BaseConfig):
    """
    Main configuration class for qtbar.

    Attributes:
        window (WindowConfig): Window-specific configuration settings
    """

    CONFIG_SOURCES = FileSource(CONFIG_FILE)
    window: WindowConfig
