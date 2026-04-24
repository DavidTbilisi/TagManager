"""
Windows Explorer context-menu integration (per-user, HKCU).

Writes small launcher scripts under %%LOCALAPPDATA%%\\TagManager\\launcher so
Explorer does not rely on PATH, then registers shell verbs under:

  HKCU\\Software\\Classes\\*\\shell\\...
  HKCU\\Software\\Classes\\Directory\\shell\\...
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Stable vendor subfolder under LOCALAPPDATA
_LAUNCHER_ROOT = Path(os.environ.get("LOCALAPPDATA", "")) / "TagManager" / "launcher"

# Registry paths (under HKEY_CURRENT_USER). ``where`` lists ``"file"`` (*\\shell),
# ``"dir"`` (Directory\\shell), or both.
_VERBS: List[Tuple[str, str, str, str, Tuple[str, ...]]] = [
    # key_suffix, menu_text, script_stem, cli_tail_with_{path}, where
    (
        "TagManager.ShowTags",
        "Show tags (TagManager)",
        "tm_show_tags",
        'path "{path}"',
        ("file", "dir"),
    ),
    (
        "TagManager.AddRecursive",
        "Add tags here - recursive (TagManager)",
        "tm_add_recursive",
        'add "{path}" -r',
        ("dir",),
    ),
    (
        "TagManager.Storage",
        "Open TagManager storage folder",
        "tm_storage_open",
        "",
        ("file", "dir"),
    ),
]


def _launcher_dir() -> Path:
    return _LAUNCHER_ROOT


def _tm_cli_prefix() -> str:
    """Command prefix to invoke TagManager CLI (quoted)."""
    exe = shutil.which("tm")
    if exe:
        return f'"{exe}"'
    py = sys.executable
    return f'"{py}" -m tagmanager.cli'


def _write_batch(script_stem: str, cli_after_python: str) -> Path:
    """
    Write ``script_stem.cmd`` that runs ``tagmanager.cli`` with one placeholder {path}.

    ``cli_after_python`` is the tail after ``tagmanager.cli`` / ``tm``, e.g.
    ``path "{path}"`` — the literal ``{path}`` is replaced by ``%~1``.
    """
    d = _launcher_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{script_stem}.cmd"
    prefix = _tm_cli_prefix()
    # %~1 = first arg, strip surrounding quotes — safe for paths with spaces
    inner = cli_after_python.replace("{path}", "%~1")
    body = (
        "@echo off\r\n"
        "setlocal\r\n"
        f"{prefix} {inner}\r\n"
        "set ERR=%ERRORLEVEL%\r\n"
        "if not %ERR%==0 (\r\n"
        '  echo.\r\n'
        "  echo TagManager exited with code %ERR%\r\n"
        "  pause\r\n"
        ")\r\n"
        "endlocal\r\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def _write_storage_opener(script_stem: str) -> Path:
    """``tm storage --open`` ignores %%1; still use batch for consistent prefix."""
    d = _launcher_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{script_stem}.cmd"
    prefix = _tm_cli_prefix()
    body = (
        "@echo off\r\n"
        "setlocal\r\n"
        f"{prefix} storage --open\r\n"
        "set ERR=%ERRORLEVEL%\r\n"
        "if not %ERR%==0 pause\r\n"
        "endlocal\r\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def _reg_set(hkey, subkey: str, name: Optional[str], value: str) -> None:
    import winreg

    with winreg.CreateKeyEx(hkey, subkey) as k:
        if name is None:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, value)
        else:
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)


def _reg_delete_value_or_key(hkey, subkey: str) -> None:
    import winreg

    try:
        winreg.DeleteKey(hkey, subkey + r"\command")
    except OSError:
        pass
    try:
        winreg.DeleteKey(hkey, subkey)
    except OSError:
        pass


def _shell_root(kind: str) -> str:
    if kind == "file":
        return r"Software\Classes\*\shell"
    if kind == "dir":
        return r"Software\Classes\Directory\shell"
    raise ValueError(kind)


def format_install_plan() -> str:
    """
    Human-readable list of launcher paths and HKCU registry keys that
    :func:`install_context_menu` would create (no writes).
    """
    lines: List[str] = []
    launcher = _launcher_dir()
    lines.append(f"Launcher directory: {launcher}")
    lines.append("")
    for suffix, menu_text, stem, tail, where in _VERBS:
        bat = launcher / f"{stem}.cmd"
        if stem == "tm_storage_open":
            cmd_line = f'"{bat}" "%1"'
        else:
            cmd_line = f'"{bat}" "%1"'
        for kind in where:
            root = _shell_root(kind)
            sk = rf"{root}\{suffix}"
            hk = rf"HKEY_CURRENT_USER\{sk}"
            lines.append(f"Verb: {suffix}")
            lines.append(f"  Menu text: {menu_text}")
            lines.append(f"  Scope: {kind}")
            lines.append(f"  Registry: {hk}")
            lines.append(f"  Registry (command): {hk}\\command")
            lines.append(f"  command default REG_SZ: {cmd_line}")
            lines.append(f"  Launcher file: {bat}")
            lines.append("")
    return "\n".join(lines).rstrip()


def install_context_menu(dry_run: bool = False) -> Tuple[int, str]:
    """Install per-user context menu entries. Returns (exit_code, message)."""
    plan = format_install_plan()
    if sys.platform != "win32":
        if dry_run:
            return (
                0,
                plan + "\n\n(Dry-run: plan only. Run on Windows to install.)",
            )
        return 1, "Context menu integration is only supported on Windows."

    if dry_run:
        return (
            0,
            plan + "\n\nDry-run: no launcher files or registry keys were written.",
        )

    import winreg

    hkey = winreg.HKEY_CURRENT_USER
    messages: List[str] = []

    for suffix, menu_text, stem, tail, where in _VERBS:
        if stem == "tm_storage_open":
            bat = _write_storage_opener(stem)
            cmd_line = f'"{bat}" "%1"'
        else:
            bat = _write_batch(stem, tail)
            cmd_line = f'"{bat}" "%1"'

        for kind in where:
            root = _shell_root(kind)
            sk = rf"{root}\{suffix}"
            _reg_set(hkey, sk, None, menu_text)
            _reg_set(hkey, sk + r"\command", None, cmd_line)
        messages.append(f"Registered '{menu_text}' -> {bat}")

    return 0, "\n".join(messages)


def uninstall_context_menu() -> Tuple[int, str]:
    """Remove registry entries created by :func:`install_context_menu`."""
    if sys.platform != "win32":
        return 1, "Windows only."

    import winreg

    hkey = winreg.HKEY_CURRENT_USER
    for suffix, _, _, _, where in _VERBS:
        for kind in where:
            root = _shell_root(kind)
            sk = rf"{root}\{suffix}"
            _reg_delete_value_or_key(hkey, sk)

    return 0, "Removed TagManager entries from Explorer context menu (current user)."


def launcher_dir_for_docs() -> str:
    """Display path for help text."""
    return str(_launcher_dir())
