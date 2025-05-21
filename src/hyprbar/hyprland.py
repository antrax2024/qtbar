from hyprpy import Hyprland
from hyprpy.components import workspaces


instance = Hyprland()
# Print information about the windows on the active workspace
# workspace = instance.get_active_workspace()


if __name__ == "__main__":
    workspaces = instance.get_workspaces()
    for workspace in workspaces:
        print()
