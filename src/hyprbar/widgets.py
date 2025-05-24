from typing import List
from datetime import datetime
from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import GLib  # pyright: ignore # noqa
from gi.repository import Pango  # pyright: ignore # noqa
from hyprbar.util import printLog, executeCommand
from hyprpy import Hyprland
from rich.console import Console
from hyprbar.config import ComponentConfig
from hyprbar.appswitch import AppSwitch


cl = Console()
instance = Hyprland()
workspaces = []
currentWorkspaceID = 1


def populateBox(box: Gtk.Box, components: List[ComponentConfig]) -> None:
    printLog(f"Populating box => {box} with components")
    for comp in components:
        if comp.type == "workspaces":
            printLog("Creating workspaces component...")
            createWorkspacesComponent(box=box, component=comp)  # pyright: ignore # noqa
        elif comp.type == "appswitch":
            printLog("Creating app switch component...")
            AppSwitch(box, comp)
        elif comp.type == "clock":
            printLog(f"Creating clock component => {comp.icon}")  # pyright: ignore # noqa
            createClockComponent(
                box=box,
                comp=comp,
            )
        elif comp.type == "kernel":
            printLog("Creating kernel component...")
            createKernelComponent(box=box, component=comp)


def getKernelVersion(command: str) -> str:
    code, out, error = executeCommand(command=command)
    if code == 0:
        return "".join(c for c in out if c not in "\n\r")
    else:
        printLog(f"Error getting kernel version: {error}")
        return f"{error}"


def updateKernel(label: Gtk.Label, command: str) -> bool:
    label.set_text(getKernelVersion(command=command))
    return True


def createKernelComponent(box: Gtk.Box, component: ComponentConfig) -> None:
    kernelIcon = Gtk.Label(label=f"{component.icon}")  # pyright: ignore # noqa
    kernelIcon.set_name(f"{component.css_id}-icon")  # pyright: ignore # noqa
    kernelLabel = Gtk.Label(label=getKernelVersion(command=component.command))  # pyright: ignore # noqa
    kernelLabel.set_name(f"{component.css_id}-label")  # pyright: ignore # noqa

    box.append(kernelIcon)
    box.append(kernelLabel)

    # Update every refresh time
    GLib.timeout_add(
        component.refresh,  # pyright: ignore # noqa
        lambda: updateKernel(label=kernelLabel, command=component.command),  # pyright: ignore # noqa
    )


def updateWorkspaces() -> bool:
    global currentWorkspaceID
    wk = instance.get_active_workspace()
    if wk.id <= len(workspaces):
        if wk.id != currentWorkspaceID:
            # Remove active class
            GLib.idle_add(
                workspaces[currentWorkspaceID - 1].remove_css_class, "workspace-active"
            )
            currentWorkspaceID = wk.id
            # add css class
            GLib.idle_add(
                workspaces[currentWorkspaceID - 1].add_css_class, "workspace-active"
            )

    return True


def createWorkspacesComponent(box, component: ComponentConfig) -> None:
    global workspaces
    global currentWorkspaceID
    workspaces.clear()  # Limpa workspaces anterior
    for index, id in enumerate(component.ids):  # pyright: ignore # noqa
        label = Gtk.Label(label=f"{id}")
        # css id for the workspace
        label.set_name(f"{component.css_id}-{index + 1}")  # pyright: ignore # noqa
        label.add_css_class("workspace-hover")
        workspaces.append(label)
        box.append(label)

    activeWorkspace = instance.get_active_workspace()
    currentWorkspaceID = activeWorkspace.id
    # Update every second (100ms)
    GLib.timeout_add(100, updateWorkspaces)
    # add active class
    GLib.idle_add(workspaces[currentWorkspaceID - 1].add_css_class, "workspace-active")


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
