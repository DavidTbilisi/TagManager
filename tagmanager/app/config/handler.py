"""
Configuration Management CLI Handler

Provides command-line interface for configuration operations.
"""

import json
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .service import (
    get_configuration_value,
    set_configuration_value,
    delete_configuration_value,
    list_configuration_values,
    reset_configuration,
    validate_configuration_key,
    get_configuration_info,
    export_configuration,
    import_configuration,
    _get_configuration_categories,
)
from tagmanager import runtime

console = Console()


def handle_config_get(key: str) -> None:
    """Handle getting a configuration value"""
    if not validate_configuration_key(key):
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": False,
                    "error": "unknown_key",
                    "key": key,
                    "message": f"Unknown configuration key '{key}'",
                }
            )
            raise typer.Exit(1)
        console.print(f"[red]Error: Unknown configuration key '{key}'[/red]")
        console.print("[yellow]Use 'tm config list' to see available keys[/yellow]")
        return

    value, is_default = get_configuration_value(key)

    if value is None:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": False,
                    "error": "not_set",
                    "key": key,
                    "message": f"Configuration key '{key}' is not set",
                }
            )
            raise typer.Exit(1)
        console.print(f"[yellow]Configuration key '{key}' is not set[/yellow]")
        return

    if runtime.json_mode():
        runtime.emit_json(
            {
                "ok": True,
                "key": key,
                "value": value,
                "is_default": is_default,
                "type": type(value).__name__,
            }
        )
        return

    # Create a nice display
    status = "[dim](default)[/dim]" if is_default else "[green](user-set)[/green]"
    console.print(f"[bold]{key}[/bold] {status}")
    console.print(f"Value: [cyan]{value}[/cyan]")
    console.print(f"Type: [dim]{type(value).__name__}[/dim]")


def handle_config_set(key: str, value: str) -> None:
    """Handle setting a configuration value"""
    if not validate_configuration_key(key):
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": False,
                    "error": "unknown_key",
                    "key": key,
                    "message": f"Unknown configuration key '{key}'",
                }
            )
            raise typer.Exit(1)
        console.print(f"[red]Error: Unknown configuration key '{key}'[/red]")
        console.print("[yellow]Use 'tm config list' to see available keys[/yellow]")
        return

    ok = set_configuration_value(key, value)
    if runtime.json_mode():
        payload = {
            "ok": ok,
            "key": key,
            "value": value,
            "message": "Set" if ok else "Failed to set configuration value",
        }
        runtime.emit_json(payload)
        if not ok:
            raise typer.Exit(1)
        return

    if ok:
        console.print(f"[green]✓[/green] Set [bold]{key}[/bold] = [cyan]{value}[/cyan]")
    else:
        console.print(f"[red]✗[/red] Failed to set configuration value")


def handle_config_delete(key: str) -> None:
    """Handle deleting a configuration value"""
    if not validate_configuration_key(key):
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": False,
                    "error": "unknown_key",
                    "key": key,
                    "message": f"Unknown configuration key '{key}'",
                }
            )
            raise typer.Exit(1)
        console.print(f"[red]Error: Unknown configuration key '{key}'[/red]")
        return

    ok = delete_configuration_value(key)
    if runtime.json_mode():
        runtime.emit_json(
            {
                "ok": ok,
                "key": key,
                "message": (
                    "Deleted; value will use default"
                    if ok
                    else f"Configuration key '{key}' was not set"
                ),
            }
        )
        return

    if ok:
        console.print(f"[green]✓[/green] Deleted configuration key [bold]{key}[/bold]")
        console.print("[dim]Value will now use default[/dim]")
    else:
        console.print(f"[yellow]Configuration key '{key}' was not set[/yellow]")


def handle_config_list(
    category: Optional[str] = None,
    show_defaults: bool = False,
    output_format: str = "table",
) -> None:
    """Handle listing configuration values"""

    # Determine prefix based on category
    prefix = f"{category}." if category else ""

    # Validate category if provided
    if category and category not in _get_configuration_categories():
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": False,
                    "error": "unknown_category",
                    "category": category,
                    "available": list(_get_configuration_categories()),
                }
            )
            raise typer.Exit(1)
        console.print(f"[red]Error: Unknown category '{category}'[/red]")
        console.print(
            f"[yellow]Available categories: {', '.join(_get_configuration_categories())}[/yellow]"
        )
        return

    config_data = list_configuration_values(prefix, show_defaults)

    if not config_data:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": True,
                    "category": category,
                    "show_defaults": show_defaults,
                    "settings": {},
                    "message": "No configuration values in this view",
                }
            )
            return
        if category:
            console.print(
                f"[yellow]No configuration values found in category '{category}'[/yellow]"
            )
        else:
            console.print("[yellow]No configuration values set[/yellow]")

        if not show_defaults:
            console.print("[dim]Use --show-defaults to see default values[/dim]")
        return

    if runtime.json_mode():
        runtime.emit_json(
            {
                "ok": True,
                "category": category,
                "show_defaults": show_defaults,
                "settings": config_data,
            }
        )
        return

    if output_format == "json":
        console.print(json.dumps(config_data, indent=2))
        return

    # Create table display
    table = Table(
        title="Configuration Settings" + (f" - {category.title()}" if category else "")
    )
    table.add_column("Key", style="bold")
    table.add_column("Value", style="cyan")
    table.add_column("Type", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Description", style="dim", max_width=40)

    # Sort by key for consistent display
    for key in sorted(config_data.keys()):
        data = config_data[key]

        # Format value for display
        value_str = str(data["value"])
        if len(value_str) > 30:
            value_str = value_str[:27] + "..."

        # Status indicator
        status = "🔧 Default" if data["is_default"] else "✓ Set"

        table.add_row(key, value_str, data["type"], status, data["description"])

    console.print(table)

    # Show summary
    total_count = len(config_data)
    user_set_count = sum(1 for d in config_data.values() if not d["is_default"])
    default_count = total_count - user_set_count

    summary_text = f"Total: {total_count}"
    if show_defaults:
        summary_text += f" (User-set: {user_set_count}, Defaults: {default_count})"

    console.print(f"\n[dim]{summary_text}[/dim]")


def handle_config_reset(key: Optional[str] = None, confirm: bool = False) -> None:
    """Handle resetting configuration"""
    if key:
        # Reset specific key
        if not validate_configuration_key(key):
            if runtime.json_mode():
                runtime.emit_json(
                    {
                        "ok": False,
                        "error": "unknown_key",
                        "key": key,
                        "message": f"Unknown configuration key '{key}'",
                    }
                )
                raise typer.Exit(1)
            console.print(f"[red]Error: Unknown configuration key '{key}'[/red]")
            return

        if not confirm:
            if runtime.json_mode():
                runtime.emit_json(
                    {
                        "ok": False,
                        "error": "confirmation_required",
                        "message": "Non-interactive reset requires --yes (-y)",
                        "key": key,
                    }
                )
                raise typer.Exit(1)
            console.print(
                f"[yellow]This will reset '{key}' to its default value.[/yellow]"
            )
            if not typer.confirm("Continue?"):
                console.print("Cancelled.")
                return

        ok = reset_configuration(key)
        if runtime.json_mode():
            payload = {
                "ok": ok,
                "key": key,
                "scope": "key",
                "message": "Reset to default" if ok else "Failed to reset",
            }
            runtime.emit_json(payload)
            if not ok:
                raise typer.Exit(1)
            return

        if ok:
            console.print(f"[green]✓[/green] Reset [bold]{key}[/bold] to default value")
        else:
            console.print(f"[red]✗[/red] Failed to reset configuration key")

    else:
        # Reset all configuration
        if not confirm:
            if runtime.json_mode():
                runtime.emit_json(
                    {
                        "ok": False,
                        "error": "confirmation_required",
                        "message": "Non-interactive full reset requires --yes (-y)",
                        "scope": "all",
                    }
                )
                raise typer.Exit(1)
            console.print(
                "[red]⚠️  This will reset ALL configuration to defaults![/red]"
            )
            console.print("[yellow]All your custom settings will be lost.[/yellow]")
            if not typer.confirm("Are you sure?"):
                console.print("Cancelled.")
                return

        ok = reset_configuration()
        if runtime.json_mode():
            payload = {
                "ok": ok,
                "scope": "all",
                "message": "Reset all configuration to defaults"
                if ok
                else "Failed to reset configuration",
            }
            runtime.emit_json(payload)
            if not ok:
                raise typer.Exit(1)
            return

        if ok:
            console.print("[green]✓[/green] Reset all configuration to defaults")
        else:
            console.print("[red]✗[/red] Failed to reset configuration")


def handle_config_info() -> None:
    """Handle showing configuration system information"""
    info = get_configuration_info()

    if runtime.json_mode():
        payload = dict(info)
        payload["ok"] = True
        runtime.emit_json(payload)
        return

    # Create info panel
    info_text = f"""
[bold]Configuration Directory:[/bold] {info['config_dir']}
[bold]Configuration File:[/bold] {info['config_file']}
[bold]File Exists:[/bold] {'✓ Yes' if info['config_exists'] else '✗ No'}
[bold]Settings Count:[/bold] {info['total_settings']}
[bold]Available Keys:[/bold] {info['available_keys']}
[bold]Categories:[/bold] {', '.join(info['config_categories'])}
    """.strip()

    panel = Panel(
        info_text, title="Configuration System Information", border_style="blue"
    )

    console.print(panel)


def handle_config_export(file_path: Optional[str] = None) -> None:
    """Handle exporting configuration"""
    try:
        exported_path = export_configuration(file_path)
        if runtime.json_mode():
            runtime.emit_json(
                {"ok": True, "path": exported_path, "message": "Configuration exported"}
            )
        else:
            console.print(
                f"[green]✓[/green] Configuration exported to: [cyan]{exported_path}[/cyan]"
            )
    except Exception as e:
        if runtime.json_mode():
            runtime.emit_json(
                {"ok": False, "error": "export_failed", "message": str(e)}
            )
            raise typer.Exit(1)
        console.print(f"[red]✗[/red] Failed to export configuration: {e}")


def handle_config_import(file_path: str, merge: bool = True) -> None:
    """Handle importing configuration"""
    try:
        ok = import_configuration(file_path, merge)
        if runtime.json_mode():
            action = "merged" if merge else "replaced"
            runtime.emit_json(
                {
                    "ok": ok,
                    "path": file_path,
                    "merge": merge,
                    "action": action if ok else None,
                    "message": (
                        f"Configuration {action} from {file_path}"
                        if ok
                        else "Failed to import configuration"
                    ),
                }
            )
            if not ok:
                raise typer.Exit(1)
            return
        if ok:
            action = "merged" if merge else "replaced"
            console.print(
                f"[green]✓[/green] Configuration {action} from: [cyan]{file_path}[/cyan]"
            )
        else:
            console.print(f"[red]✗[/red] Failed to import configuration")
    except FileNotFoundError:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": False,
                    "error": "not_found",
                    "path": file_path,
                    "message": f"Configuration file not found: {file_path}",
                }
            )
            raise typer.Exit(1)
        console.print(f"[red]✗[/red] Configuration file not found: {file_path}")
    except Exception as e:
        if runtime.json_mode():
            runtime.emit_json(
                {"ok": False, "error": "import_failed", "message": str(e)}
            )
            raise typer.Exit(1)
        console.print(f"[red]✗[/red] Failed to import configuration: {e}")


def handle_config_categories() -> None:
    """Handle showing configuration categories"""
    categories = _get_configuration_categories()

    if runtime.json_mode():
        runtime.emit_json({"ok": True, "categories": list(categories)})
        return

    console.print("[bold]Configuration Categories:[/bold]")
    for category in categories:
        console.print(f"  • [cyan]{category}[/cyan]")

    console.print(
        f"\n[dim]Use 'tm config list --category <name>' to see category settings[/dim]"
    )


def handle_config_validate() -> None:
    """Handle validating current configuration"""
    config_data = list_configuration_values(show_defaults=False)

    if not config_data:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "ok": True,
                    "message": "No user configuration to validate",
                    "results": [],
                    "valid_count": 0,
                    "invalid_count": 0,
                }
            )
        else:
            console.print("[green]✓[/green] No user configuration to validate")
        return

    valid_count = 0
    invalid_count = 0
    results = []

    for key, data in config_data.items():
        try:
            # Re-validate the current value
            from ...config_manager import get_config_manager

            config_manager = get_config_manager()
            config_manager._validate_value(key, data["value"])

            results.append({"key": key, "ok": True, "error": None})
            valid_count += 1

        except Exception as e:
            results.append({"key": key, "ok": False, "error": str(e)})
            invalid_count += 1

    if runtime.json_mode():
        payload = {
            "ok": invalid_count == 0,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "results": results,
        }
        runtime.emit_json(payload)
        if not payload["ok"]:
            raise typer.Exit(1)
        return

    console.print("[bold]Validating configuration...[/bold]")
    for row in results:
        if row["ok"]:
            console.print(f"[green]✓[/green] {row['key']}")
        else:
            console.print(f"[red]✗[/red] {row['key']}: {row['error']}")

    # Summary
    console.print(f"\n[bold]Validation Summary:[/bold]")
    console.print(f"Valid: [green]{valid_count}[/green]")
    console.print(f"Invalid: [red]{invalid_count}[/red]")

    if invalid_count > 0:
        console.print(
            f"\n[yellow]Use 'tm config reset <key>' to fix invalid values[/yellow]"
        )


def handle_config_tui() -> None:
    """Interactive menu for essential settings (TTY only)."""
    if runtime.json_mode():
        runtime.emit_json(
            {
                "ok": False,
                "error": "interactive_only",
                "message": "tm config tui is not available with --json / TM_JSON",
            }
        )
        raise typer.Exit(1)

    from .tui import run_config_tui

    try:
        run_config_tui(console=console)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
