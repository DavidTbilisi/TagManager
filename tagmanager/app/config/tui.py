"""
Minimal interactive menu for the most-used TagManager settings.

Uses Rich (already a dependency). Requires a TTY.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from ...config_manager import get_config_manager
from .service import get_configuration_value, set_configuration_value, validate_configuration_key
from .tui_autotag_patterns import open_user_config_json, run_autotag_patterns_menu

_OUTPUT_FORMATS = ("table", "json", "csv", "tree", "yaml")

# Keys must exist in ConfigManager validation (``tm config set`` path).
TUI_ENTRIES: List[Dict[str, Any]] = [
    {
        "key": "storage.tag_file_path",
        "label": "Tag database JSON path",
        "kind": "str",
        "help": "Path to file_tags.json (supports ~)",
    },
    {
        "key": "display.colors",
        "label": "Colored terminal output",
        "kind": "bool",
    },
    {
        "key": "display.emojis",
        "label": "Emoji icons in listings",
        "kind": "bool",
    },
    {
        "key": "search.fuzzy_threshold",
        "label": "Fuzzy search similarity",
        "kind": "float",
        "min": 0.0,
        "max": 1.0,
        "help": "0.0 = loose matching, 1.0 = strict",
    },
    {
        "key": "files.include_hidden",
        "label": "Include hidden dotfiles",
        "kind": "bool",
    },
    {
        "key": "files.follow_symlinks",
        "label": "Follow symbolic links",
        "kind": "bool",
    },
    {
        "key": "backup.auto_backup",
        "label": "Auto-backup tag database",
        "kind": "bool",
    },
    {
        "key": "backup.count",
        "label": "Rotating backups to keep",
        "kind": "int",
        "min": 1,
        "max": 99,
    },
    {
        "key": "tags.auto_create",
        "label": "Auto-create tags when adding",
        "kind": "bool",
    },
    {
        "key": "output.format",
        "label": "Default CLI output format",
        "kind": "enum",
        "choices": list(_OUTPUT_FORMATS),
    },
    {
        "key": "display.max_items",
        "label": "Max rows in large tables",
        "kind": "int",
        "min": 1,
        "max": 1_000_000,
    },
]


def allowed_values_hint(entry: Dict[str, Any]) -> str:
    """Short hint for the menu: allowed enum values or numeric ranges."""
    kind = entry.get("kind")
    if kind == "bool":
        return "yes | no"
    if kind == "enum":
        choices = entry.get("choices") or []
        return ", ".join(str(c) for c in choices)
    if kind == "float":
        lo = entry.get("min", 0.0)
        hi = entry.get("max", 1.0)
        return f"{lo}–{hi}"
    if kind == "int":
        lo = int(entry.get("min", 1))
        hi = int(entry.get("max", 99))
        return f"{lo}–{hi} (integer)"
    if kind == "str":
        return str(entry.get("help") or "non-empty string")
    return "—"


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("true", "1", "yes", "on", "enabled")
    return bool(v)


def _current_display(key: str, raw: Any) -> str:
    if raw is None:
        return "(unset — using default)"
    if isinstance(raw, bool):
        return "yes" if raw else "no"
    return str(raw)


def _edit_bool(console: Console, label: str, current: Any) -> bool:
    """Pick yes/no explicitly (same UX as other enums)."""
    cur = _as_bool(current)
    opts = ("no", "yes")
    default_idx = 2 if cur else 1
    console.print(f"[bold]{label}[/bold] [dim](yes | no)[/dim]")
    for i, name in enumerate(opts, start=1):
        is_current = (name == "yes" and cur) or (name == "no" and not cur)
        mark = " ← current" if is_current else ""
        console.print(f"  {i}. {name}{mark}")
    while True:
        pick = IntPrompt.ask("Choice", default=default_idx, console=console)
        if pick == 1:
            return False
        if pick == 2:
            return True
        console.print("[red]Enter 1 (no) or 2 (yes).[/red]")


def _edit_str(console: Console, label: str, current: Any, help_text: str = "") -> str:
    default = "" if current is None else str(current)
    hint = f" ({help_text})" if help_text else ""
    while True:
        s = Prompt.ask(f"{label}{hint}", default=default, console=console).strip()
        if s:
            return s
        console.print("[red]Value cannot be empty.[/red]")


def _edit_float(
    console: Console,
    label: str,
    current: Any,
    lo: float,
    hi: float,
) -> float:
    while True:
        default = "0.6" if current is None else str(float(current))
        s = Prompt.ask(
            f"{label} [dim](allowed {lo}–{hi})[/dim]",
            default=default,
            console=console,
        ).strip()
        try:
            v = float(s)
        except ValueError:
            console.print("[red]Enter a number.[/red]")
            continue
        if not lo <= v <= hi:
            console.print(f"[red]Must be between {lo} and {hi}.[/red]")
            continue
        return v


def _edit_int(
    console: Console,
    label: str,
    current: Any,
    min_v: int,
    max_v: int,
) -> int:
    while True:
        if current is None:
            default_s = str(min_v)
        else:
            try:
                default_s = str(int(current))
            except (TypeError, ValueError):
                default_s = str(min_v)
        s = Prompt.ask(
            f"{label} [dim](allowed {min_v}–{max_v})[/dim]",
            default=default_s,
            console=console,
        ).strip()
        try:
            v = int(s, 10)
        except ValueError:
            console.print("[red]Enter an integer.[/red]")
            continue
        if v < min_v or v > max_v:
            console.print(f"[red]Must be between {min_v} and {max_v}.[/red]")
            continue
        return v


def _edit_enum(console: Console, label: str, choices: Tuple[str, ...], current: Any) -> str:
    """Numbered list; values stored lowercase for output.format-style keys."""
    norm = [str(c).lower() for c in choices]
    cur = (str(current).lower() if current is not None else norm[0])
    if cur not in norm:
        cur = norm[0]
    default_idx = norm.index(cur) + 1
    console.print(f"[bold]{label}[/bold] [dim]({', '.join(norm)})[/dim]")
    for i, name in enumerate(norm, start=1):
        mark = " ← current" if name == cur else ""
        console.print(f"  {i}. {name}{mark}")
    while True:
        pick = IntPrompt.ask("Choice", default=default_idx, console=console)
        if 1 <= pick <= len(norm):
            return norm[pick - 1]
        console.print(f"[red]Enter 1–{len(norm)}.[/red]")


def _apply_setting(console: Console, entry: Dict[str, Any]) -> None:
    key = entry["key"]
    label = entry["label"]
    kind = entry["kind"]
    raw, _is_default = get_configuration_value(key)
    help_text = str(entry.get("help") or "")

    if kind == "bool":
        new = _edit_bool(console, label, raw)
        ok = set_configuration_value(key, "true" if new else "false")
    elif kind == "str":
        new = _edit_str(console, label, raw, help_text)
        ok = set_configuration_value(key, new)
    elif kind == "float":
        lo = float(entry.get("min", 0.0))
        hi = float(entry.get("max", 1.0))
        new = _edit_float(console, label, raw, lo, hi)
        ok = set_configuration_value(key, str(new))
    elif kind == "int":
        lo = int(entry.get("min", 1))
        hi = int(entry.get("max", 99))
        new = _edit_int(console, label, raw, lo, hi)
        ok = set_configuration_value(key, str(new))
    elif kind == "enum":
        ch = tuple(str(x) for x in (entry.get("choices") or ()))
        if not ch:
            console.print("[red]enum kind requires choices[/red]")
            return
        new = _edit_enum(console, label, ch, raw)
        ok = set_configuration_value(key, new)
    else:
        console.print(f"[red]Unknown editor kind: {kind}[/red]")
        return

    if ok:
        console.print(f"[green]Saved[/green] [bold]{key}[/bold] = {_current_display(key, get_configuration_value(key)[0])}")
    else:
        console.print(f"[red]Failed to save {key}[/red]")


def _menu_table() -> Table:
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Setting")
    table.add_column("Current", style="cyan")
    table.add_column("Allowed", style="dim")

    for i, entry in enumerate(TUI_ENTRIES, start=1):
        key = entry["key"]
        raw, _ = get_configuration_value(key)
        table.add_row(
            str(i),
            entry["label"],
            _current_display(key, raw),
            allowed_values_hint(entry),
        )
    return table


def run_config_tui(console: Optional[Console] = None) -> None:
    """
    Run the settings menu until the user chooses Quit.

    No-op with a message when stdin is not a TTY.
    """
    console = console or Console()
    if not sys.stdin.isatty():
        console.print(
            "[yellow]Interactive settings need a terminal (TTY).[/yellow] "
            "Use [bold]tm config set <key> <value>[/bold] or edit config.json instead."
        )
        return

    mgr = get_config_manager()
    info = mgr.get_config_info()

    console.print(
        Panel.fit(
            "[bold]TagManager — quick settings[/bold]\n"
            f"[dim]Config file:[/dim] {info.get('config_file', '?')}",
            border_style="blue",
        )
    )

    while True:
        console.print()
        console.print(_menu_table())
        console.print()
        console.print("  [bold]0[/bold]  Quit")
        console.print("  [bold]p[/bold]  Show config paths")
        console.print("  [bold]a[/bold]  Auto-tag pattern packs (built-in groups + masters)")
        console.print("  [bold]e[/bold]  Open config.json in default app (custom JSON)")
        console.print()

        choice = Prompt.ask("Choice", default="0", console=console).strip().lower()
        if choice in ("0", "q", "quit", ""):
            console.print("[dim]Bye.[/dim]")
            return
        if choice == "p":
            console.print(f"[dim]Config directory:[/dim] {info.get('config_dir', '')}")
            console.print(f"[dim]Config file:[/dim] {info.get('config_file', '')}")
            continue
        if choice == "a":
            cfg_path = str(info.get("config_file", ""))
            try:
                run_autotag_patterns_menu(console, cfg_path)
            except KeyboardInterrupt:
                console.print("\n[yellow]Back to main menu.[/yellow]")
            continue
        if choice == "e":
            open_user_config_json(console, str(info.get("config_file", "")))
            continue
        try:
            n = int(choice, 10)
        except ValueError:
            console.print("[red]Enter a number, p, or 0.[/red]")
            continue
        if n < 1 or n > len(TUI_ENTRIES):
            console.print("[red]Unknown option.[/red]")
            continue

        entry = TUI_ENTRIES[n - 1]
        key = entry["key"]
        if not validate_configuration_key(key):
            console.print(f"[red]Invalid key in menu: {key}[/red]")
            continue
        try:
            _apply_setting(console, entry)
        except KeyboardInterrupt:
            console.print("\n[yellow]Edit cancelled.[/yellow]")


def tui_entry_keys() -> Tuple[str, ...]:
    """Keys exposed in the TUI (for tests)."""
    return tuple(e["key"] for e in TUI_ENTRIES)
