# this class is reponsible for appswitch hyprbar module
#
#
from hyprbar.config import ComponentConfig
from typing import List, Tuple
from hyprpy import Hyprland


class AppSwitch:
    hyprland = Hyprland()  # instance of Hyprland
    overview: List[
        Tuple
    ] = []  # array of tuples with workspace id and number of windows
    refresh: int = 300  # 300 miliseconds

    def init__(self, config: ComponentConfig) -> None:
        self.config = config

    def updateAppSwitch(self) -> bool:
        return True
