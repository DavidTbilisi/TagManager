"""CLI handlers for `tm hotkey`."""

from .service import (
    DEFAULT_KEY,
    DEFAULT_MOD,
    autostart_status,
    install_autostart,
    run_daemon,
    uninstall_autostart,
)


def handle_run(modifiers: str = DEFAULT_MOD, key: str = DEFAULT_KEY) -> int:
    return run_daemon(modifiers, key)


def handle_install(modifiers: str = DEFAULT_MOD, key: str = DEFAULT_KEY) -> int:
    result = install_autostart(modifiers, key)
    print(result["message"])
    return 0 if result.get("success") else 1


def handle_uninstall() -> int:
    result = uninstall_autostart()
    print(result["message"])
    return 0 if result.get("success") else 1


def handle_status() -> int:
    s = autostart_status()
    if not s.get("platform_supported"):
        print("Hotkey integration is only available on Windows.")
        return 1
    if s.get("installed"):
        print(f"Hotkey autostart: INSTALLED\n  {s.get('shortcut', '')}")
    else:
        print(f"Hotkey autostart: NOT installed\n  Would be created at: {s.get('shortcut', '')}")
        print("\nRun 'tm hotkey install' to enable autostart, or 'tm hotkey run' for a one-off session.")
    return 0
