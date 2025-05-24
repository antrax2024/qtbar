import dbus  # pyright: ignore # noqa
import time


def check_sni_services():
    """Verifica serviços SNI disponíveis"""
    try:
        bus = dbus.SessionBus()
        names = bus.list_names()

        print("🔍 SERVIÇOS SNI DETECTADOS:")
        print("-" * 50)

        sni_services = [name for name in names if "StatusNotifierItem" in name]

        if sni_services:
            for service in sni_services:
                print(f"📡 {service}")
        else:
            print("❌ Nenhum serviço SNI encontrado")

        # Verifica StatusNotifierWatcher
        watcher_service = "org.kde.StatusNotifierWatcher"
        if watcher_service in names:
            print(f"\n✅ StatusNotifierWatcher ativo: {watcher_service}")

            # Tenta obter itens registrados
            try:
                watcher = bus.get_object(watcher_service, "/StatusNotifierWatcher")
                props = dbus.Interface(watcher, "org.freedesktop.DBus.Properties")
                items = props.Get(
                    "org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems"
                )

                print(f"📊 Itens registrados: {len(items)}")
                for item in items:
                    print(f"   └─ {item}")

            except Exception as e:
                print(f"❌ Erro ao obter itens: {e}")
        else:
            print("\n❌ StatusNotifierWatcher não encontrado")

    except Exception as e:
        print(f"❌ Erro ao conectar ao DBus: {e}")


def main():
    print("🔗 VERIFICADOR DE SNI - DEBUG")
    print("=" * 50)

    try:
        while True:
            check_sni_services()
            print("\n" + "=" * 50)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Finalizado!")


if __name__ == "__main__":
    main()

