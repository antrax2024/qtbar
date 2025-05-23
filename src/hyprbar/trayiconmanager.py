import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gio, GLib, GdkPixbuf, Gdk  # pyright: ignore # noqa
from hyprbar.util import printLog


class TrayIconManager:
    def __init__(self, tray_box: Gtk.Box):
        self.tray_box = tray_box
        self.status_notifier_items = {}  # full_item_address -> {proxy, widget, signals_ids, etc.}
        self._dbus_connection = None
        self._watcher_proxy = None
        self._watcher_signal_handlers = []

        self._init_dbus()
        self._init_watcher()

    def _init_dbus(self):
        try:
            self._dbus_connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except GLib.Error as e:
            printLog(f"Error connecting to D-Bus: {e}")
            # Consider raising an exception or setting an error state here
            return

    def _init_watcher(self):
        if not self._dbus_connection:
            printLog("D-Bus connection not available to start the watcher.")
            return

        watcher_specs = [
            {
                "bus_name": "org.kde.StatusNotifierWatcher",
                "object_path": "/StatusNotifierWatcher",
                "interface_name": "org.kde.StatusNotifierWatcher",
            },
            {
                "bus_name": "org.freedesktop.StatusNotifierWatcher",
                "object_path": "/StatusNotifierWatcher",
                "interface_name": "org.freedesktop.StatusNotifierWatcher",
            },
        ]

        self.standard_watcher_interface = "org.freedesktop.StatusNotifierWatcher"

        for spec in watcher_specs:
            # Inside _init_watcher, in the loop for spec in watcher_specs:
            try:
                # Try to verify if the service name has an owner on D-Bus
                # This will raise GLib.Error (with GDBus.Error.NameHasNoOwner) if the service is not active.
                name_owner_details_variant = self._dbus_connection.call_sync(
                    "org.freedesktop.DBus",  # Main D-Bus service name
                    "/org/freedesktop/DBus",  # D-Bus service object path
                    "org.freedesktop.DBus",  # D-Bus service interface
                    "GetNameOwner",  # Method to check the owner of a name
                    GLib.Variant(
                        "(s)", (spec["bus_name"],)
                    ),  # Parameters: (string watcher_service_name)
                    GLib.VariantType(
                        "(s)"
                    ),  # Expected return type: tuple containing a string (s)
                    Gio.DBusCallFlags.NONE,
                    1000,  # Timeout in milliseconds (e.g., 1 second)
                    None,  # Cancellable
                )

                # If call_sync didn't raise an error, name_owner_details_variant is a GVariant tuple.
                # The tuple contains the owner name as a string.
                if name_owner_details_variant:
                    # Extract the string from the tuple. The tuple has format (s), so we get the first child.
                    owner_name_str = name_owner_details_variant.get_child_value(
                        0
                    ).get_string()
                    if owner_name_str:  # Check if the owner name is not empty
                        printLog(
                            f"Service {spec['bus_name']} is active, owned by: {owner_name_str}."
                        )
                        # Now, try to create the proxy for the watcher service.
                        self._watcher_proxy = Gio.DBusProxy.new_sync(
                            self._dbus_connection,
                            Gio.DBusProxyFlags.NONE,
                            None,  # Gio.DBusInterfaceInfo
                            spec["bus_name"],  # The watcher service bus name
                            spec["object_path"],  # Its object path
                            spec["interface_name"],  # Its interface
                            None,  # Cancellable
                        )
                        printLog(
                            f"Connected to StatusNotifierWatcher: {spec['bus_name']}"
                        )
                        break  # Successfully connected, exit the loop
                    else:
                        # Rare case for GetNameOwner, which usually returns a valid name or error.
                        printLog(
                            f"Service {spec['bus_name']} GetNameOwner returned an empty owner name."
                        )
                else:
                    # Uncommon case for call_sync to return None without GLib.Error.
                    printLog(
                        f"GetNameOwner for {spec['bus_name']} returned None without explicit GLib.Error."
                    )

            except GLib.Error as e:
                # This block catches:
                # 1. org.freedesktop.DBus.Error.NameHasNoOwner from GetNameOwner.
                # 2. Network errors, timeouts, etc., from GetNameOwner.
                # 3. Errors from Gio.DBusProxy.new_sync if GetNameOwner succeeded but proxy creation failed.
                printLog(
                    f"Could not use service {spec['bus_name']}: {e.message} (Domain: {e.domain}, Code: {e.code})"
                )
                self._watcher_proxy = (
                    None  # Ensure the proxy is None if this attempt fails
                )
        if not self._watcher_proxy:
            printLog("Could not connect to any StatusNotifierWatcher service.")
            return

        handler_id = self._watcher_proxy.connect("g-signal", self._on_watcher_signal)
        self._watcher_signal_handlers.append(handler_id)

        try:
            registered_items_variant = self._watcher_proxy.get_cached_property(
                "RegisteredStatusNotifierItems"
            )
            if registered_items_variant:
                item_addresses = registered_items_variant.get_strv()
                printLog(f"Initial tray items: {item_addresses}")
                for address in item_addresses:
                    # Use GLib.idle_add to queue the addition in the main loop,
                    # ensuring that subsequent UI and D-Bus operations are well-behaved.
                    GLib.idle_add(self._add_tray_item, address)
            else:
                printLog(
                    "No tray items initially registered or property not available."
                )
        except GLib.Error as e:
            printLog(f"Error getting RegisteredStatusNotifierItems: {e}")

    def _on_watcher_signal(self, proxy, sender_name, signal_name, parameters):
        if signal_name == "StatusNotifierItemRegistered":
            full_item_address = parameters.get_child_value(0).get_string()
            printLog(f"D-Bus Signal: Item Registered: {full_item_address}")
            GLib.idle_add(self._add_tray_item, full_item_address)
        elif signal_name == "StatusNotifierItemUnregistered":
            full_item_address = parameters.get_child_value(0).get_string()
            printLog(f"D-Bus Signal: Item Unregistered: {full_item_address}")
            GLib.idle_add(self._remove_tray_item, full_item_address)

    def _add_tray_item(self, full_item_address: str):
        if not self._dbus_connection:
            printLog(f"Cannot add {full_item_address}: D-Bus connection lost.")
            return

        # Parse full_item_address to get service_name and object_path
        # The StatusNotifierWatcher may return the service name and object path concatenated.
        # E.g.: ':1.123/StatusNotifierItem' or ':1.123/org/ayatana/NotificationItem/myitem'
        # The D-Bus service name is the part before the first '/', and the object path is the part after.
        if "/" in full_item_address:
            parts = full_item_address.split("/", 1)
            service_name = parts[0]
            object_path = "/" + parts[1]  # Ensure the path starts with '/'
        else:
            # If there's no '/', assume it's just the service name,
            # and the object path is the default for StatusNotifierItem.
            service_name = full_item_address
            object_path = "/StatusNotifierItem"

        # The key for status_notifier_items should be unique. full_item_address is ideal.
        if full_item_address in self.status_notifier_items:
            printLog(f"Item {full_item_address} already added (using original key).")
            return

        # Validate the parsed service name and object path
        if not Gio.dbus_is_name(service_name):
            printLog(
                f"Invalid D-Bus service name '{service_name}' derived from '{full_item_address}'. Skipping."
            )
            return
        if not GLib.variant_is_object_path(
            object_path
        ):  # GLib.variant_is_object_path requires GLib >= 2.34
            # Simple alternative for object path checking if GLib.variant_is_object_path is not available
            # or for broader compatibility, although strict validation is better.
            # if not (object_path.startswith('/') and object_path != '/'):
            if not object_path.startswith("/"):  # Basic check
                printLog(
                    f"Invalid D-Bus object path '{object_path}' (must start with '/'). Skipping."
                )
                return

        item_interface_name = "org.freedesktop.StatusNotifierItem"
        try:
            printLog(
                f"Trying to create proxy for service: '{service_name}', path: '{object_path}'"
            )
            item_proxy = Gio.DBusProxy.new_sync(
                self._dbus_connection,
                Gio.DBusProxyFlags.NONE,
                None,  # info
                service_name,  # Parsed D-Bus bus name
                object_path,  # Parsed D-Bus object path
                item_interface_name,  # Interface
                None,  # cancellable
            )
        except (
            GLib.Error
        ) as e:  # Catch GLib errors, which may include proxy creation failures
            printLog(
                f"GLib.Error creating D-Bus proxy for service '{service_name}' at '{object_path}': {e}"
            )
            return
        except (
            TypeError
        ) as e:  # Catch the specific TypeError if the constructor returns NULL
            printLog(
                f"TypeError (probably constructor returned NULL) creating proxy for '{service_name}' at '{object_path}': {e}"
            )
            return

        if not item_proxy:  # Double check, although TypeError should catch NULL
            printLog(
                f"Proxy not created (NULL) for '{service_name}' at '{object_path}'."
            )
            return

        icon_widget = Gtk.Image(pixel_size=24)
        self._update_item_icon(item_proxy, icon_widget)
        self._update_item_tooltip(item_proxy, icon_widget)

        event_controller = Gtk.GestureClick.new()
        # Pass item_proxy and icon_widget as user_data to the callback
        event_controller.connect(
            "pressed", self._on_item_clicked, item_proxy, icon_widget
        )
        icon_widget.add_controller(event_controller)

        self.tray_box.append(icon_widget)

        item_data = {
            "proxy": item_proxy,
            "widget": icon_widget,
            "original_address": full_item_address,
            "service_name": service_name,  # Store the parsed service name
            "object_path": object_path,  # Store the parsed object path
            "signal_handler_id": None,
            "event_controller": event_controller,
        }

        # Pass item_data to the item signal callback
        handler_id = item_proxy.connect("g-signal", self._on_item_signal, item_data)
        item_data["signal_handler_id"] = handler_id

        self.status_notifier_items[full_item_address] = (
            item_data  # Use full_item_address as key
        )
        printLog(
            f"Added tray item: {full_item_address} (Service: {service_name}, Path: {object_path})"
        )

    def _remove_tray_item(self, full_item_address: str):
        if full_item_address in self.status_notifier_items:
            item_data = self.status_notifier_items.pop(full_item_address)
            widget = item_data["widget"]
            proxy = item_data["proxy"]

            if item_data.get("signal_handler_id") and proxy:
                try:
                    proxy.disconnect(item_data["signal_handler_id"])
                except (
                    Exception
                ) as e:  # Be more specific with the exception if possible
                    printLog(
                        f"Error disconnecting signal from item {item_data.get('original_address', full_item_address)}: {e}"
                    )

            if item_data.get("event_controller") and widget:
                widget.remove_controller(item_data["event_controller"])

            if widget and widget.get_parent():  # Ensure the widget is still in the box
                self.tray_box.remove(widget)

            printLog(f"Removed tray item: {full_item_address}")
        else:
            printLog(f"Attempt to remove non-existent tray item: {full_item_address}")

    def _on_item_signal(self, proxy, sender_name, signal_name, parameters, item_data):
        # item_data is passed here
        widget = item_data["widget"]
        if not widget or not widget.get_parent():  # Widget may have been removed
            printLog(
                f"Widget for {item_data['original_address']} not found or not parented, skipping signal update {signal_name}."
            )
            # Consider disconnecting the signal here if the item should no longer be managed.
            # if item_data.get("signal_handler_id") and proxy:
            # try:
            # proxy.disconnect(item_data["signal_handler_id"])
            # item_data["signal_handler_id"] = None # Avoid multiple disconnection attempts
            # except Exception as e:
            # printLog(f"Error trying to auto-disconnect signal for orphaned item: {e}")
            return

        if signal_name in ("NewIcon", "NewAttentionIcon", "NewOverlayIcon"):
            GLib.idle_add(self._update_item_icon, proxy, widget)
        elif signal_name == "NewToolTip":
            GLib.idle_add(self._update_item_tooltip, proxy, widget)
        elif signal_name == "NewStatus":
            if parameters and parameters.n_children() > 0:
                status = parameters.get_child_value(0).get_string()
                printLog(f"Item {item_data['original_address']} new status: {status}")

    def _update_item_icon(self, item_proxy, icon_widget: Gtk.Image):
        pixbuf = None
        target_size = icon_widget.get_pixel_size() or 24

        proxy_name = getattr(item_proxy, "get_name", lambda: "unknown proxy")()
        printLog(f"Updating icon for proxy: {proxy_name}")
        printLog(
            f"Interface name for proxy {proxy_name}: {item_proxy.get_interface_name()}"
        )  # Deve ser org.freedesktop.StatusNotifierItem

        # Debug: Listar todas as propriedades em cache para este proxy
        prop_names_variant = item_proxy.get_cached_property_names()
        if prop_names_variant:
            prop_names_list = prop_names_variant.get_strv()
            printLog(
                f"Proxy {proxy_name} available cached properties: {prop_names_list}"
            )
            if not prop_names_list:
                printLog(
                    f"Proxy {proxy_name} - get_cached_property_names() returned an empty list."
                )
        else:
            printLog(f"Proxy {proxy_name} - get_cached_property_names() returned None.")

        # ... (resto do seu código como está) ...
        try:
            # 1. Try IconPixmap first
            icon_pixmap_variant = item_proxy.get_cached_property(
                "IconPixmap"
            )  # Espera-se que seja GVariant do tipo a(iiay)

            # Correção: Verificar o tipo e usar icon_pixmap_variant diretamente
            if icon_pixmap_variant and icon_pixmap_variant.is_of_type(
                GLib.VariantType.new("a(iiay)")
            ):
                # 'icon_pixmap_variant' É o array GVariant. Não chame .get_variant().
                printLog(f"IconPixmap variant (type 'a(iiay)') found for {proxy_name}")

                if (
                    icon_pixmap_variant.n_children() > 0
                ):  # Usar icon_pixmap_variant diretamente
                    printLog(
                        f"IconPixmap has {icon_pixmap_variant.n_children()} entries for {proxy_name}"
                    )  # Usar icon_pixmap_variant
                    best_pixmap_data = None
                    min_diff = float("inf")

                    # Usar icon_pixmap_variant para iterar
                    for i in range(icon_pixmap_variant.n_children()):
                        struct = icon_pixmap_variant.get_child_value(i)
                        width = struct.get_child_value(0).get_int32()
                        height = struct.get_child_value(1).get_int32()

                        printLog(f"Pixmap entry {i}: {width}x{height}")

                        # Validar dimensões
                        if width <= 0 or height <= 0 or width > 512 or height > 512:
                            printLog(
                                f"Invalid dimensions for pixmap entry {i}: {width}x{height}"
                            )
                            continue

                        current_diff = abs(width - target_size) + abs(
                            height - target_size
                        )
                        if best_pixmap_data is None or current_diff < min_diff:
                            min_diff = current_diff
                            data_bytes_variant = struct.get_child_value(
                                2
                            )  # GVariant 'ay'
                            data_bytes = bytes(data_bytes_variant.get_bytestring())

                            expected_size = width * height * 4  # ARGB32
                            if len(data_bytes) == expected_size:
                                best_pixmap_data = (width, height, data_bytes)
                                printLog(
                                    f"Valid pixmap data found for entry {i}: {width}x{height}, {len(data_bytes)} bytes"
                                )
                            else:
                                printLog(
                                    f"Invalid data size for pixmap entry {i}: expected {expected_size}, got {len(data_bytes)}"
                                )

                    if best_pixmap_data:
                        w, h, data = best_pixmap_data
                        try:
                            # Converter ARGB32 para RGBA
                            rgba_data = bytearray(len(data))
                            for idx in range(
                                0, len(data), 4
                            ):  # Renomeado 'i' para 'idx'
                                # Renomeado componentes para clareza e evitar conflito de escopo
                                a_pixel, r_pixel, g_pixel, b_pixel = (
                                    data[idx],
                                    data[idx + 1],
                                    data[idx + 2],
                                    data[idx + 3],
                                )
                                (
                                    rgba_data[idx],
                                    rgba_data[idx + 1],
                                    rgba_data[idx + 2],
                                    rgba_data[idx + 3],
                                ) = (
                                    r_pixel,
                                    g_pixel,
                                    b_pixel,
                                    a_pixel,
                                )  # Ordem para RGBA

                            # Criar pixbuf com dados convertidos
                            # Armazenar em uma variável temporária primeiro
                            current_pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                                GLib.Bytes.new(rgba_data),
                                GdkPixbuf.Colorspace.RGB,
                                True,  # has_alpha
                                8,  # bits_per_sample
                                w,
                                h,
                                w * 4,  # rowstride
                            )

                            # Redimensionar se necessário e atribuir a 'pixbuf'
                            if (
                                target_size != w or target_size != h
                            ):  # Checar ambas as dimensões
                                pixbuf = current_pixbuf.scale_simple(
                                    target_size,
                                    target_size,
                                    GdkPixbuf.InterpType.BILINEAR,
                                )
                            else:
                                pixbuf = current_pixbuf  # Usar o pixbuf como está

                            printLog(
                                f"Successfully created pixbuf from IconPixmap for {proxy_name}"
                            )

                        except (
                            Exception
                        ) as e_pixbuf:  # Nome da variável de exceção mais específico
                            printLog(
                                f"Error creating pixbuf from IconPixmap data for {proxy_name}: {e_pixbuf}"
                            )
                            pixbuf = (
                                None  # Garante que pixbuf seja None em caso de erro
                            )
                else:  # n_children == 0
                    printLog(f"IconPixmap array is empty for {proxy_name}")

            elif (
                icon_pixmap_variant
            ):  # A propriedade existe, mas não é do tipo 'a(iiay)'
                printLog(
                    f"IconPixmap property found for {proxy_name}, but it's of unexpected type: {icon_pixmap_variant.get_type_string()}"
                )
            else:  # A propriedade não existe (retornou None de get_cached_property)
                printLog(f"No IconPixmap property found for {proxy_name}")

            # Se conseguiu criar o pixbuf, usar ele
            if pixbuf:
                icon_widget.set_from_pixbuf(pixbuf)
                printLog(f"Icon set from pixbuf for {proxy_name}")
                return

            # 2. Fallback para IconName
            icon_name_variant = item_proxy.get_cached_property("IconName")
            if icon_name_variant:
                icon_name = icon_name_variant.get_string()
                printLog(f"IconName found for {proxy_name}: '{icon_name}'")
                if icon_name and icon_name.strip():
                    icon_theme = Gtk.IconTheme.get_for_display(
                        Gdk.Display.get_default()  # pyright: ignore
                    )
                    if icon_theme.has_icon(icon_name):
                        icon_widget.set_from_icon_name(icon_name)
                        printLog(f"Icon set from theme for {proxy_name}: {icon_name}")
                        return
                    else:
                        printLog(
                            f"Icon '{icon_name}' not found in theme for {proxy_name}"
                        )
            else:
                printLog(f"No IconName property found for {proxy_name}")

            # 3. Último fallback - tentar AttentionIconName
            # (código para AttentionIconName como no seu arquivo original)
            attention_icon_variant = item_proxy.get_cached_property("AttentionIconName")
            if attention_icon_variant:
                attention_icon = attention_icon_variant.get_string()
                printLog(
                    f"AttentionIconName found for {proxy_name}: '{attention_icon}'"
                )
                if attention_icon and attention_icon.strip():
                    icon_theme = Gtk.IconTheme.get_for_display(
                        Gdk.Display.get_default()  # pyright: ignore
                    )
                    if icon_theme.has_icon(attention_icon):
                        icon_widget.set_from_icon_name(attention_icon)
                        printLog(
                            f"Icon set from attention icon for {proxy_name}: {attention_icon}"
                        )
                        return
                    # Adicionado else para log de ícone de atenção não encontrado no tema
                    else:
                        printLog(
                            f"Attention icon '{attention_icon}' not found in theme for {proxy_name}"
                        )
            # Adicionado else para log de propriedade AttentionIconName não encontrada
            else:
                printLog(f"No AttentionIconName property found for {proxy_name}")

            # Se nada funcionou, usar ícone padrão
            printLog(f"Using fallback icon (application-x-executable) for {proxy_name}")
            icon_widget.set_from_icon_name("application-x-executable")

        except Exception as e:
            printLog(f"Error updating icon for {proxy_name}: {e}")
            icon_widget.set_from_icon_name(
                "application-x-executable"
            )  # Fallback em caso de erro inesperado

    def _update_item_tooltip(self, item_proxy, icon_widget: Gtk.Image):
        # (Implementation of _update_item_tooltip method as before)
        try:
            tooltip_variant = item_proxy.get_cached_property("ToolTip")
            if tooltip_variant and tooltip_variant.n_children() == 4:
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
                icon_widget.set_tooltip_text(None)
        except Exception as e:  # More generic
            if hasattr(item_proxy, "get_name"):
                proxy_name = item_proxy.get_name()
            else:
                proxy_name = "unknown proxy"
            printLog(f"Error updating tooltip for {proxy_name}: {e}")
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
        # (Implementation of _on_item_clicked method as before)
        # Added check for valid item_proxy, as it may be None if creation failed.
        if not item_proxy:
            printLog("Attempt to click item with invalid proxy.")
            return

        button = gesture.get_current_button()
        item_name_for_log = (
            item_proxy.get_name()
            if hasattr(item_proxy, "get_name")
            else "unknown proxy"
        )

        if button == Gdk.BUTTON_PRIMARY:
            try:
                printLog(f"Activating item (primary): {item_name_for_log}")
                item_proxy.call_sync(
                    "Activate",
                    GLib.Variant("(ii)", (int(x), int(y))),
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                )
            except GLib.Error as e:
                printLog(f"Error calling Activate on {item_name_for_log}: {e}")

        elif button == Gdk.BUTTON_SECONDARY:
            self._show_context_menu(item_proxy, widget, int(x), int(y))

    def _show_context_menu(
        self, item_proxy: Gio.DBusProxy, widget: Gtk.Widget, click_x: int, click_y: int
    ):
        # (Implementation of _show_context_menu method as before)
        if not item_proxy:
            printLog("Attempt to show context menu with invalid proxy.")
            return

        item_name_for_log = (
            item_proxy.get_name()
            if hasattr(item_proxy, "get_name")
            else "unknown proxy"
        )
        try:
            menu_path_variant = item_proxy.get_cached_property("Menu")
            if menu_path_variant:
                menu_object_path = menu_path_variant.get_string()
                if menu_object_path and menu_object_path != "/":
                    printLog(
                        f"Item {item_name_for_log} has a D-Bus menu at: {menu_object_path}"
                    )
                    # Here would enter the complex D-Bus menu logic
                # else:
                # printLog(f"Item {item_name_for_log} doesn't have a valid menu path: {menu_object_path}")

            printLog(f"Trying to call ContextMenu on {item_name_for_log}")
            item_proxy.call_sync(
                "ContextMenu",
                GLib.Variant("(ii)", (click_x, click_y)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )

        except GLib.Error as e:
            printLog(f"Error trying to show context menu for {item_name_for_log}: {e}")
