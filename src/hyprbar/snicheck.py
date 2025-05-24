import dbus  # pyright: ignore # noqa
import time
from typing import Dict, Any, List, Tuple


def get_sni_item_properties(
    bus: dbus.Bus, service_name: str, object_path: str
) -> Dict[str, Any]:
    """Get all properties from a StatusNotifierItem"""
    try:
        item = bus.get_object(service_name, object_path)
        props_interface = dbus.Interface(item, "org.freedesktop.DBus.Properties")

        # Try both org.kde and org.freedesktop interfaces
        interfaces_to_try = [
            "org.kde.StatusNotifierItem",
            "org.freedesktop.StatusNotifierItem",
        ]

        for interface in interfaces_to_try:
            try:
                properties = props_interface.GetAll(interface)
                return dict(properties)
            except dbus.exceptions.DBusException:
                continue

        return {}
    except Exception as e:
        print(f"❌ Erro ao obter propriedades de {service_name}{object_path}: {e}")
        return {}


def get_context_menu_info(
    bus: dbus.Bus, service_name: str, object_path: str, properties: Dict[str, Any]
) -> Dict[str, Any]:
    """Get context menu information from StatusNotifierItem"""
    menu_info = {
        "has_menu": False,
        "menu_path": None,
        "menu_service": None,
        "menu_items": [],
    }

    try:
        # Check if item has a menu
        menu_path = properties.get("Menu", "")
        if menu_path:
            menu_info["has_menu"] = True
            menu_info["menu_path"] = menu_path
            menu_info["menu_service"] = service_name

            # Try to get menu items
            try:
                menu_items = get_dbus_menu_items(bus, service_name, menu_path)
                menu_info["menu_items"] = menu_items
            except Exception as e:
                print(f"⚠️ Erro ao obter itens do menu: {e}")

        # Check ItemIsMenu property
        item_is_menu = properties.get("ItemIsMenu", False)
        if item_is_menu:
            menu_info["item_is_menu"] = True

    except Exception as e:
        print(f"❌ Erro ao verificar menu de {service_name}: {e}")

    return menu_info


def get_dbus_menu_items(
    bus: dbus.Bus, service_name: str, menu_path: str
) -> List[Dict[str, Any]]:
    """Get menu items from DBusMenu interface"""
    try:
        menu_obj = bus.get_object(service_name, menu_path)
        menu_interface = dbus.Interface(menu_obj, "com.canonical.dbusmenu")

        # Get layout starting from root (0)
        revision, layout = menu_interface.GetLayout(0, -1, [])

        menu_items = []
        if layout and len(layout) > 2:
            # layout format: (id, properties, children)
            children = layout[2] if len(layout) > 2 else []
            menu_items = parse_menu_layout(children)

        return menu_items

    except Exception as e:
        print(f"❌ Erro ao acessar DBusMenu: {e}")
        return []


def parse_menu_layout(children: List) -> List[Dict[str, Any]]:
    """Parse menu layout recursively"""
    items = []

    for child in children:
        if len(child) >= 3:
            item_id = child[0]
            properties = dict(child[1]) if child[1] else {}
            sub_children = child[2] if len(child) > 2 else []

            item = {
                "id": item_id,
                "label": properties.get("label", ""),
                "enabled": properties.get("enabled", True),
                "visible": properties.get("visible", True),
                "type": properties.get("type", "standard"),
                "icon_name": properties.get("icon-name", ""),
                "shortcut": properties.get("shortcut", ""),
                "toggle_type": properties.get("toggle-type", ""),
                "toggle_state": properties.get("toggle-state", 0),
                "children": [],
            }

            # Parse submenu items recursively
            if sub_children:
                item["children"] = parse_menu_layout(sub_children)

            items.append(item)

    return items


def display_menu_items(menu_items: List[Dict[str, Any]], indent: int = 0):
    """Display menu items in a tree format"""
    prefix = "  " * indent

    for item in menu_items:
        if not item.get("visible", True):
            continue

        label = item.get("label", "").replace("_", "")  # Remove mnemonics
        item_type = item.get("type", "standard")
        enabled = item.get("enabled", True)
        icon = item.get("icon_name", "")

        # Format item display
        status_icon = "✅" if enabled else "❌"
        type_icon = {
            "separator": "➖",
            "standard": "📄",
            "radio": "🔘",
            "checkmark": "☑️",
        }.get(item_type, "📄")

        if item_type == "separator":
            print(f"{prefix}➖ ────────────")
        else:
            icon_display = f"🎨{icon} " if icon else ""
            print(f"{prefix}{status_icon} {type_icon} {icon_display}{label}")

            # Show toggle state for checkboxes/radio buttons
            if item.get("toggle_type"):
                state = "✓" if item.get("toggle_state") else "✗"
                print(f"{prefix}   └─ Estado: {state}")

        # Display children (submenu)
        if item.get("children"):
            print(f"{prefix}   └─ 📁 Submenu:")
            display_menu_items(item["children"], indent + 2)


def test_menu_interaction(
    bus: dbus.Bus, service_name: str, menu_path: str, item_id: int
):
    """Test menu item interaction (for demonstration)"""
    try:
        menu_obj = bus.get_object(service_name, menu_path)
        menu_interface = dbus.Interface(menu_obj, "com.canonical.dbusmenu")

        # Simulate click on menu item
        print(f"🖱️ Simulando clique no item {item_id}...")
        menu_interface.Event(
            item_id,
            "clicked",
            dbus.Array([], signature="v"),
            dbus.UInt32(int(time.time())),
        )

    except Exception as e:
        print(f"❌ Erro ao interagir com menu: {e}")


def display_item_info(
    service_name: str, object_path: str, properties: Dict[str, Any], bus: dbus.Bus
):
    """Display formatted information about an SNI item including context menu"""
    print(f"\n📋 ITEM: {service_name}{object_path}")
    print("-" * 80)

    # Basic info
    item_id = properties.get("Id", "N/A")
    title = properties.get("Title", "N/A")
    category = properties.get("Category", "N/A")
    status = properties.get("Status", "N/A")

    print(f"🆔 ID: {item_id}")
    print(f"📝 Título: {title}")
    print(f"📂 Categoria: {format_category(category)}")
    print(f"🔄 Status: {format_status(status)}")

    # Icon information
    icon_name = properties.get("IconName", "")
    attention_icon_name = properties.get("AttentionIconName", "")
    overlay_icon_name = properties.get("OverlayIconName", "")

    if icon_name:
        print(f"🎨 Ícone Principal: {icon_name}")
    if attention_icon_name:
        print(f"⚠️ Ícone de Atenção: {attention_icon_name}")
    if overlay_icon_name:
        print(f"🔗 Ícone Overlay: {overlay_icon_name}")

    # Tooltip information
    tooltip_title = properties.get("ToolTipTitle", "")
    tooltip_subtitle = properties.get("ToolTipSubTitle", "")
    tooltip_icon = properties.get("ToolTipIconName", "")

    if tooltip_title or tooltip_subtitle:
        print(f"💭 Tooltip:")
        if tooltip_title:
            print(f"   └─ Título: {tooltip_title}")
        if tooltip_subtitle:
            print(f"   └─ Subtítulo: {tooltip_subtitle}")
        if tooltip_icon:
            print(f"   └─ Ícone: {tooltip_icon}")

    # Context Menu Information
    print(f"\n🍽️ CONTEXT MENU:")
    menu_info = get_context_menu_info(bus, service_name, object_path, properties)

    if menu_info["has_menu"]:
        print(f"✅ Menu disponível em: {menu_info['menu_path']}")
        print(f"🔗 Serviço: {menu_info['menu_service']}")

        if menu_info["menu_items"]:
            print(f"📋 Itens do menu ({len(menu_info['menu_items'])}):")
            display_menu_items(menu_info["menu_items"])
        else:
            print("⚠️ Não foi possível obter itens do menu")
    else:
        print("❌ Nenhum menu disponível")

    # Item is menu check
    item_is_menu = properties.get("ItemIsMenu", False)
    if item_is_menu:
        print("📋 ItemIsMenu: True (o próprio item funciona como menu)")

    # Additional properties
    window_id = properties.get("WindowId", 0)
    if window_id:
        print(f"🪟 Window ID: {window_id}")


def format_category(category: str) -> str:
    """Format category for display"""
    category_map = {
        "ApplicationStatus": "📱 Aplicação",
        "Communications": "💬 Comunicação",
        "SystemServices": "⚙️ Sistema",
        "Hardware": "🔧 Hardware",
    }
    return category_map.get(category, f"❓ {category}")


def format_status(status: str) -> str:
    """Format status for display"""
    status_map = {
        "Passive": "😴 Inativo",
        "Active": "✅ Ativo",
        "NeedsAttention": "⚠️ Atenção",
    }
    return status_map.get(status, f"❓ {status}")


def check_sni_services():
    """Check available SNI services and get detailed information"""
    try:
        bus = dbus.SessionBus()
        names = bus.list_names()

        print("🔍 SNI SERVICES DETECTED:")
        print("=" * 80)

        # Check StatusNotifierWatcher
        watcher_service = "org.kde.StatusNotifierWatcher"
        if watcher_service in names:  # pyright: ignore # noqa
            print(f"\n✅ StatusNotifierWatcher ativo: {watcher_service}")

            # Try to get registered items
            try:
                watcher = bus.get_object(watcher_service, "/StatusNotifierWatcher")
                props = dbus.Interface(watcher, "org.freedesktop.DBus.Properties")
                items = props.Get(
                    "org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems"
                )

                print(f"📊 Total de itens registrados: {len(items)}")

                for item in items:
                    # Parse service name and object path
                    if "/" in item:
                        service_name = item.split("/")[0]
                        object_path = "/" + "/".join(item.split("/")[1:])
                    else:
                        service_name = item
                        object_path = "/StatusNotifierItem"

                    # Get detailed properties
                    properties = get_sni_item_properties(bus, service_name, object_path)
                    if properties:
                        display_item_info(service_name, object_path, properties, bus)
                    else:
                        print(f"\n❌ Não foi possível obter propriedades de: {item}")

            except Exception as e:
                print(f"❌ Erro ao obter itens: {e}")
        else:
            print("\n❌ StatusNotifierWatcher não encontrado")
            print(
                "💡 Dica: Verifique se você está usando KDE/Plasma ou uma extensão compatível"
            )

    except Exception as e:
        print(f"❌ Erro ao conectar no DBus: {e}")


def main():
    print("🔗 SNI CHECKER - VERSÃO COMPLETA COM CONTEXT MENU")
    print("=" * 80)
    print("💡 Pressione Ctrl+C para sair")

    try:
        while True:
            check_sni_services()
            print("\n" + "=" * 80)
            print("🔄 Atualizando em 5 segundos...")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Aplicação finalizada!")


if __name__ == "__main__":
    main()
