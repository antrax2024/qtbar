from typing import List
import threading
import time
from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import GLib  # pyright: ignore # noqa
from hyprbar.config import ComponentConfig
from hyprpy import Hyprland

instance = Hyprland()
workspaces = []
currentWorkspaceID = 1


def createWidget(component):
    if component.type == "label":
        return Gtk.Label(label=component.text)
    elif component.type == "button":
        btn = Gtk.Button(label=component.text)
        # Aqui você pode conectar o sinal "clicked" a uma função baseada no on_click
        return btn
    elif component.type == "progressbar":
        pb = Gtk.ProgressBar()
        # Defina o valor conforme necessário
        return pb

    # Adicione outros tipos conforme necessário

    return None


def populateBox(box: Gtk.Box, components: List[ComponentConfig]):
    for comp in components:
        if comp.type == "workspaces":
            createWorkspacesComponent(box=box, workspace_text=comp.text)  # pyright: ignore # noqa
        elif comp.type == "clock":
            createClockComponent(
                box=box,
                icon=comp.icon,  # pyright: ignore # noqa
                format=comp.format,  # pyright: ignore # noqa
                refresh=comp.refresh,  # pyright: ignore # noqa
                css_id=comp.css_id,  # pyright: ignore # noqa
            )
        else:
            widget = createWidget(comp)
            widget.set_name(comp.css_id)  # pyright: ignore # noqa
            if widget:
                box.append(widget)  # Para GTK4, use append
            # if Markup: Ok, set_markup
            if comp.markup:
                widget.set_markup(comp.markup)  # pyright: ignore # noqa


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


def createClockComponent(
    box: Gtk.Box,
    icon: str,
    format: str,
    css_id: str,
    refresh: int = 1,
):
    iconLabel = Gtk.Label(label=f"{icon}")
    iconLabel.set_name(f"{css_id}-icon")
    clockLabel = Gtk.Label()
    clockLabel.set_name(f"{css_id}-label")

    thread = threading.Thread(
        target=clockThread,
        args=(clockLabel, format, refresh),
        daemon=True,
    )
    thread.start()
    box.append(iconLabel)
    box.append(clockLabel)


def createCPUComponent() -> None:
    pass
