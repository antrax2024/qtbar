import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gio, GLib, GdkPixbuf, Gdk  # pyright: ignore # noqa


class TrayIconManager:
    def __init__(self, tray_box: Gtk.Box):
        self.tray_box = tray_box
        self.status_notifier_items = {}  # service_name -> {proxy, widget, signals_ids}
        self._dbus_connection = None
        self._watcher_proxy = None
        self._watcher_signal_handlers = []

        self._init_dbus()
        self._init_watcher()

    def _init_dbus(self):
        try:
            self._dbus_connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error as e:
            print(f"Erro ao conectar ao D-Bus: {e}")
            return

    def _init_watcher(self):
        if not self._dbus_connection:
            print("Conexão D-Bus não disponível para iniciar o watcher.")
            return

        # Tenta primeiro o watcher do KDE, depois o freedesktop padrão
        watcher_specs = [
            {
                "bus_name": "org.kde.StatusNotifierWatcher",
                "object_path": "/StatusNotifierWatcher",
                "interface_name": "org.kde.StatusNotifierWatcher",  # Interface primária para este serviço
            },
            {
                "bus_name": "org.freedesktop.StatusNotifierWatcher",
                "object_path": "/StatusNotifierWatcher",
                "interface_name": "org.freedesktop.StatusNotifierWatcher",
            },
        ]

        # A interface padrão para sinais e propriedades que vamos usar
        self.standard_watcher_interface = "org.freedesktop.StatusNotifierWatcher"

        for spec in watcher_specs:
            try:
                # Verifica se o serviço está ativo no D-Bus
                name_owner_variant = self._dbus_connection.call_sync(
                    "org.freedesktop.DBus",
                    "/org/freedesktop/DBus",
                    "org.freedesktop.DBus",
                    "GetNameOwner",
                    GLib.Variant("(s)", (spec["bus_name"],)),
                    GLib.VariantType("(s)"),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                )

                if name_owner_variant:  # Se o serviço existe
                    self._watcher_proxy = Gio.DBusProxy.new_sync(
                        self._dbus_connection,
                        Gio.DBusProxyFlags.NONE,
                        None,  # Gio.DBusInterfaceInfo (opcional)
                        spec["bus_name"],
                        spec["object_path"],
                        spec["interface_name"],  # Interface para criação do proxy
                        None,  # GCancellable
                    )
                    print(f"Conectado ao StatusNotifierWatcher: {spec['bus_name']}")
                    break
            except GLib.Error as e:
                print(
                    f"Falha ao criar proxy para {spec['bus_name']} (interface {spec['interface_name']}): {e}"
                )
                self._watcher_proxy = None

        if not self._watcher_proxy:
            print("Não foi possível conectar a nenhum serviço StatusNotifierWatcher.")
            return

        # Conecta aos sinais usando a interface padrão
        # Usamos g-signal que é mais genérico e lida com as assinaturas automaticamente
        handler_id = self._watcher_proxy.connect("g-signal", self._on_watcher_signal)
        self._watcher_signal_handlers.append(handler_id)

        try:
            # Obtém itens já registrados usando a interface padrão
            # A propriedade está na interface org.freedesktop.StatusNotifierWatcher
            registered_items_variant = self._watcher_proxy.get_cached_property(
                "RegisteredStatusNotifierItems"
            )
            if registered_items_variant:
                service_names = registered_items_variant.get_strv()
                print(f"Itens de bandeja iniciais: {service_names}")
                for service_name in service_names:
                    self._add_tray_item(service_name)
            else:
                print(
                    "Nenhum item de bandeja registrado inicialmente ou propriedade não disponível."
                )
        except GLib.Error as e:
            print(f"Erro ao obter RegisteredStatusNotifierItems: {e}")

    def _on_watcher_signal(self, proxy, sender_name, signal_name, parameters):
        # parameters é um GVariant tuple
        if signal_name == "StatusNotifierItemRegistered":
            service_name = parameters.get_child_value(0).get_string()
            print(f"Sinal D-Bus: Item Registrado: {service_name}")
            GLib.idle_add(self._add_tray_item, service_name)
        elif signal_name == "StatusNotifierItemUnregistered":
            service_name = parameters.get_child_value(0).get_string()
            print(f"Sinal D-Bus: Item Desregistrado: {service_name}")
            GLib.idle_add(self._remove_tray_item, service_name)

    def _add_tray_item(
        self, service_name: str, object_path: str = "/StatusNotifierItem"
    ):
        if not self._dbus_connection:
            print(f"Não é possível adicionar {service_name}: conexão D-Bus perdida.")
            return
        if service_name in self.status_notifier_items:
            print(f"Item {service_name} já adicionado.")
            return

        item_interface_name = "org.freedesktop.StatusNotifierItem"
        try:
            item_proxy = Gio.DBusProxy.new_sync(
                self._dbus_connection,
                Gio.DBusProxyFlags.NONE,
                None,
                service_name,
                object_path,
                item_interface_name,
                None,
            )
        except GLib.Error as e:
            print(
                f"Falha ao criar proxy D-Bus para o item {service_name} em {object_path}: {e}"
            )
            return

        icon_widget = Gtk.Image(pixel_size=24)  # Ou Gtk.Button
        self._update_item_icon(item_proxy, icon_widget)
        self._update_item_tooltip(item_proxy, icon_widget)

        event_controller = Gtk.GestureClick.new()
        event_controller.connect(
            "pressed", self._on_item_clicked, item_proxy, icon_widget
        )
        icon_widget.add_controller(event_controller)

        self.tray_box.append(icon_widget)

        item_data = {
            "proxy": item_proxy,
            "widget": icon_widget,
            "service_name": service_name,
            "object_path": object_path,
            "signal_handler_id": None,
            "event_controller": event_controller,
        }

        handler_id = item_proxy.connect("g-signal", self._on_item_signal, item_data)
        item_data["signal_handler_id"] = handler_id

        self.status_notifier_items[service_name] = item_data
        print(f"Adicionado item de bandeja: {service_name}")

    def _remove_tray_item(self, service_name: str):
        if service_name in self.status_notifier_items:
            item_data = self.status_notifier_items.pop(service_name)
            widget = item_data["widget"]
            proxy = item_data["proxy"]

            if item_data.get("signal_handler_id"):
                try:
                    proxy.disconnect(item_data["signal_handler_id"])
                except Exception as e:
                    print(f"Erro ao desconectar sinal do item {service_name}: {e}")

            if item_data.get("event_controller"):
                widget.remove_controller(item_data["event_controller"])

            self.tray_box.remove(widget)
            print(f"Removido item de bandeja: {service_name}")
        else:
            print(f"Tentativa de remover item de bandeja inexistente: {service_name}")

    def _on_item_signal(self, proxy, sender, signal_name, parameters, item_data):
        widget = item_data["widget"]
        # Certifique-se de que as atualizações da UI ocorram no thread principal
        if (
            signal_name == "NewIcon"
            or signal_name == "NewAttentionIcon"
            or signal_name == "NewOverlayIcon"
        ):
            GLib.idle_add(self._update_item_icon, proxy, widget)
        elif signal_name == "NewToolTip":
            GLib.idle_add(self._update_item_tooltip, proxy, widget)
        elif signal_name == "NewStatus":
            status = parameters.get_child_value(0).get_string()
            print(f"Item {item_data['service_name']} novo status: {status}")
            # Você pode querer mudar a aparência do ícone com base no status
            # (ex: "NeedsAttention" vs "Passive")

    def _update_item_icon(self, item_proxy, icon_widget: Gtk.Image):
        pixbuf = None
        try:
            # 1. Tentar IconPixmap (array de (iiay) - int, int, array de bytes)
            icon_pixmap_variant = item_proxy.get_cached_property("IconPixmap")
            if icon_pixmap_variant:
                pixmap_array = (
                    icon_pixmap_variant.get_variant()
                )  # GVariant do tipo a(iiay)
                if pixmap_array and pixmap_array.n_children() > 0:
                    # Escolher o melhor pixmap (ex: mais próximo de 24x24)
                    best_pixmap_data = None
                    target_size = (
                        icon_widget.get_pixel_size()
                    )  # Usar o tamanho do Gtk.Image
                    min_diff = float("inf")

                    for i in range(pixmap_array.n_children()):
                        struct = pixmap_array.get_child_value(
                            i
                        )  # GVariant do tipo (iiay)
                        width = struct.get_child_value(0).get_int32()
                        height = struct.get_child_value(1).get_int32()

                        current_diff = abs(width - target_size) + abs(
                            height - target_size
                        )
                        if best_pixmap_data is None or current_diff < min_diff:
                            min_diff = current_diff
                            data_bytes_variant = struct.get_child_value(
                                2
                            )  # GVariant do tipo ay
                            # data_bytes = data_bytes_variant.get_data() # get_data() -> bytes
                            data_bytes = bytes(data_bytes_variant.get_bytestring())

                            best_pixmap_data = (width, height, data_bytes)

                    if best_pixmap_data:
                        w, h, data = best_pixmap_data
                        # Dados são ARGB32
                        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                            GLib.Bytes.new(data),
                            GdkPixbuf.Colorspace.RGB,
                            True,  # has_alpha
                            8,  # bits_per_sample
                            w,
                            h,
                            w * 4,  # rowstride (4 bytes por pixel para ARGB32)
                        )
            if pixbuf:
                icon_widget.set_from_pixbuf(pixbuf)
                return

            # 2. Fallback para IconName (string)
            icon_name_variant = item_proxy.get_cached_property("IconName")
            if icon_name_variant:
                icon_name = icon_name_variant.get_string()
                if icon_name:
                    icon_widget.set_from_icon_name(icon_name)
                    # icon_widget.set_pixel_size(24) # Já definido no construtor
                    return

            # 3. Fallback para um ícone "missing"
            print(
                f"Nenhum ícone utilizável encontrado para {item_proxy.get_name()}. Usando 'image-missing'."
            )
            icon_widget.set_from_icon_name("image-missing")

        except GLib.Error as e:
            print(f"Erro ao atualizar ícone para {item_proxy.get_name()}: {e}")
            icon_widget.set_from_icon_name(
                "image-missing"
            )  # Ícone de fallback em caso de erro
        except Exception as ex:
            print(f"Exceção inesperada ao atualizar ícone: {ex}")
            icon_widget.set_from_icon_name("image-missing")

    def _update_item_tooltip(self, item_proxy, icon_widget: Gtk.Image):
        try:
            tooltip_variant = item_proxy.get_cached_property(
                "ToolTip"
            )  # Tipo (sa(iiay)ss)
            if tooltip_variant and tooltip_variant.n_children() == 4:
                # (icon_name, icon_data_array, title, text)
                # v_icon_name = tooltip_variant.get_child_value(0).get_string()
                # v_icon_data = tooltip_variant.get_child_value(1) # a(iiay)
                v_title = tooltip_variant.get_child_value(2).get_string()
                v_text = tooltip_variant.get_child_value(3).get_string()

                tooltip_markup = GLib.markup_escape_text(v_title)
                if v_text:
                    tooltip_markup += (
                        f"\n<small>{GLib.markup_escape_text(v_text)}</small>"
                    )

                icon_widget.set_tooltip_markup(
                    tooltip_markup if tooltip_markup else None
                )
            else:
                icon_widget.set_tooltip_text(None)  # Limpa se não houver tooltip
        except GLib.Error as e:
            print(f"Erro ao atualizar tooltip para {item_proxy.get_name()}: {e}")
            icon_widget.set_tooltip_text(None)
        except Exception as ex:
            print(f"Exceção inesperada ao atualizar tooltip: {ex}")
            icon_widget.set_tooltip_text(None)

    def _on_item_clicked(
        self,
        gesture: Gtk.GestureClick,
        n_press: int,
        x: int,
        y: int,
        item_proxy: Gio.DBusProxy,
        widget: Gtk.Widget,
    ):
        # Coordenadas x, y são relativas ao widget
        # O item_proxy e widget são passados como user_data na conexão do sinal "pressed"

        button = gesture.get_current_button()
        # As coordenadas para Activate/ContextMenu são relativas ao ícone.
        # No GTK4, x e y de 'pressed' são relativas ao widget que tem o controller.
        # Para simplificar, passamos (0,0) ou as coordenadas relativas se a API do item as usar.
        # Muitos itens ignoram essas coordenadas.

        if button == Gdk.BUTTON_PRIMARY:  # Botão esquerdo
            try:
                print(f"Ativando item (primário): {item_proxy.get_name()}")
                item_proxy.call_sync(
                    "Activate",
                    GLib.Variant("(ii)", (int(x), int(y))),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                )
            except GLib.Error as e:
                print(f"Erro ao chamar Activate em {item_proxy.get_name()}: {e}")

        elif button == Gdk.BUTTON_SECONDARY:  # Botão direito
            self._show_context_menu(item_proxy, widget, int(x), int(y))

    def _show_context_menu(
        self, item_proxy: Gio.DBusProxy, widget: Gtk.Widget, click_x: int, click_y: int
    ):
        try:
            # Opção 1: Usar a propriedade "Menu" que aponta para um objeto D-Bus com interface com.canonical.dbusmenu
            menu_path_variant = item_proxy.get_cached_property(
                "Menu"
            )  # Tipo 'o' (object_path)
            if menu_path_variant:
                menu_object_path = menu_path_variant.get_string()
                if (
                    menu_object_path and menu_object_path != "/"
                ):  # "/" às vezes significa sem menu
                    print(
                        f"Item {item_proxy.get_name()} tem um menu D-Bus em: {menu_object_path}"
                    )
                    # Implementar a busca e exibição do menu D-Bus (com.canonical.dbusmenu) é complexo.
                    # Requereria chamadas recursivas a GetLayout, GetProperties e construir um Gtk.Menu.
                    # Para este exemplo, vamos pular a implementação completa do D-Bus menu.
                    # Em vez disso, como fallback, podemos chamar o método ContextMenu.
                else:
                    print(
                        f"Item {item_proxy.get_name()} não tem um caminho de menu válido: {menu_object_path}"
                    )

            # Opção 2: Chamar o método "ContextMenu" diretamente no item.
            # Algumas aplicações implementam isso para mostrar seu próprio menu.
            print(f"Tentando chamar ContextMenu em {item_proxy.get_name()}")
            item_proxy.call_sync(
                "ContextMenu",
                GLib.Variant("(ii)", (click_x, click_y)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
            # Nota: Se o item realmente depende do menu D-Bus (com.canonical.dbusmenu)
            # e não implementa o método ContextMenu, isso pode não fazer nada ou dar erro.
            # Uma implementação completa de cliente dbusmenu é um projeto à parte.

        except GLib.Error as e:
            print(
                f"Erro ao tentar mostrar menu de contexto para {item_proxy.get_name()}: {e}"
            )
            # Como último recurso, um menu genérico GTK simples (não recomendado para produção)
            # menu = Gtk.Menu()
            # mi = Gtk.MenuItem(label=f"Ações para {item_proxy.get_property('Id').get_string()}")
            # menu.append(mi)
            # menu.set_parent(widget) # Necessário para popup_at_widget em GTK4
            # menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)

    def shutdown(self):
        print("Desligando TrayIconManager...")
        # Desconectar sinais do watcher
        if self._watcher_proxy:
            for handler_id in self._watcher_signal_handlers:
                try:
                    self._watcher_proxy.disconnect(handler_id)
                except Exception as e:
                    print(f"Erro ao desconectar sinal do watcher: {e}")
            self._watcher_proxy = None
        self._watcher_signal_handlers.clear()

        # Remover todos os itens restantes
        # Iterar sobre uma cópia das chaves, pois _remove_tray_item modifica o dicionário
        for service_name in list(self.status_notifier_items.keys()):
            self._remove_tray_item(service_name)

        self.status_notifier_items.clear()

        # A conexão D-Bus é geralmente compartilhada e não precisa ser fechada aqui,
        # a menos que seja criada exclusivamente para esta classe.
        # Gio.bus_get_sync retorna uma conexão gerenciada.
        print("TrayIconManager desligado.")
