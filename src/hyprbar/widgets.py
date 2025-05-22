from typing import List, Any
import threading
import time
from gi.repository import Gtk  # pyright: ignore #noqa
from gi.repository import GLib  # pyright: ignore # noqa
from hyprbar.config import ComponentConfig
from hyprpy import Hyprland

instance = Hyprland()
workspaces = []
currentWorkspaceID = 1


# TODO: Criar um componente do tipo workspace
# Definir uma prop refresh que cria uma thread e atualiza o widget
# definir um componente de clock que atualiza a cada disparo da thead
# label.set_markup('<span foreground="purple">Temperatura:</span> <span foreground="green">20°C</span>')


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
        else:
            widget = createWidget(comp)
            widget.set_name(comp.css_id)  # pyright: ignore # noqa
            if widget:
                box.append(widget)  # Para GTK4, use append
            # if Markup: Ok, set_markup
            if comp.markup:
                widget.set_markup(comp.markup)  # pyright: ignore # noqa

        # HACK: Se há refresh precisa criar uma thread aqui
        # if comp.refresh > 0:
        #     pass
        #


def workspaceAddActiveClass() -> None:
    GLib.idle_add(workspaces[currentWorkspaceID - 1].add_css_class, "active")


def workspacesThread() -> None:
    global currentWorkspaceID
    while True:
        wk = instance.get_active_workspace()
        if wk.id > len(workspaces):
            print("Daria um out off range... faço nada...")
        else:
            if wk.id != currentWorkspaceID:
                # Remove active class
                GLib.idle_add(
                    workspaces[currentWorkspaceID - 1].remove_css_class, "active"
                )
                currentWorkspaceID = wk.id
                # add css class
                workspaceAddActiveClass()

        time.sleep(0.1)


def updateWorkspace(id: int):
    global currentWorkspaceID
    # Atualiza a interface na thread principal
    GLib.idle_add(workspaces[id - 1].set_text, "gonha")
    currentWorkspaceID = id


def createWorkspacesComponent(box, workspace_text: str):
    global workspaces
    global currentWorkspaceID
    wks = workspace_text.split(",")

    workspaces.clear()  # Limpa workspaces anterior
    for wk in wks:
        label = Gtk.Label(label=f"{wk}")
        label.set_name(f"workspace-{len(workspaces)}")
        workspaces.append(label)
        box.append(label)

    activeWorkspace = instance.get_active_workspace()
    currentWorkspaceID = activeWorkspace.id
    workspaceAddActiveClass()
    updateWorkspace(activeWorkspace.id)
    # Start worspaces thread
    thread = threading.Thread(target=workspacesThread, daemon=True)
    thread.start()
