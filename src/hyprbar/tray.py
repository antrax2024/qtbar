import dbus  # pyright: ignore # noqa
import time
import os
from typing import Dict, List


class SNIMonitor:
    def __init__(self):
        self.session_bus = dbus.SessionBus()
        self.sni_watcher_service = "org.kde.StatusNotifierWatcher"
        self.sni_watcher_path = "/StatusNotifierWatcher"

    def get_sni_watcher(self):
        """Obtém o StatusNotifierWatcher"""
        try:
            return self.session_bus.get_object(
                self.sni_watcher_service, self.sni_watcher_path
            )
        except dbus.exceptions.DBusException:
            return None

    def get_registered_items(self) -> List[str]:
        """Obtém lista de itens SNI registrados"""
        try:
            watcher = self.get_sni_watcher()
            if not watcher:
                return []

            # Obtém a propriedade RegisteredStatusNotifierItems
            props = dbus.Interface(watcher, "org.freedesktop.DBus.Properties")
            items = props.Get(
                "org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems"
            )
            return list(items)
        except Exception as e:
            return []

    def get_item_details(self, item_service: str) -> Dict:
        """Obtém detalhes de um item SNI específico"""
        try:
            # Parse do service name (formato: org.freedesktop.StatusNotifierItem-PID-ID)
            parts = item_service.split("-")
            if len(parts) >= 3:
                pid = parts[-2]
                item_id = parts[-1]
            else:
                pid = "unknown"
                item_id = "unknown"

            # Conecta ao objeto SNI
            sni_object = self.session_bus.get_object(
                item_service, "/StatusNotifierItem"
            )
            props = dbus.Interface(sni_object, "org.freedesktop.DBus.Properties")

            # Obtém propriedades do SNI
            details = {
                "service": item_service,
                "pid": pid,
                "id": item_id,
                "category": "unknown",
                "status": "unknown",
                "title": "unknown",
                "icon_name": "unknown",
            }

            try:
                details["category"] = str(
                    props.Get("org.freedesktop.StatusNotifierItem", "Category")
                )
            except:
                pass

            try:
                details["status"] = str(
                    props.Get("org.freedesktop.StatusNotifierItem", "Status")
                )
            except:
                pass

            try:
                details["title"] = str(
                    props.Get("org.freedesktop.StatusNotifierItem", "Title")
                )
            except:
                pass

            try:
                details["id"] = str(
                    props.Get("org.freedesktop.StatusNotifierItem", "Id")
                )
            except:
                pass

            try:
                details["icon_name"] = str(
                    props.Get("org.freedesktop.StatusNotifierItem", "IconName")
                )
            except:
                pass

            return details

        except Exception as e:
            return {
                "service": item_service,
                "error": str(e),
                "pid": "unknown",
                "id": "unknown",
            }

    def check_sni_watcher_available(self) -> bool:
        """Verifica se o StatusNotifierWatcher está disponível"""
        try:
            names = self.session_bus.list_names()
            return self.sni_watcher_service in names
        except:
            return False

    def display_sni_status(self, items: List[str], details: List[Dict]) -> None:
        """Exibe o status dos itens SNI"""
        os.system("clear")

        print("🔗 MONITOR DE STATUS NOTIFIER ITEMS (SNI)")
        print("=" * 70)
        print(f"⏰ {time.strftime('%d/%m/%Y %H:%M:%S')}")

        # Verifica se o SNI Watcher está disponível
        watcher_available = self.check_sni_watcher_available()
        watcher_status = "🟢 ATIVO" if watcher_available else "🔴 INATIVO"
        print(f"📡 StatusNotifierWatcher: {watcher_status}")

        print(f"📊 Total de itens registrados: {len(items)}")
        print("-" * 70)

        if not watcher_available:
            print("❌ StatusNotifierWatcher não está disponível!")
            print("   Isso pode significar que:")
            print("   • Nenhuma barra de status com suporte SNI está rodando")
            print("   • O sistema não suporta StatusNotifierItem")
            print("   • Você está usando um ambiente que não implementa SNI")
        elif not items:
            print("📭 Nenhum item SNI registrado no momento")
            print("   Aplicações de tray podem estar usando:")
            print("   • System Tray (protocolo antigo)")
            print("   • Não estão rodando")
        else:
            for detail in details:
                if "error" in detail:
                    print(f"❌ {detail['service']}")
                    print(f"   └─ Erro: {detail['error']}")
                else:
                    status_icon = self._get_status_icon(detail.get("status", "unknown"))
                    category_icon = self._get_category_icon(
                        detail.get("category", "unknown")
                    )

                    print(
                        f"{status_icon} {detail['title']:<25} | PID: {detail['pid']:<8}"
                    )
                    print(
                        f"   └─ {category_icon} ID: {detail['id']:<15} | Status: {detail['status']}"
                    )
                    print(f"   └─ 🔧 Service: {detail['service']}")
                    if detail["icon_name"] != "unknown":
                        print(f"   └─ 🎨 Icon: {detail['icon_name']}")

        print("-" * 70)
        print("💡 Pressione Ctrl+C para parar")
        print("=" * 70)

    def _get_status_icon(self, status: str) -> str:
        """Retorna ícone baseado no status"""
        status_icons = {
            "Active": "🟢",
            "Passive": "🟡",
            "NeedsAttention": "🔴",
            "unknown": "❓",
        }
        return status_icons.get(status, "❓")

    def _get_category_icon(self, category: str) -> str:
        """Retorna ícone baseado na categoria"""
        category_icons = {
            "ApplicationStatus": "📱",
            "Communications": "💬",
            "SystemServices": "⚙️",
            "Hardware": "🔧",
            "unknown": "❓",
        }
        return category_icons.get(category, "❓")

    def run_monitor(self) -> None:
        """Loop principal de monitoramento"""
        print("🚀 Iniciando monitor de StatusNotifierItems (SNI)...")

        try:
            while True:
                # Obtém itens registrados
                items = self.get_registered_items()

                # Obtém detalhes de cada item
                details = []
                for item in items:
                    detail = self.get_item_details(item)
                    details.append(detail)

                # Exibe status
                self.display_sni_status(items, details)

                time.sleep(1)  # Atualiza a cada 1 segundo

        except KeyboardInterrupt:
            print("\n\n🛑 Monitor SNI finalizado!")


if __name__ == "__main__":
    monitor = SNIMonitor()
    monitor.run_monitor()

