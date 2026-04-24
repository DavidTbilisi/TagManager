"""
Windows Explorer context-menu integration (per-user, HKCU).

Registers a single **TagManager** cascade under:

  HKCU\\Software\\Classes\\*\\shell\\TagManager\\
  HKCU\\Software\\Classes\\Directory\\shell\\TagManager\\

Each parent key uses Microsoft's documented **ExtendedSubCommandsKey** layout
so the parent is treated as a *popup*, not a verb (the same trick fixes the
"This file does not have an app associated…" error users see when Explorer
tries to invoke a parent that lacks a ``\\command`` subkey)::

    TagManager
        (Default) = ""
        MUIVerb   = "TagManager"
        ExtendedSubCommandsKey
            Shell
                <LeafId>
                    (Default) = "<menu text>"
                    command
                        (Default) = "<launcher.cmd> %*"

This layout is the only HKCU-friendly cascade pattern that survives both the
classic Explorer menu and Windows 11's modern context menu.

Launchers live under %%LOCALAPPDATA%%\\TagManager\\launcher. Explorer passes
selected paths as separate arguments (``%1``, ``%2``, …); batch scripts loop
``shift`` so multiple files can be tagged at once.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

# Stable vendor subfolder under LOCALAPPDATA
_LAUNCHER_ROOT = Path(os.environ.get("LOCALAPPDATA", "")) / "TagManager" / "launcher"

# Single parent folder name under *\shell and Directory\shell
_PARENT_KEY = "TagManager"
_PARENT_LABEL = "TagManager"

WriterKind = Literal["batch", "terminal", "storage", "add_multi", "remove_multi", "show_multi"]


@dataclass(frozen=True)
class _Leaf:
    """One Explorer item under the TagManager cascade."""

    id: str
    menu_text: str
    writer: WriterKind
    scopes: Tuple[str, ...]  # "file" (*), "dir" (Directory)


_LEAVES: Tuple[_Leaf, ...] = (
    _Leaf("ShowTags", "Show tags", "show_multi", ("file", "dir")),
    _Leaf("AddTags", "Add tags…", "add_multi", ("file", "dir")),
    _Leaf("RemoveTags", "Remove tags…", "remove_multi", ("file", "dir")),
    _Leaf("AddHereOneLevel", "Add tags — this folder only (1 level)", "add_multi", ("dir",)),
    _Leaf("AddHereRecursive", "Add tags — all subfolders", "add_multi", ("dir",)),
    _Leaf("AddHereRecursiveDryRun", "Add tags — all subfolders (dry-run)", "add_multi", ("dir",)),
    _Leaf("OpenTerminalHere", "Open Command Prompt here", "terminal", ("dir",)),
    _Leaf("Storage", "Open TagManager storage folder", "storage", ("file", "dir")),
)


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
    """Single-path batch (``%~1`` replaces ``{path}``)."""
    d = _launcher_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{script_stem}.cmd"
    prefix = _tm_cli_prefix()
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


def _write_open_terminal_here(script_stem: str) -> Path:
    d = _launcher_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{script_stem}.cmd"
    body = (
        "@echo off\r\n"
        "setlocal\r\n"
        'cd /d "%~1"\r\n'
        'start "" cmd /k\r\n'
        "endlocal\r\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def _write_storage_opener(script_stem: str) -> Path:
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


def _write_show_multi(script_stem: str) -> Path:
    """Loop all selected paths with ``tm path``."""
    d = _launcher_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{script_stem}.cmd"
    prefix = _tm_cli_prefix()
    body = (
        "@echo off\r\n"
        "setlocal EnableExtensions\r\n"
        ":loop\r\n"
        'if "%~1"=="" goto :after\r\n'
        f"{prefix} path \"%1\"\r\n"
        "shift\r\n"
        "goto :loop\r\n"
        ":after\r\n"
        "pause\r\n"
        "endlocal\r\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def _write_add_tags_interactive(script_stem: str) -> Path:
    """Multi-select: prompt tags once, then each path — folders get 1 vs full recursive choice."""
    d = _launcher_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{script_stem}.cmd"
    prefix = _tm_cli_prefix()
    body = (
        "@echo off\r\n"
        "setlocal EnableExtensions EnableDelayedExpansion\r\n"
        'set /p TM_TAGS=Enter tags (comma-separated): \r\n'
        'if "!TM_TAGS!"=="" (\r\n'
        "  echo Cancelled.\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "set ERR=0\r\n"
        ":loop\r\n"
        'if "%~1"=="" goto :after\r\n'
        'set "TARGET=%~1"\r\n'
        'if exist "!TARGET!\\" (\r\n'
        "  echo.\r\n"
        '  echo Folder: !TARGET!\r\n'
        "  echo [1] This folder only - one level ^(recommended^)\r\n"
        "  echo [2] All subfolders recursively\r\n"
        "  choice /c 12 /n /m \"Choose 1 or 2: \"\r\n"
        "  if errorlevel 2 (\r\n"
        f"    {prefix} add \"!TARGET!\" -r --tags \"!TM_TAGS!\"\r\n"
        "  ) else (\r\n"
        f"    {prefix} add \"!TARGET!\" -r --max-depth 1 --tags \"!TM_TAGS!\"\r\n"
        "  )\r\n"
        ") else (\r\n"
        f"  {prefix} add \"!TARGET!\" --tags \"!TM_TAGS!\"\r\n"
        ")\r\n"
        "if not !ERRORLEVEL!==0 set ERR=!ERRORLEVEL!\r\n"
        "shift\r\n"
        "goto :loop\r\n"
        ":after\r\n"
        "if not !ERR!==0 (\r\n"
        "  echo.\r\n"
        "  echo TagManager exited with code !ERR!\r\n"
        "  pause\r\n"
        ")\r\n"
        "pause\r\n"
        "endlocal\r\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def _write_remove_multi(script_stem: str) -> Path:
    d = _launcher_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{script_stem}.cmd"
    prefix = _tm_cli_prefix()
    body = (
        "@echo off\r\n"
        "setlocal EnableExtensions EnableDelayedExpansion\r\n"
        'set /p TM_TAG=Tag to remove ^(use * to clear ALL tags on each file, keeping the path^): \r\n'
        'if "!TM_TAG!"=="" (\r\n'
        "  echo Cancelled.\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        ":loop\r\n"
        'if "%~1"=="" goto :after\r\n'
        'if "!TM_TAG!"=="*" (\r\n'
        f"  {prefix} remove --path \"%~1\" --all-tags\r\n"
        ") else (\r\n"
        f"  {prefix} remove --path \"%~1\" --tag \"!TM_TAG!\"\r\n"
        ")\r\n"
        "set ERR=%ERRORLEVEL%\r\n"
        "shift\r\n"
        "goto :loop\r\n"
        ":after\r\n"
        "if not %ERR%==0 pause\r\n"
        "pause\r\n"
        "endlocal\r\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def _write_add_dir_fixed(script_stem: str, mode: str) -> Path:
    """Directory-only verbs: no prompt for depth (fixed behaviour)."""
    d = _launcher_dir()
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{script_stem}.cmd"
    prefix = _tm_cli_prefix()
    if mode == "onelevel":
        tail = 'add "%~1" -r --max-depth 1'
    elif mode == "full":
        tail = 'add "%~1" -r'
    elif mode == "fulldry":
        tail = 'add "%~1" -r --dry-run'
    else:
        raise ValueError(mode)
    body = (
        "@echo off\r\n"
        "setlocal EnableExtensions EnableDelayedExpansion\r\n"
        'set /p TM_TAGS=Enter tags (comma-separated): \r\n'
        'if "!TM_TAGS!"=="" (\r\n'
        "  echo Cancelled.\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "set ERR=0\r\n"
        ":loop\r\n"
        'if "%~1"=="" goto :after\r\n'
        f"{prefix} {tail} --tags \"!TM_TAGS!\"\r\n"
        "if not !ERRORLEVEL!==0 set ERR=!ERRORLEVEL!\r\n"
        "shift\r\n"
        "goto :loop\r\n"
        ":after\r\n"
        "if not !ERR!==0 pause\r\n"
        "pause\r\n"
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


def _shell_root(kind: str) -> str:
    if kind == "file":
        return rf"Software\Classes\*\shell\{_PARENT_KEY}"
    if kind == "dir":
        return rf"Software\Classes\Directory\shell\{_PARENT_KEY}"
    raise ValueError(kind)


def _leaf_shell_path(kind: str, leaf_id: str) -> str:
    return rf"{_shell_root(kind)}\ExtendedSubCommandsKey\Shell\{leaf_id}"


def _reg_delete_subtree(hkey, subkey: str) -> None:
    """Delete a registry key and all subkeys (deepest first)."""
    import winreg

    try:
        with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ | winreg.KEY_WRITE) as k:
            while True:
                try:
                    child = winreg.EnumKey(k, 0)
                except OSError:
                    break
                _reg_delete_subtree(hkey, rf"{subkey}\{child}")
    except OSError:
        return
    try:
        winreg.DeleteKey(hkey, subkey)
    except OSError:
        pass


def _leaf_to_stem(leaf: _Leaf) -> str:
    return f"tm_ctx_{leaf.id}"


def _write_leaf_launcher(leaf: _Leaf) -> Path:
    stem = _leaf_to_stem(leaf)
    if leaf.writer == "terminal":
        return _write_open_terminal_here(stem)
    if leaf.writer == "storage":
        return _write_storage_opener(stem)
    if leaf.writer == "show_multi":
        return _write_show_multi(stem)
    if leaf.writer == "remove_multi":
        return _write_remove_multi(stem)
    if leaf.writer == "add_multi":
        if leaf.id == "AddTags":
            return _write_add_tags_interactive(stem)
        if leaf.id == "AddHereOneLevel":
            return _write_add_dir_fixed(stem, "onelevel")
        if leaf.id == "AddHereRecursive":
            return _write_add_dir_fixed(stem, "full")
        if leaf.id == "AddHereRecursiveDryRun":
            return _write_add_dir_fixed(stem, "fulldry")
    raise ValueError(leaf)


def _command_line_for_leaf(leaf: _Leaf, bat: Path) -> str:
    if leaf.writer == "storage":
        return f'"{bat}" "%1"'
    return f'"{bat}" %*'


def format_install_plan() -> str:
    """Human-readable plan (no writes)."""
    lines: List[str] = []
    launcher = _launcher_dir()
    lines.append(f"Launcher directory: {launcher}")
    lines.append(f"Cascade parent: {_PARENT_LABEL} ({_PARENT_KEY})")
    lines.append(
        f"  Parent registry: (Default)=empty REG_SZ, MUIVerb={_PARENT_LABEL!r} "
        "(required for Explorer cascade; do not set parent default to the label text)."
    )
    lines.append("")
    for leaf in _LEAVES:
        stem = _leaf_to_stem(leaf)
        bat = launcher / f"{stem}.cmd"
        for kind in leaf.scopes:
            sk = _leaf_shell_path(kind, leaf.id)
            hk = rf"HKEY_CURRENT_USER\{sk}"
            cmd = _command_line_for_leaf(leaf, bat)
            lines.append(f"Leaf: {leaf.id}  scope={kind}")
            lines.append(f"  Menu: {leaf.menu_text}")
            lines.append(f"  Registry: {hk}")
            lines.append(f"  command: {hk}\\command  =>  {cmd}")
            lines.append(f"  Launcher: {bat}")
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

    # Write each unique launcher once (leaves may share scopes but unique stem per leaf)
    written: Dict[str, Path] = {}
    for leaf in _LEAVES:
        stem = _leaf_to_stem(leaf)
        if stem not in written:
            written[stem] = _write_leaf_launcher(leaf)

    for kind in ("file", "dir"):
        parent = _shell_root(kind)
        _reg_set(hkey, parent, None, "")
        _reg_set(hkey, parent, "MUIVerb", _PARENT_LABEL)

    for leaf in _LEAVES:
        bat = written[_leaf_to_stem(leaf)]
        cmd_line = _command_line_for_leaf(leaf, bat)
        for kind in leaf.scopes:
            sk = _leaf_shell_path(kind, leaf.id)
            _reg_set(hkey, sk, None, leaf.menu_text)
            _reg_set(hkey, sk + r"\command", None, cmd_line)
        messages.append(f"Registered '{leaf.menu_text}' -> {bat}")

    return 0, "\n".join(messages)


def uninstall_context_menu() -> Tuple[int, str]:
    """Remove registry entries created by :func:`install_context_menu`."""
    if sys.platform != "win32":
        return 1, "Windows only."

    import winreg

    hkey = winreg.HKEY_CURRENT_USER
    kinds = ("file", "dir")
    for kind in kinds:
        parent = _shell_root(kind)
        _reg_delete_subtree(hkey, parent)
    return 0, "Removed TagManager cascade from Explorer context menu (current user)."


def cascade_parent_registry_state_for_tests(hkey: int, parent_subkey: str) -> Tuple[Optional[str], Optional[str]]:
    """Read ``(default_sz, MUIVerb)`` under *parent_subkey* (HKCU-relative path).

    Used by integration tests to assert Explorer-safe cascade parents: default
    should be empty and ``MUIVerb`` should hold the visible label.
    """
    import winreg

    with winreg.OpenKey(hkey, parent_subkey) as k:
        default: Optional[str] = None
        try:
            val, typ = winreg.QueryValueEx(k, "")
            if typ in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                default = str(val)
        except OSError:
            pass
        mui: Optional[str] = None
        try:
            val2, typ2 = winreg.QueryValueEx(k, "MUIVerb")
            if typ2 in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                mui = str(val2)
        except OSError:
            pass
    return default, mui


def launcher_dir_for_docs() -> str:
    """Display path for help text."""
    return str(_launcher_dir())


def menu_leaves_for_tests() -> Tuple[_Leaf, ...]:
    """Expose leaf definitions for unit tests."""
    return _LEAVES


def shell_root_for_tests(kind: str) -> str:
    return _shell_root(kind)


def leaf_shell_path_for_tests(kind: str, leaf_id: str) -> str:
    return _leaf_shell_path(kind, leaf_id)


def leaf_to_stem_for_tests(leaf: _Leaf) -> str:
    return _leaf_to_stem(leaf)


def command_line_for_leaf_for_tests(leaf: _Leaf, bat: Path) -> str:
    return _command_line_for_leaf(leaf, bat)
