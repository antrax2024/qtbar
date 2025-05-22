from typing import List
import threading
import time
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
            printLog(f"Creating workspaces component => {comp.text}")  # pyright: ignore # noqa
            createWorkspacesComponent(box=box, workspace_text=comp.text)  # pyright: ignore # noqa
        elif comp.type == "clock":
            printLog(f"Creating clock component => {comp.icon}")  # pyright: ignore # noqa
            createClockComponent(
                box=box,
                comp=comp,
            )
        elif comp.type == "label":
            printLog(f"Creating label component => {comp.text}")  # pyright: ignore # noqa
            print(f"Label: {comp.text}")  # pyright: ignore # noqa


def workspaceSetActiveClass() -> None:
    GLib.idle_add(workspaces[currentWorkspaceID - 1].add_css_class, "active")


def workspaceResetActiveClass() -> None:
    GLib.idle_add(workspaces[currentWorkspaceID - 1].remove_css_class, "active")


def workspaceSetHoverClass() -> None:
    GLib.idle_add(workspaces[currentWorkspaceID - 1].add_css_class, "hover")


def workspaceResetHoverClass() -> None:
    GLib.idle_add(workspaces[currentWorkspaceID - 1].remove_css_class, "hover")


def workspacesThread() -> None:
    global currentWorkspaceID
    while True:
        wk = instance.get_active_workspace()
        if wk.id <= len(workspaces):
            if wk.id != currentWorkspaceID:
                # Remove active class
                workspaceResetActiveClass()
                currentWorkspaceID = wk.id
                # add css class
                workspaceSetActiveClass()

        time.sleep(0.1)


def createWorkspacesComponent(box, workspace_text: str):
    global workspaces
    global currentWorkspaceID
    wks = workspace_text.split(",")

    workspaces.clear()  # Limpa workspaces anterior
    for wk in wks:
        label = Gtk.Label(label=f"{wk}")
        label.set_name(f"workspace-{len(workspaces)}")
        label.add_css_class("hover")
        workspaces.append(label)
        box.append(label)

    activeWorkspace = instance.get_active_workspace()
    currentWorkspaceID = activeWorkspace.id
    workspaceSetActiveClass()
    # Start worspaces thread
    thread = threading.Thread(target=workspacesThread, daemon=True)
    thread.start()


def clockThread(clockLabel: Gtk.Label, format: str, refresh: int) -> None:
    while True:
        current_time = time.strftime(format)
        GLib.idle_add(clockLabel.set_text, current_time)
        time.sleep(refresh)


def createClockComponent(box: Gtk.Box, comp: ComponentConfig):
    iconLabel = Gtk.Label(label=f"{comp.icon}")  # pyright: ignore # noqa
    iconLabel.set_name(f"{comp.css_id}-icon")  # pyright: ignore # noqa
    clockLabel = Gtk.Label()
    clockLabel.set_name(f"{comp.css_id}-label")  # pyright: ignore # noqa

    printLog(f"Starting thread for clock component...")  # pyright: ignore # noqa
    thread = threading.Thread(
        target=clockThread,
        args=(clockLabel, comp.format, comp.refresh),  # pyright: ignore # noqa
        daemon=True,
    )
    thread.start()
    printLog(f"Append icon and label to box...")  # pyright: ignore # noqa
    box.append(iconLabel)
    box.append(clockLabel)


def createCPUComponent() -> None:
    pass
