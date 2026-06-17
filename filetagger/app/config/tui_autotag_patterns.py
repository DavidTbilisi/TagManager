"""
Auto-tag built-in pattern groups (``tm config tui`` submenu).

``autotag.content_pattern_groups``: ``null``/missing = all packs on; ``[]`` = none;
otherwise a list of group ids from ``content_rule_groups.CONTENT_RULE_GROUPS``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any, Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ...config_manager import get_config_manager
from ..autotag.content_rule_groups import ALL_GROUP_IDS, CONTENT_RULE_GROUPS
from .service import set_configuration_value


def _as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("true", "1", "yes", "on", "enabled")
    return bool(v)


def _effective_pattern_group_ids(mgr: Any) -> Set[str]:
    raw = mgr.get("autotag.content_pattern_groups")
    if raw is None:
        return set(ALL_GROUP_IDS)
    if not isinstance(raw, list):
        return set(ALL_GROUP_IDS)
    return {str(x) for x in raw if str(x) in ALL_GROUP_IDS}


def _persist_pattern_groups(mgr: Any, enabled: Set[str]) -> None:
    if enabled == set(ALL_GROUP_IDS):
        mgr.delete("autotag.content_pattern_groups")
    elif not enabled:
        mgr.set("autotag.content_pattern_groups", [])
    else:
        mgr.set("autotag.content_pattern_groups", sorted(enabled))


def _toggle_bool_key(key: str, label: str, console: Console, default: bool) -> None:
    mgr = get_config_manager()
    cur = _as_bool(mgr.get(key, default))
    new = not cur
    if set_configuration_value(key, "true" if new else "false"):
        console.print(f"[green]{label}[/green] → [bold]{'yes' if new else 'no'}[/bold]")
    else:
        console.print(f"[red]Failed to set {key}[/red]")


def _toggle_pattern_group(console: Console, index: int) -> None:
    if index < 1 or index > len(CONTENT_RULE_GROUPS):
        console.print("[red]Invalid group number.[/red]")
        return
    gid = str(CONTENT_RULE_GROUPS[index - 1]["id"])
    mgr = get_config_manager()
    eff = _effective_pattern_group_ids(mgr)
    if gid in eff:
        eff.remove(gid)
        console.print(f"[dim]Off:[/dim] {gid}")
    else:
        eff.add(gid)
        console.print(f"[dim]On:[/dim] {gid}")
    _persist_pattern_groups(mgr, eff)


def open_user_config_json(console: Console, path: str) -> None:
    p = os.path.abspath(os.path.expanduser(path))
    console.print(f"[dim]Opening[/dim] [cyan]{p}[/cyan]")
    try:
        if sys.platform.startswith("win"):
            os.startfile(p)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
            if editor:
                subprocess.Popen([editor, p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["xdg-open", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        console.print(f"[red]Could not open file: {exc}[/red]")


def run_autotag_patterns_menu(console: Console, config_file: str) -> None:
    """Interactive toggles for autotag masters and built-in pattern groups."""
    mgr = get_config_manager()

    while True:
        en = _as_bool(mgr.get("autotag.enabled", True))
        ce = _as_bool(mgr.get("autotag.content_enabled", False))
        ud = _as_bool(mgr.get("autotag.content_use_defaults", True))
        eff = _effective_pattern_group_ids(mgr)
        raw_groups = mgr.get("autotag.content_pattern_groups")
        pack_note = (
            "[dim]all built-in packs on (default)[/dim]"
            if raw_groups is None
            else ("[dim]no built-in packs[/dim]" if raw_groups == [] else "[dim]custom subset[/dim]")
        )

        console.print()
        console.print(
            Panel.fit(
                "[bold]Auto-tag — masters[/bold]\n"
                f"  [cyan]E[/cyan]  Autotag overall (extensions + rules)  [{'ON' if en else 'OFF'}]\n"
                f"  [cyan]C[/cyan]  Content / title / filename rules        [{'ON' if ce else 'OFF'}]\n"
                f"  [cyan]D[/cyan]  Use built-in default rule packs         [{'ON' if ud else 'OFF'}]\n"
                f"  {pack_note}",
                border_style="magenta",
            )
        )

        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=4)
        table.add_column("Pattern pack", style="white")
        table.add_column("", width=6)

        for i, group in enumerate(CONTENT_RULE_GROUPS, start=1):
            gid = str(group["id"])
            on = gid in eff
            table.add_row(str(i), str(group["title"]), "[green]ON[/green]" if on else "[dim]off[/dim]")

        console.print(table)
        console.print(
            "[dim]Tip: add custom rules under \"autotag\" → \"content_rules\" in config.json[/dim]"
        )
        console.print(
            "  [bold]+[/bold]  Turn all packs on (clear [cyan]autotag.content_pattern_groups[/cyan])\n"
            "  [bold]O[/bold]  Open config.json (edit JSON; custom [cyan]content_rules[/cyan])\n"
            "  [bold]0[/bold]  Back to main menu"
        )

        ch = Prompt.ask("Toggle [E/C/D], pack [1–N], +, O, or 0", default="0", console=console).strip()

        if not ch or ch == "0":
            return
        cu = ch.upper()
        if cu == "E":
            _toggle_bool_key("autotag.enabled", "autotag.enabled", console, True)
            continue
        if cu == "C":
            _toggle_bool_key("autotag.content_enabled", "autotag.content_enabled", console, False)
            continue
        if cu == "D":
            _toggle_bool_key(
                "autotag.content_use_defaults",
                "autotag.content_use_defaults",
                console,
                True,
            )
            continue
        if ch == "+":
            mgr.delete("autotag.content_pattern_groups")
            console.print("[green]All built-in pattern packs enabled[/green] (config key removed).")
            continue
        if cu == "O":
            open_user_config_json(console, config_file)
            continue
        if ch.isdigit():
            _toggle_pattern_group(console, int(ch, 10))
            continue
        console.print("[red]Unrecognized choice.[/red]")
