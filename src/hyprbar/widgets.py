from typing import List
from gi.repository import Gtk  # pyright: ignore #noqa
from hyprbar.config import ComponentConfig


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


# TODO: função necessária
#  GLib.timeout_add_seconds(component.refresh, update_label)
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


def createWorkspacesComponent(box, workspace_text: str):
    workspaces = workspace_text.split(",")
    for index, workspace in enumerate(workspaces):
        label = Gtk.Label(label=f"{workspace}")
        label.set_name(f"workspace-{index}")
        print(index)
        box.append(label)
