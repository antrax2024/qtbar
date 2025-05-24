#!/usr/bin/env python3

import time
import threading
from pydbus import SessionBus
from gi.repository import GLib  # pyright: ignore # noqa

# --- Configuração ---
CHECK_INTERVAL_SECONDS = 10  # Com que frequência verificar (em segundos)

# --- Nova Configuração ou Constante ---
EXCLUDE_SERVICE_PATTERNS = [
    "StatusNotifierWatcher",  # Pega org.kde.StatusNotifierWatcher, org.ayatana.StatusNotifierWatcher, etc.
    "StatusNotifierHost",  # Pega org.kde.StatusNotifierHost-*, etc.
    "org.gnome.Shell",  # Frequentemente o próprio shell, não um app de bandeja
    "org.freedesktop.DBus",  # O próprio daemon D-Bus
    "org.freedesktop.portal",  # Portais de desktop
    # Protetores de tela ou bloqueios de tela que podem ter um nome no bus mas não são ícones de bandeja
    "org.gnome.ScreenSaver",
    "org.freedesktop.ScreenSaver",
    "org.mate.ScreenSaver",
    "org.cinnamon.ScreenSaver",
    # Serviços de método de entrada
    "ibus",
    "fcitx",
]
# --- Fim da Nova Configuração ---

# Palavras-chave para detecção de fallback. Seus exemplos estão incluídos.
# nm-applet, blueberry-tray, jamesdsp, copyQ
FALLBACK_TRAY_APP_KEYWORDS = [
    "nm-applet",
    "blueberry-tray",
    "jamesdsp",
    "copyq",  # Seus exemplos
    "kdeconnect",
    "flameshot",
    "steam",
    "discord",
    "telegram",
    "nextcloud",
    "dropbox",
    "redshift",
    "volumeicon",
    "pamac",
    "blueman",
    "applet",
    "tray",
    "indicator",
    "statusnotifier",  # Termos genéricos
]
# --- Fim da Configuração ---

# Globais para armazenar instâncias do bus e manager para evitar recriação constante
_session_bus_instance = None
_dbus_manager_proxy_instance = None


def get_dbus_essentials():
    """Obtém e armazena em cache as instâncias do SessionBus e do proxy do gerenciador D-Bus."""
    global _session_bus_instance, _dbus_manager_proxy_instance
    if _session_bus_instance is None:
        try:
            _session_bus_instance = SessionBus()
        except GLib.Error as e:
            print(
                f"ERRO CRÍTICO: Não foi possível conectar ao SessionBus do D-Bus: {e}"
            )
            return None, None  # Não pode continuar sem o bus

    if _dbus_manager_proxy_instance is None and _session_bus_instance:
        try:
            _dbus_manager_proxy_instance = _session_bus_instance.get(
                "org.freedesktop.DBus", "/org/freedesktop/DBus"
            )
        except GLib.Error as e:
            print(
                f"ERRO CRÍTICO: Não foi possível obter o proxy do gerenciador D-Bus: {e}"
            )
            # Permite que o bus exista, mas o manager pode falhar ao ser obtido
    return _session_bus_instance, _dbus_manager_proxy_instance


def resolve_service_to_info_string(service_name_or_path):
    """
    Resolve um nome de serviço D-Bus (que pode ser único, ex: :1.123, ou incluir um caminho)
    para uma string mais identificável, incluindo PID e nome do comando, se possível.
    """
    bus, dbus_manager = get_dbus_essentials()
    if not dbus_manager:  # Se o dbus_manager não pôde ser inicializado
        return service_name_or_path  # Retorna o original como fallback

    # Extrai apenas a parte do nome do barramento, ignorando o caminho do objeto, se houver
    service_name = service_name_or_path.split("/")[0]

    if service_name.startswith(":"):  # Nome de conexão único
        try:
            pid = dbus_manager.GetConnectionUnixProcessID(service_name)
            app_name_str = service_name  # Padrão caso o comando não seja encontrado
            try:
                # /proc/[pid]/comm geralmente fornece o nome do executável de forma limpa
                with open(f"/proc/{pid}/comm", "r") as f:
                    cmd = f.read().strip()
                app_name_str = f"{service_name} (App: {cmd}, PID: {pid})"
            except FileNotFoundError:
                app_name_str = (
                    f"{service_name} (PID: {pid}, nome do app não encontrado via /comm)"
                )
            except Exception:  # Outros erros ao ler /comm
                app_name_str = f"{service_name} (PID: {pid}, erro ao ler nome do app)"
            return app_name_str
        except (
            GLib.Error
        ):  # Falha ao obter PID (serviço pode ter desconectado ou sem permissão)
            return f"{service_name} (PID não disponível)"
        except Exception:  # Outro erro inesperado
            return f"{service_name} (Erro ao resolver PID)"
    else:  # Nome bem conhecido
        return service_name


def find_tray_applications():
    bus, dbus_manager = get_dbus_essentials()
    if not bus or not dbus_manager:
        return []

    found_apps_info = set()
    # Armazena (nome_do_comando, pid) de nomes únicos resolvidos para ajudar na de-duplicação
    resolved_app_identifiers = set()
    # Armazena nomes base de serviços encontrados pelo watcher para evitar reprocessamento por palavra-chave
    services_processed_by_watcher = set()

    try:
        all_dbus_services = dbus_manager.ListNames()
    except GLib.Error as e:
        print(f"AVISO: Não foi possível listar todos os serviços D-Bus: {e}")
        all_dbus_services = []
    except AttributeError:  # Se dbus_manager for None
        all_dbus_services = []

    # Função para verificar se um serviço deve ser excluído
    def should_exclude(
        service_name_or_info_str, original_service_name_for_pattern_match=""
    ):
        s_lower = service_name_or_info_str.lower()
        orig_s_lower = original_service_name_for_pattern_match.lower()
        for pattern in EXCLUDE_SERVICE_PATTERNS:
            p_lower = pattern.lower()
            if p_lower in s_lower or (orig_s_lower and p_lower in orig_s_lower):
                return True
        return False

    # 1. Consultar serviços StatusNotifierWatcher
    watcher_configurations = [
        ("org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher"),
        ("org.ayatana.StatusNotifierWatcher", "/StatusNotifierWatcher"),
        (
            "com.canonical.indicator.application.Watcher",
            "/com/canonical/indicator/application/watcher",
        ),
    ]

    for watcher_name, watcher_obj_path in watcher_configurations:
        if watcher_name in all_dbus_services:
            try:
                watcher_proxy = bus.get(watcher_name, watcher_obj_path)
                registered_items = watcher_proxy.RegisteredStatusNotifierItems

                if isinstance(registered_items, list):
                    for item_specifier_str in registered_items:
                        if not (
                            isinstance(item_specifier_str, str) and item_specifier_str
                        ):
                            continue

                        original_bus_name = item_specifier_str.split("/")[0]
                        services_processed_by_watcher.add(original_bus_name)

                        info_str = resolve_service_to_info_string(item_specifier_str)

                        if not should_exclude(info_str, original_bus_name):
                            found_apps_info.add(info_str)
                            # Se for um nome único como ":1.23 (App: cmd, PID: 456)"
                            # armazena ("cmd", 456) para de-duplicação
                            if (
                                original_bus_name.startswith(":")
                                and "(App: " in info_str
                                and ", PID: " in info_str
                            ):
                                try:
                                    parts = info_str.split("(App: ", 1)[1].split(
                                        ", PID: ", 1
                                    )
                                    app_part = parts[0]
                                    pid_part_str = parts[1].split(")", 1)[0]
                                    pid_part = int(pid_part_str)
                                    resolved_app_identifiers.add((app_part, pid_part))
                                except (IndexError, ValueError, TypeError):
                                    # print(f"Debug: Falha ao parsear app/pid de: {info_str}")
                                    pass
            except (GLib.Error, AttributeError, Exception):
                # Ignora erros com watchers individuais (podem não estar ativos ou acessíveis)
                pass

    # 2. Fallback/Complemento: Verificar todos os serviços D-Bus com palavras-chave conhecidas
    for service_name in all_dbus_services:
        base_service_name = service_name.split("/")[0]

        # Pular nomes únicos (tratados pelo watcher) ou já processados pelo watcher
        if (
            base_service_name.startswith(":")
            or base_service_name in services_processed_by_watcher
        ):
            continue

        # Filtro para nomes de serviço que parecem ser de aplicativos
        if not (
            base_service_name.startswith("org.")
            or base_service_name.startswith("com.")
            or base_service_name.startswith("io.")
            or base_service_name.startswith("net.")
        ):
            continue

        # Verificar exclusão para o nome base do serviço
        if should_exclude(base_service_name):
            continue

        for keyword in FALLBACK_TRAY_APP_KEYWORDS:
            if keyword.lower() in base_service_name.lower():
                # Candidato encontrado por palavra-chave. Tentar evitar duplicatas.
                is_likely_duplicate = False
                # Verifica se o nome do app implícito pela palavra-chave já foi resolvido
                for res_app_name, _ in resolved_app_identifiers:
                    # Se a palavra-chave é parte do nome de um app já resolvido E
                    # a palavra-chave também está no nome do serviço D-Bus atual.
                    # Ex: keyword 'nm-applet', res_app_name 'nm-applet', base_service_name 'org.freedesktop.network-manager-applet'
                    if (
                        keyword.lower() in res_app_name.lower()
                        and keyword.lower() in base_service_name.lower()
                    ):
                        is_likely_duplicate = True
                        break

                if not is_likely_duplicate:
                    info_str = resolve_service_to_info_string(base_service_name)
                    if not should_exclude(
                        info_str, base_service_name
                    ):  # Dupla verificação de exclusão
                        found_apps_info.add(info_str)
                break  # Encontrado por palavra-chave, passar para o próximo service_name

    return sorted(list(found_apps_info))


def tray_monitor_thread_function():
    """
    Função trabalhadora para a thread. Verifica periodicamente e imprime os aplicativos da bandeja.
    """
    print("Iniciando monitoramento de aplicativos na bandeja do sistema (via D-Bus)...")
    print(
        f"Verificando a cada {CHECK_INTERVAL_SECONDS} segundos. Pressione Ctrl+C para sair."
    )
    print("-" * 70)

    last_displayed_apps_set = set()

    try:
        while True:
            # Garante que a conexão D-Bus seja estabelecida/reestabelecida para esta iteração, se necessário
            get_dbus_essentials()  # A função lida com o cache interno

            current_apps_list = find_tray_applications()
            current_apps_set = set(current_apps_list)

            if current_apps_set != last_displayed_apps_set:
                timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n--- Aplicativos na Bandeja ({timestamp_str}) ---")
                if current_apps_list:
                    for app_info_item in current_apps_list:
                        print(f"  -> {app_info_item}")
                else:
                    print("  (Nenhum aplicativo de bandeja detectado)")
                print("-" * 70)
                last_displayed_apps_set = current_apps_set

            time.sleep(CHECK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        # Normalmente, o KeyboardInterrupt é capturado pela thread principal.
        # Se capturado aqui, significa que o sleep foi interrompido.
        print("\nThread de monitoramento interrompida.")
    except Exception as e:
        import traceback

        print(f"\nERRO na thread de monitoramento: {e}")
        print(traceback.format_exc())


if __name__ == "__main__":
    # Tenta inicializar os essenciais do D-Bus uma vez antes de iniciar a thread.
    # Isso ajuda a identificar problemas de conexão D-Bus mais cedo.
    bus, manager = get_dbus_essentials()
    if not bus:  # Se a conexão com o SessionBus falhou, não podemos continuar.
        print("Falha crítica ao inicializar o D-Bus. O script não pode continuar.")
        exit(1)
    if not manager:
        print(
            "AVISO: O proxy do gerenciador D-Bus não pôde ser inicializado. Algumas funcionalidades podem ser limitadas."
        )
        # O script pode continuar, mas a resolução de nomes e listagem completa podem falhar.

    monitor_thread = threading.Thread(target=tray_monitor_thread_function, daemon=True)
    monitor_thread.start()

    try:
        # Mantém a thread principal viva até Ctrl+C
        while monitor_thread.is_alive():
            # join com timeout permite que o loop verifique KeyboardInterrupt periodicamente
            monitor_thread.join(timeout=0.5)
    except KeyboardInterrupt:
        print(
            "\nSaindo... Aguardando a thread de monitoramento finalizar (se necessário)."
        )
    except Exception as e:
        print(f"Erro inesperado no script principal: {e}")
    finally:
        print("Script finalizado.")
