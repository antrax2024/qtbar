import dbus  # pyright: ignore # noqa
import time


def check_sni_services():
    """Check available SNI services"""
    try:
        bus = dbus.SessionBus()
        names = bus.list_names()

        print("🔍 SNI SERVICES DETECTED:")
        print("-" * 50)

        # Check StatusNotifierWatcher
        watcher_service = "org.kde.StatusNotifierWatcher"
        if watcher_service in names:  # pyright: ignore # noqa
            print(f"\n✅ StatusNotifierWatcher active: {watcher_service}")

            # Try to get registered items
            try:
                watcher = bus.get_object(watcher_service, "/StatusNotifierWatcher")
                props = dbus.Interface(watcher, "org.freedesktop.DBus.Properties")
                items = props.Get(
                    "org.kde.StatusNotifierWatcher", "RegisteredStatusNotifierItems"
                )

                print(f"📊 Registered items: {len(items)}")
                for item in items:
                    print(f"   └─ {item}")

            except Exception as e:
                print(f"❌ Error getting items: {e}")
        else:
            print("\n❌ StatusNotifierWatcher not found")

    except Exception as e:
        print(f"❌ Error connecting to DBus: {e}")


def main():
    print("🔗 SNI CHECKER - DEBUG")
    print("=" * 50)

    try:
        while True:
            check_sni_services()
            print("\n" + "=" * 50)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Finished!")


if __name__ == "__main__":
    main()
