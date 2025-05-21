from gi.repository import Gtk  # pyright: ignore #noqa


# TODO: Criar um componente do tipo workspace
# Definir uma prop refresh que cria uma thread e atualiza o widget
# definir um componente de clock que atualiza a cada disparo da thead
# label.set_markup('<span foreground="purple">Temperatura:</span> <span foreground="green">20°C</span>')


def createWidget(component):
    if component.type == "workspaces":
        pass

    elif component.type == "label":
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
