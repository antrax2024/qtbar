# Config File Classes and Functions
#
# This module defines the configuration structure for qtbar using confz.
# confz provides type validation and default values for configuration parameters.
#
from confz import BaseConfig, FileSource
from hyprbar.constants import CONFIG_FILE
from typing import Literal, Union, Optional, List


class ComponentConfig(BaseConfig):
    type: str


class AppSwitchConfig(ComponentConfig):
    type: Literal["appswitch"]  # pyright: ignore # noqa
    workspaces: int = 1  # number of workspaces to display windows
    css_id: Optional[str] = None  # css id for the component


class KernelConfig(ComponentConfig):
    type: Literal["kernel"]  # pyright: ignore # noqa
    icon: Optional[str] = None  # icon  nerd font or emoji
    command: Optional[str] = "uname -r"  # command to run
    css_id: Optional[str] = None  # css id for the component
    refresh: int = 60  # refresh time in seconds


class WorkspacesConfig(ComponentConfig):
    type: Literal["workspaces"]  # pyright: ignore # noqa
    ids: List[str]  # list with workspaces identifiers
    css_id: Optional[str] = None  # css id for the component


class ClockConfig(ComponentConfig):
    type: Literal["clock"]  # pyright: ignore # noqa
    icon: Optional[str] = None  # nerd font or emoji
    format: Optional[str] = "%H:%M:%S"
    css_id: Optional[str] = None
    refresh: Optional[int] = 1


ComponentUnion = Union[AppSwitchConfig, KernelConfig, WorkspacesConfig, ClockConfig]


class ContainerConfig(BaseConfig):
    hor_spacing: int = 4  # horizontal spacing
    components: List[ComponentUnion] = []


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
