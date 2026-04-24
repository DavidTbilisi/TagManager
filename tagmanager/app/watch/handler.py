import json
import os
import time
import threading
from collections import deque
from typing import Any, Deque, Dict, List, Optional

import typer

from tagmanager import runtime

from .service import WatchEvent, start_watching, WATCHDOG_AVAILABLE

# Max recent events shown in the live display
_MAX_EVENTS = 30

_KIND_STYLE = {
    "created": ("green",  "✚ created"),
    "moved":   ("cyan",   "→ moved  "),
    "deleted": ("red",    "✖ deleted"),
}


def _format_path(path: str, watch_root: str) -> str:
    """Show path relative to the watch root if possible."""
    try:
        rel = os.path.relpath(path, watch_root)
        return rel if len(rel) < len(path) else path
    except ValueError:
        return path


def _watch_event_to_dict(ev: WatchEvent, watch_root: str) -> Dict[str, Any]:
    """Structured event for ``tm --json watch`` (one JSON object per line)."""
    d: Dict[str, Any] = {
        "event": "watch_file",
        "kind": ev.kind,
        "path": _format_path(ev.path, watch_root),
        "success": ev.success,
        "tags": list(ev.tags),
        "timestamp": ev.timestamp.isoformat(timespec="seconds"),
    }
    if ev.dest:
        d["dest"] = _format_path(ev.dest, watch_root)
    if ev.reason:
        d["reason"] = ev.reason
    return d


def _emit_watch_jsonl(obj: Dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def _render_event_line(ev: WatchEvent, watch_root: str) -> str:
    color, verb = _KIND_STYLE.get(ev.kind, ("white", ev.kind))
    ts = ev.timestamp.strftime("%H:%M:%S")
    short = _format_path(ev.path, watch_root)
    if ev.kind == "moved" and ev.dest:
        dest_short = _format_path(ev.dest, watch_root)
        detail = f"{short}  →  {dest_short}"
    else:
        detail = short

    status = "✓" if ev.success else "✗"
    tag_part = ""
    if ev.tags:
        tag_part = "  [" + ", ".join(ev.tags[:6]) + (", …" if len(ev.tags) > 6 else "") + "]"
    reason_part = f"  ({ev.reason})" if not ev.success and ev.reason else ""

    return f"[{ts}] {verb} {status}  {detail}{tag_part}{reason_part}"


def _try_rich_live(
    watch_path: str,
    recursive: bool,
    extra_tags: List[str],
    preset_name: Optional[str],
    auto_tag: bool,
    content_tag: bool,
    on_delete_clean: bool,
    ignore_patterns: List[str],
) -> None:
    """Run the watcher with a Rich live-updating display."""
    from rich.live import Live
    from rich.table import Table
    from rich.text import Text
    from rich.panel import Panel
    from rich.console import Console

    console = Console()
    events: Deque[WatchEvent] = deque(maxlen=_MAX_EVENTS)
    lock = threading.Lock()
    total = [0]

    def on_event(ev: WatchEvent) -> None:
        with lock:
            events.append(ev)
            total[0] += 1

    observer = start_watching(
        path=watch_path,
        recursive=recursive,
        extra_tags=extra_tags,
        preset_name=preset_name,
        auto_tag=auto_tag,
        content_tag=content_tag,
        on_delete_clean=on_delete_clean,
        ignore_patterns=ignore_patterns,
        on_event=on_event,
    )

    def build_display():
        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column(no_wrap=True)
        with lock:
            snapshot = list(events)
        if not snapshot:
            table.add_row(Text("  Waiting for file events…", style="dim"))
        else:
            for ev in reversed(snapshot):
                color, verb = _KIND_STYLE.get(ev.kind, ("white", ev.kind))
                table.add_row(Text(_render_event_line(ev, watch_path), style=color if ev.success else "red"))

        mode_parts = []
        if recursive:
            mode_parts.append("recursive")
        if auto_tag:
            mode_parts.append("auto-tag")
        if extra_tags:
            mode_parts.append(f"tags=[{', '.join(extra_tags)}]")
        if preset_name:
            mode_parts.append(f"preset={preset_name}")
        if on_delete_clean:
            mode_parts.append("clean-on-delete")
        if ignore_patterns:
            mode_parts.append(f"ignore={ignore_patterns}")
        mode_str = "  ".join(mode_parts) or "default"

        title = (
            f"[bold cyan]TagManager Watch[/bold cyan]  "
            f"[dim]{watch_path}[/dim]  "
            f"[yellow]{total[0]} events[/yellow]"
        )
        subtitle = f"[dim]{mode_str}[/dim]  [dim italic]Ctrl+C to stop[/dim italic]"

        return Panel(table, title=title, subtitle=subtitle, border_style="bright_black")

    try:
        with Live(build_display(), refresh_per_second=4, console=console) as live:
            while observer.is_alive():
                live.update(build_display())
                time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        console.print(f"\n[dim]Watch stopped. {total[0]} events processed.[/dim]")


def _fallback_plain(
    watch_path: str,
    recursive: bool,
    extra_tags: List[str],
    preset_name: Optional[str],
    auto_tag: bool,
    content_tag: bool,
    on_delete_clean: bool,
    ignore_patterns: List[str],
) -> None:
    """Simple line-by-line output fallback if Rich Live is unavailable."""
    total = [0]

    def on_event(ev: WatchEvent) -> None:
        total[0] += 1
        line = _render_event_line(ev, watch_path)
        typer.echo(line)

    observer = start_watching(
        path=watch_path,
        recursive=recursive,
        extra_tags=extra_tags,
        preset_name=preset_name,
        auto_tag=auto_tag,
        content_tag=content_tag,
        on_delete_clean=on_delete_clean,
        ignore_patterns=ignore_patterns,
        on_event=on_event,
    )

    try:
        while observer.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        typer.echo(f"\nWatch stopped. {total[0]} events processed.")


def _run_watch_jsonl(
    watch_path: str,
    recursive: bool,
    extra_tags: List[str],
    preset_name: Optional[str],
    auto_tag: bool,
    content_tag: bool,
    on_delete_clean: bool,
    ignore_patterns: List[str],
) -> None:
    """Stream one JSON object per line (NDJSON) on stdout; no Rich UI."""
    total = [0]

    def on_event(ev: WatchEvent) -> None:
        total[0] += 1
        _emit_watch_jsonl(_watch_event_to_dict(ev, watch_path))

    observer = start_watching(
        path=watch_path,
        recursive=recursive,
        extra_tags=extra_tags,
        preset_name=preset_name,
        auto_tag=auto_tag,
        content_tag=content_tag,
        on_delete_clean=on_delete_clean,
        ignore_patterns=ignore_patterns,
        on_event=on_event,
    )

    try:
        while observer.is_alive():
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        _emit_watch_jsonl(
            {
                "event": "watch_stopped",
                "ok": True,
                "events_processed": total[0],
                "watch_path": watch_path,
            }
        )


def handle_watch_command(
    watch_path: str,
    recursive: bool,
    extra_tags: List[str],
    preset_name: Optional[str],
    auto_tag: bool,
    content_tag: bool,
    on_delete_clean: bool,
    ignore_patterns: List[str],
    plain: bool,
) -> None:
    if not WATCHDOG_AVAILABLE:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": False,
                    "error": "watchdog_not_installed",
                    "message": "Install watchdog: pip install watchdog or pip install tagmanager-cli[watch]",
                }
            )
        else:
            typer.echo(
                "Error: watchdog is not installed.\n"
                "Install it with:\n"
                "  pip install watchdog\n"
                "  or: pip install tagmanager-cli[watch]",
                err=True,
            )
        raise typer.Exit(1)

    abs_path = os.path.abspath(watch_path)
    if not os.path.isdir(abs_path):
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": False,
                    "error": "not_a_directory",
                    "path": watch_path,
                    "message": f"'{watch_path}' is not a directory.",
                }
            )
        else:
            typer.echo(f"Error: '{watch_path}' is not a directory.", err=True)
        raise typer.Exit(1)

    if runtime.json_mode():
        _emit_watch_jsonl(
            {
                "event": "watch_started",
                "ok": True,
                "watch_path": abs_path,
                "recursive": recursive,
                "extra_tags": list(extra_tags),
                "preset": preset_name,
                "auto_tag": auto_tag,
                "content_tag": content_tag,
                "clean_on_delete": on_delete_clean,
                "ignore_patterns": list(ignore_patterns),
            }
        )
        _run_watch_jsonl(
            watch_path=abs_path,
            recursive=recursive,
            extra_tags=extra_tags,
            preset_name=preset_name,
            auto_tag=auto_tag,
            content_tag=content_tag,
            on_delete_clean=on_delete_clean,
            ignore_patterns=ignore_patterns,
        )
        return

    typer.echo(f"Watching: {abs_path}")
    typer.echo(
        f"  Recursive: {recursive} | Auto-tag: {auto_tag} | "
        f"Content rules: {content_tag} | Clean-on-delete: {on_delete_clean}"
    )
    if extra_tags:
        typer.echo(f"  Always add tags: {extra_tags}")
    if preset_name:
        typer.echo(f"  Preset: {preset_name}")
    if ignore_patterns:
        typer.echo(f"  Ignoring: {ignore_patterns}")
    typer.echo("Press Ctrl+C to stop.\n")

    runner = _fallback_plain if plain else _try_rich_live
    runner(
        watch_path=abs_path,
        recursive=recursive,
        extra_tags=extra_tags,
        preset_name=preset_name,
        auto_tag=auto_tag,
        content_tag=content_tag,
        on_delete_clean=on_delete_clean,
        ignore_patterns=ignore_patterns,
    )
