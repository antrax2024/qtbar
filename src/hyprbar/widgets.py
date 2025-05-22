from typing import List
from datetime import datetime
from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import GLib  # pyright: ignore # noqa
from hyprbar.util import printLog
from hyprpy import Hyprland

from hyprbar.config import ComponentConfig

instance = Hyprland()
workspaces = []
currentWorkspaceID = 1


def populateBox(box: Gtk.Box, components: List[ComponentConfig]) -> None:
    printLog(f"Populating box => {box} with components")
    for comp in components:
        if comp.type == "workspaces":
            printLog(f"Creating workspaces component...")  # pyright: ignore # noqa
            createWorkspacesComponent(box=box, component=comp)  # pyright: ignore # noqa
        elif comp.type == "clock":
            printLog(f"Creating clock component => {comp.icon}")  # pyright: ignore # noqa
            createClockComponent(
                box=box,
                comp=comp,
            )
        elif comp.type == "label":
            printLog(f"Creating label component => {comp.text}")  # pyright: ignore # noqa
            print(f"Label: {comp.text}")  # pyright: ignore # noqa


def updateWorkspaces() -> bool:
    global currentWorkspaceID
    wk = instance.get_active_workspace()
    if wk.id <= len(workspaces):
        if wk.id != currentWorkspaceID:
            # Remove active class
            GLib.idle_add(workspaces[currentWorkspaceID - 1].remove_css_class, "active")
            currentWorkspaceID = wk.id
            # add css class
            GLib.idle_add(workspaces[currentWorkspaceID - 1].add_css_class, "active")

    return True


def createWorkspacesComponent(box, component: ComponentConfig):
    global workspaces
    global currentWorkspaceID
    workspaces.clear()  # Limpa workspaces anterior
    for index, id in enumerate(component.ids):  # pyright: ignore # noqa
        label = Gtk.Label(label=f"{id}")
        # css id for the workspace
        label.set_name(f"{component.css_id}-{index + 1}")  # pyright: ignore # noqa
        label.add_css_class("hover")
        workspaces.append(label)
        box.append(label)

    activeWorkspace = instance.get_active_workspace()
    currentWorkspaceID = activeWorkspace.id
    # Update every second (100ms)
    GLib.timeout_add(100, updateWorkspaces)
    # add active class
    GLib.idle_add(workspaces[currentWorkspaceID - 1].add_css_class, "active")


def clockUpdate(clockLabel: Gtk.Label, format: str) -> bool:
    current_time = datetime.now().strftime(format)
    GLib.idle_add(clockLabel.set_text, current_time)
    return True  # Continua chamando periodicamente


def createClockComponent(box: Gtk.Box, comp: ComponentConfig):
    iconLabel = Gtk.Label(label=f"{comp.icon}")  # pyright: ignore # noqa
    iconLabel.set_name(f"{comp.css_id}-icon")  # pyright: ignore # noqa
    clockLabel = Gtk.Label(label=datetime.now().strftime(comp.format))  # pyright: ignore # noqa
    clockLabel.set_name(f"{comp.css_id}-label")  # pyright: ignore # noqa

    printLog(f"Starting thread for clock component...")  # pyright: ignore # noqa
    # Update every second (1000ms)
    GLib.timeout_add(
        1000,
        lambda: clockUpdate(clockLabel, comp.format),  # pyright: ignore # noqa
    )  # Atualiza a cada 1 segundo

    printLog(f"Append icon and label to box...")  # pyright: ignore # noqa
    box.append(iconLabel)
    box.append(clockLabel)


def createCPUComponent() -> None:
    pass
