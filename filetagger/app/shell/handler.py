"""CLI handlers for the `ftag shell` subcommand."""

import sys

from .service import (
    context_menu_status,
    install_context_menu,
    tag_path_interactively,
    uninstall_context_menu,
)


def handle_install() -> int:
    result = install_context_menu()
    print(result["message"])
    if result.get("success"):
        print(
            "\nThe verb is registered via IExplorerCommand. Restart File Explorer\n"
            "(or sign out / in) if it does not appear immediately:\n"
            "  taskkill /f /im explorer.exe; start explorer"
        )
    return 0 if result.get("success") else 1


def handle_uninstall() -> int:
    result = uninstall_context_menu()
    print(result["message"])
    return 0 if result.get("success") else 1


def handle_status() -> int:
    status = context_menu_status()
    if not status.get("platform_supported"):
        print(f"Shell integration is only available on Windows (current: {sys.platform}).")
        return 1

    installed = status.get("installed") or []
    missing = status.get("missing") or []
    clsid_registered = status.get("clsid_registered")
    dll = status.get("dll")

    if clsid_registered and installed and not missing:
        print("Context menu: INSTALLED (CLSID + all verb locations)")
    elif clsid_registered or installed:
        print("Context menu: PARTIALLY installed")
    else:
        print("Context menu: NOT installed")

    print(f"  CLSID:   {'[x]' if clsid_registered else '[ ]'} InProcServer32"
          + (f" -> {dll}" if dll else ""))
    for path in installed:
        print(f"  Verb:    [x] HKCU\\{path}")
    for path in missing:
        print(f"  Verb:    [ ] HKCU\\{path}")
    if not (clsid_registered and installed):
        print("\nRun 'ftag shell install' to register the COM handler.")
    return 0


def handle_tag(path: str) -> int:
    result = tag_path_interactively(path)
    msg = result.get("message") or ""
    if msg:
        print(msg)
    return 0 if result.get("success") else 1
