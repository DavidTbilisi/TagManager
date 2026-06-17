"""CLI handlers for `tm sendto`."""

from .service import install, status, uninstall


def handle_install() -> int:
    result = install()
    print(result["message"])
    return 0 if result.get("success") else 1


def handle_uninstall() -> int:
    result = uninstall()
    print(result["message"])
    return 0 if result.get("success") else 1


def handle_status() -> int:
    s = status()
    if not s.get("platform_supported"):
        print("Send to integration is only available on Windows.")
        return 1
    shortcut = s.get("shortcut", "")
    if s.get("installed"):
        print(f"Send to entry: INSTALLED\n  {shortcut}")
    else:
        print(f"Send to entry: NOT installed\n  Would be created at: {shortcut}")
        print("\nRun 'tm sendto install' to add it.")
    return 0
