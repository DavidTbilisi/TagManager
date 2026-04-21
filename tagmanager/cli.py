#!/usr/bin/env python3
"""
TagManager CLI Entry Point
"""

import os
import sys
from typing import List, Optional

import typer

from .app.add.service import add_tags, add_tags_recursive
from .app.bulk.handler import handle_bulk_add, handle_bulk_remove, handle_bulk_retag
from .app.filter.handler import (
    handle_filter_duplicates,
    handle_filter_orphans,
    handle_filter_similar,
    handle_filter_clusters,
    handle_filter_isolated,
)
from .app.list_all.service import print_list_tags_all_table
from .app.paths.service import path_tags, fuzzy_search_path
from .app.remove.service import remove_path, remove_invalid_paths, remove_all_tags
from .app.search.service import (
    combined_search,
    search_files_by_path,
    search_files_by_tags,
)
from .app.stats.handler import handle_stats_command
from .app.storage.service import show_storage_location, open_storage_location
from .app.tags.service import (
    list_all_tags,
    search_files_by_tag,
    open_list_files_by_tag_result,
)
from .app.visualization.handler import (
    handle_tree_view,
    handle_tag_cloud,
    handle_stats_charts,
)
from .app.config.handler import (
    handle_config_get,
    handle_config_set,
    handle_config_delete,
    handle_config_list,
    handle_config_reset,
    handle_config_info,
    handle_config_export,
    handle_config_import,
    handle_config_categories,
    handle_config_validate,
)
from .app.alias.service import (
    get_aliases,
    add_alias,
    remove_alias,
    clear_aliases,
)
from .app.preset.service import (
    get_preset,
    save_preset,
    delete_preset,
    list_presets,
)
from .app.move.service import move_path, clean_missing
from .app.graph.handler import handle_graph_command
from .app.watch.handler import handle_watch_command
from .app.exportdata.service import export_tags_json, export_tags_csv, import_tags


try:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


# ---------------------------------------------------------------------------
# Shell completion helpers
# ---------------------------------------------------------------------------

def _complete_tags(incomplete: str) -> List[str]:
    """Return existing tag names that start with the incomplete string."""
    try:
        return [t for t in list_all_tags() if t.lower().startswith(incomplete.lower())]
    except Exception:
        return []


def _complete_preset_names(incomplete: str) -> List[str]:
    """Return preset names that start with the incomplete string."""
    try:
        return [n for n in list_presets() if n.lower().startswith(incomplete.lower())]
    except Exception:
        return []


def _complete_alias_names(incomplete: str) -> List[str]:
    """Return alias names that start with the incomplete string."""
    try:
        return [a for a in get_aliases() if a.lower().startswith(incomplete.lower())]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="tm",
    help="TagManager - The Ultimate Command-Line File Tagging System",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Core commands
# ---------------------------------------------------------------------------

@app.command()
def add(
    file: str = typer.Argument(
        ...,
        help="Path to a file, or a directory when using --recursive",
    ),
    tags: List[str] = typer.Option(
        None, "-t", "--tags",
        help="Tags to add (comma-separated or multiple --tags)",
        autocompletion=_complete_tags,
    ),
    preset: Optional[str] = typer.Option(
        None, "--preset", "-P",
        help="Apply a saved preset of tags",
        autocompletion=_complete_preset_names,
    ),
    recursive: bool = typer.Option(
        False,
        "-r",
        "--recursive",
        help="If path is a directory, tag every file under it (rule-based extension tags per file)",
    ),
    no_auto: bool = typer.Option(False, "--no-auto", help="Skip extension-based auto-tagging"),
    no_aliases: bool = typer.Option(False, "--no-aliases", help="Skip alias resolution"),
):
    """Add tags to a file (with optional preset and auto-tagging)"""
    flat: List[str] = []
    for tag_group in (tags or []):
        flat.extend(t.strip() for t in tag_group.split(",") if t.strip())

    if preset:
        preset_tags = get_preset(preset)
        if preset_tags is None:
            typer.echo(f"Error: preset '{preset}' not found. Use 'tm preset list' to see available presets.")
            raise typer.Exit(1)
        for t in preset_tags:
            if t not in flat:
                flat.append(t)

    if not flat and no_auto:
        typer.echo("Error: no tags provided.")
        raise typer.Exit(1)

    abs_target = os.path.abspath(os.path.join(os.getcwd(), file))
    if recursive:
        if not os.path.isdir(abs_target):
            typer.echo(
                f"Error: --recursive requires a directory; '{abs_target}' is not a directory."
            )
            raise typer.Exit(1)
        result = add_tags_recursive(
            file,
            flat,
            apply_aliases=not no_aliases,
            auto_tag=not no_auto,
        )
        if not result.get("success"):
            raise typer.Exit(1)
        return

    add_tags(file, flat or [""], apply_aliases=not no_aliases, auto_tag=not no_auto)


@app.command()
def remove(
    path: Optional[str] = typer.Option(None, "-p", "--path", help="Path to the file"),
    invalid: bool = typer.Option(
        False, "-i", "--invalid", help="Remove invalid paths from tags"
    ),
    all_tags: bool = typer.Option(
        False, "--all-tags", help="Clear ALL tags from a file (keeps the entry, just empties its tags)"
    ),
):
    """Remove a file from tags, clean invalid paths, or clear all tags from a file"""
    if all_tags and path:
        result = remove_all_tags(path)
        typer.echo(result["message"])
        if not result["success"]:
            raise typer.Exit(1)
    elif path:
        remove_path(path)
    elif invalid:
        remove_invalid_paths()
    else:
        typer.echo("No arguments provided")


@app.command("ls")
def list_all(
    all: Optional[str] = typer.Option(None, "--all", help="Not implemented"),
    ext: Optional[str] = typer.Option(None, "--ext", help="Not implemented"),
    tree: bool = typer.Option(False, "--tree", help="Display files in tree view"),
):
    """List files and tags in a table or tree view"""
    if tree:
        handle_tree_view()
    else:
        print_list_tags_all_table()


@app.command()
def path(
    filepath: str = typer.Argument(..., help="Path to the file"),
    fuzzy: bool = typer.Option(False, "-f", "--fuzzy", help="Type of search to use"),
    folder: bool = typer.Option(
        False, "-F", "--folder", help="Search for a folder instead of a file"
    ),
    exact: bool = typer.Option(
        False, "-e", "--exact", help="Exact match for file path"
    ),
):
    """List tags of a file"""
    if fuzzy:
        result = fuzzy_search_path(filepath)
    else:
        result = path_tags(filepath)
    if json_out:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result)
    json_out: bool = typer.Option(False, "--json", help="Output results as JSON"),


@app.command()
def tags(
    search: Optional[str] = typer.Option(
        None, "-s", "--search", help="List files by a specific tag",
        autocompletion=_complete_tags,
    ),
    open: bool = typer.Option(False, "-o", "--open", help="Open the file"),
    exact: bool = typer.Option(False, "-e", "--exact", help="Exact match for tag"),
    where: bool = typer.Option(
        False, "-w", "--where", help="Display the path of the file"
    ),
    cloud: bool = typer.Option(False, "--cloud", help="Display tags as a visual cloud"),
):
    """List all tags or display as a cloud"""
    if cloud:
        handle_tag_cloud()
    elif search and open:
        open_list_files_by_tag_result(search_files_by_tag(search, exact))
    elif search:
        result = search_files_by_tag(search, exact)
        if json_out:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            for i, file in enumerate(result, start=1):
                print(f"{i}. {file}")
    else:
        tags_list = list_all_tags()
        if json_out:
            print(json.dumps(tags_list, indent=2, ensure_ascii=False))
        else:
            for i, tag in enumerate(tags_list, start=1):
                print(f"{i}. {tag}")


@app.command()
def storage(
    open: bool = typer.Option(False, "-o", "--open", help="Open the storage location")
):
    """Display storage location of the tag file"""
    if open:
        open_storage_location()
    else:
        print(show_storage_location())


@app.command()
def search(
    tags: Optional[List[str]] = typer.Option(
        None, "-t", "--tags", help="Tags to search for (OR by default, AND with --match-all)",
        autocompletion=_complete_tags,
    ),
    path: Optional[str] = typer.Option(
        None, "-p", "--path", help="Path query to search for"
    ),
    match_all: bool = typer.Option(
        False, "-a", "--match-all", help="Require ALL listed tags (AND)"
    ),
    exclude: Optional[List[str]] = typer.Option(
        None, "-x", "--exclude", help="Exclude files that have ANY of these tags (NOT)",
        autocompletion=_complete_tags,
    ),
    exact: bool = typer.Option(False, "-e", "--exact", help="Exact tag match (no fuzzy)"),
    open: bool = typer.Option(False, "-o", "--open", help="Open the matched file(s)"),
):
    """Search files by tags or path. Supports AND (--match-all) and NOT (--exclude)."""
    if tags and path:
        result = combined_search(tags, path, match_all, exclude_tags=exclude)
    elif tags:
        result = search_files_by_tags(tags, match_all, exact, exclude_tags=exclude)
    elif path:
        result = search_files_by_path(path)
    else:
        typer.echo("No search criteria provided.")
        typer.echo("Examples:")
        typer.echo("  tm search -t python                   # files tagged python")
        typer.echo("  tm search -t python -t web --match-all # both tags")
        typer.echo("  tm search -t python --exclude legacy   # python but not legacy")
        return

    if result:
        for i, file in enumerate(result, start=1):
            print(f"{i}. {file}")
        print()
    else:
        print("No files found matching the criteria.")


@app.command("mv")
def mv(
    old_path: str = typer.Argument(..., help="Current path tracked in TagManager"),
    new_path: str = typer.Argument(..., help="New path to associate tags with"),
):
    """Update the tag record when a file is moved or renamed"""
    success, message = move_path(old_path, new_path)
    typer.echo(message)
    if not success:
        raise typer.Exit(1)


@app.command()
def clean(
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be removed without making changes"
    ),
):
    """Remove tag records for files that no longer exist on disk"""
    result = clean_missing(dry_run=dry_run)
    if result["count"] == 0:
        typer.echo("No missing paths found. Tag database is clean.")
    else:
        prefix = "[dry-run] " if dry_run else ""
        for p in result["missing"]:
            typer.echo(f"  {prefix}Remove: {p}")
        typer.echo(result["message"])


@app.command()
def stats(
    tag: Optional[str] = typer.Option(
        None, "--tag", help="Show statistics for a specific tag"
    ),
    file_count: bool = typer.Option(
        False, "--file-count", help="Show files per tag distribution"
    ),
    chart: bool = typer.Option(
        False, "--chart", help="Display statistics as ASCII charts"
    ),
):
    """Show tag statistics and analytics"""
    if chart:
        handle_stats_charts()
    else:
        handle_stats_command(tag=tag, file_count=file_count)


# ---------------------------------------------------------------------------
# Sub-apps
# ---------------------------------------------------------------------------

bulk_app = typer.Typer(help="Bulk tag operations")
filter_app = typer.Typer(help="Smart filtering and analysis")
config_app = typer.Typer(help="Configuration management")
alias_app = typer.Typer(help="Tag alias management")
preset_app = typer.Typer(help="Tag preset management")

app.add_typer(bulk_app,   name="bulk")
app.add_typer(filter_app, name="filter")
app.add_typer(config_app, name="config")
app.add_typer(alias_app,  name="alias")
app.add_typer(preset_app, name="preset")


# ---------------------------------------------------------------------------
# Bulk sub-commands
# ---------------------------------------------------------------------------

@bulk_app.command("add")
def bulk_add(
    pattern: str = typer.Argument(..., help="Glob pattern to match files"),
    tags: List[str] = typer.Option(
        ..., "--tags", "-t", help="Tags to add",
        autocompletion=_complete_tags,
    ),
    base_path: Optional[str] = typer.Option(None, "--base", "-b", help="Base directory for glob"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
):
    """Add tags to all files matching a glob pattern"""
    flat = [t.strip() for tg in tags for t in tg.split(",") if t.strip()]
    handle_bulk_add(pattern, flat, base_path, dry_run)


@bulk_app.command("remove")
def bulk_remove(
    tag: Optional[str] = typer.Option(None, "--tag", help="Remove all files with this tag", autocompletion=_complete_tags),
    remove_tag: Optional[str] = typer.Option(None, "--remove-tag", help="Remove this tag from all files", autocompletion=_complete_tags),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
):
    """Remove files by tag or remove tag from all files"""
    handle_bulk_remove(tag, remove_tag, dry_run)


@bulk_app.command("retag")
def bulk_retag(
    from_tag: str = typer.Option(..., "--from", help="Current tag name to replace", autocompletion=_complete_tags),
    to_tag: str = typer.Option(..., "--to", help="New tag name"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done"),
):
    """Rename a tag across all files"""
    handle_bulk_retag(from_tag, to_tag, dry_run)


# ---------------------------------------------------------------------------
# Filter sub-commands
# ---------------------------------------------------------------------------

@filter_app.command("duplicates")
def filter_duplicates():
    """Find files with identical tag sets"""
    handle_filter_duplicates()


@filter_app.command("orphans")
def filter_orphans():
    """Find files with no tags"""
    handle_filter_orphans()


@filter_app.command("similar")
def filter_similar(
    file_path: str = typer.Argument(..., help="Path to the target file"),
    threshold: float = typer.Option(0.3, "--threshold", "-t", help="Similarity threshold (0.0-1.0)"),
):
    """Find files with similar tags to a target file"""
    handle_filter_similar(file_path, threshold)


@filter_app.command("clusters")
def filter_clusters(
    min_size: int = typer.Option(2, "--min-size", "-s", help="Minimum files in a cluster"),
):
    """Find clusters of files sharing common tags"""
    handle_filter_clusters(min_size)


@filter_app.command("isolated")
def filter_isolated(
    max_shared: int = typer.Option(1, "--max-shared", "-m", help="Maximum shared tags"),
):
    """Find files that share few tags with others"""
    handle_filter_isolated(max_shared)


# ---------------------------------------------------------------------------
# Config sub-commands
# ---------------------------------------------------------------------------

@config_app.command("get")
def config_get(key: str = typer.Argument(..., help="Configuration key to retrieve")):
    """Get a configuration value"""
    handle_config_get(key)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to set"),
):
    """Set a configuration value"""
    handle_config_set(key, value)


@config_app.command("delete")
def config_delete(key: str = typer.Argument(..., help="Configuration key to delete")):
    """Delete a configuration value (revert to default)"""
    handle_config_delete(key)


@config_app.command("list")
def config_list(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    show_defaults: bool = typer.Option(False, "--show-defaults", "-d", help="Show default values"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)"),
):
    """List configuration values"""
    handle_config_list(category, show_defaults, output_format)


@config_app.command("reset")
def config_reset(
    key: Optional[str] = typer.Argument(None, help="Configuration key to reset"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Reset configuration to defaults"""
    handle_config_reset(key, yes)


@config_app.command("info")
def config_info():
    """Show configuration system information"""
    handle_config_info()


@config_app.command("export")
def config_export(
    file_path: Optional[str] = typer.Option(None, "--file", "-f", help="Export file path"),
):
    """Export configuration to a file"""
    handle_config_export(file_path)


@config_app.command("import")
def config_import(
    file_path: str = typer.Argument(..., help="Configuration file to import"),
    replace: bool = typer.Option(False, "--replace", help="Replace entire configuration"),
):
    """Import configuration from a file"""
    handle_config_import(file_path, not replace)


@config_app.command("categories")
def config_categories():
    """Show available configuration categories"""
    handle_config_categories()


@config_app.command("validate")
def config_validate():
    """Validate current configuration"""
    handle_config_validate()


# ---------------------------------------------------------------------------
# Alias sub-commands
# ---------------------------------------------------------------------------

@alias_app.command("add")
def alias_add(
    alias: str = typer.Argument(..., help="The shorthand alias (e.g. 'py')"),
    canonical: str = typer.Argument(..., help="The canonical tag it maps to (e.g. 'python')", autocompletion=_complete_tags),
):
    """Add a tag alias (e.g. 'py' -> 'python')"""
    if add_alias(alias, canonical):
        typer.echo(f"Alias added: '{alias}' -> '{canonical}'")
    else:
        typer.echo("Error: alias and canonical must be different non-empty strings.")
        raise typer.Exit(1)


@alias_app.command("remove")
def alias_remove(
    alias: str = typer.Argument(..., help="The alias to remove", autocompletion=_complete_alias_names),
):
    """Remove a tag alias"""
    if remove_alias(alias):
        typer.echo(f"Alias '{alias}' removed.")
    else:
        typer.echo(f"Alias '{alias}' not found.")
        raise typer.Exit(1)


@alias_app.command("list")
def alias_list():
    """List all configured tag aliases"""
    aliases = get_aliases()
    if not aliases:
        typer.echo("No aliases configured. Use 'tm alias add <alias> <canonical>' to add one.")
        return
    for alias, canonical in sorted(aliases.items()):
        typer.echo(f"  {alias:20s} -> {canonical}")


@alias_app.command("clear")
def alias_clear(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Remove all tag aliases"""
    if not yes:
        typer.confirm("Remove all aliases?", abort=True)
    count = clear_aliases()
    typer.echo(f"Removed {count} alias(es).")


# ---------------------------------------------------------------------------
# Preset sub-commands
# ---------------------------------------------------------------------------

@preset_app.command("save")
def preset_save(
    name: str = typer.Argument(..., help="Name for this preset"),
    tags: List[str] = typer.Option(
        ..., "--tags", "-t", help="Tags in this preset",
        autocompletion=_complete_tags,
    ),
):
    """Save a named preset of tags"""
    flat = [t.strip() for tg in tags for t in tg.split(",") if t.strip()]
    if save_preset(name, flat):
        typer.echo(f"Preset '{name}' saved with tags: {', '.join(flat)}")
    else:
        typer.echo("Error: preset name and at least one tag are required.")
        raise typer.Exit(1)


@preset_app.command("list")
def preset_list():
    """List all saved presets"""
    presets = list_presets()
    if not presets:
        typer.echo("No presets saved. Use 'tm preset save <name> --tags ...' to create one.")
        return
    for name, ptags in sorted(presets.items()):
        typer.echo(f"  {name:20s}: {', '.join(ptags)}")


@preset_app.command("apply")
def preset_apply(
    name: str = typer.Argument(..., help="Preset name to apply", autocompletion=_complete_preset_names),
    file: str = typer.Argument(..., help="File or directory (with --recursive) to tag"),
    recursive: bool = typer.Option(
        False,
        "-r",
        "--recursive",
        help="If path is a directory, apply preset (+ auto-tags) to all files under it",
    ),
    no_auto: bool = typer.Option(False, "--no-auto", help="Skip extension-based auto-tagging"),
    no_aliases: bool = typer.Option(False, "--no-aliases", help="Skip alias resolution"),
):
    """Apply a preset's tags to a file"""
    preset_tags = get_preset(name)
    if preset_tags is None:
        typer.echo(f"Error: preset '{name}' not found.")
        raise typer.Exit(1)
    abs_target = os.path.abspath(os.path.join(os.getcwd(), file))
    if recursive:
        if not os.path.isdir(abs_target):
            typer.echo(
                f"Error: --recursive requires a directory; '{abs_target}' is not a directory."
            )
            raise typer.Exit(1)
        result = add_tags_recursive(
            file,
            list(preset_tags),
            apply_aliases=not no_aliases,
            auto_tag=not no_auto,
        )
        if not result.get("success"):
            raise typer.Exit(1)
        return
    add_tags(file, preset_tags, apply_aliases=not no_aliases, auto_tag=not no_auto)


@preset_app.command("delete")
def preset_delete(
    name: str = typer.Argument(..., help="Preset name to delete", autocompletion=_complete_preset_names),
):
    """Delete a saved preset"""
    if delete_preset(name):
        typer.echo(f"Preset '{name}' deleted.")
    else:
        typer.echo(f"Preset '{name}' not found.")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Export / Import tag data
# ---------------------------------------------------------------------------

@app.command("export")
def export_data(
    output: str = typer.Option(
        "tag_export.json",
        "--output", "-o",
        help="Destination file path (.json or .csv)",
    ),
    fmt: Optional[str] = typer.Option(
        None,
        "--format", "-f",
        help="Output format: json or csv (inferred from extension if omitted)",
    ),
):
    """Export all tag data to a JSON or CSV file"""
    ext = (fmt or os.path.splitext(output)[1].lstrip(".") or "json").lower()
    if ext == "csv":
        if not output.endswith(".csv"):
            output = os.path.splitext(output)[0] + ".csv"
        result = export_tags_csv(output)
    else:
        if not output.endswith(".json"):
            output = os.path.splitext(output)[0] + ".json"
        result = export_tags_json(output)
    typer.echo(result["message"])
    if not result["success"]:
        raise typer.Exit(1)


@app.command("import")
def import_data(
    input_file: str = typer.Argument(..., help="Import file (.json or .csv)"),
    replace: bool = typer.Option(
        False,
        "--replace",
        help="Replace the entire database instead of merging",
    ),
):
    """Import tag data from a JSON or CSV file (merges with existing data by default)"""
    result = import_tags(input_file, replace=replace)
    typer.echo(result["message"])
    if not result["success"]:
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Watch mode
# ---------------------------------------------------------------------------

_DEFAULT_IGNORE = ["*.pyc", "__pycache__", ".git", ".DS_Store", "*.swp", "*.tmp", "~*"]


@app.command("watch")
def watch(
    path: str = typer.Argument(
        ".",
        help="Directory to watch (default: current directory)",
    ),
    recursive: bool = typer.Option(
        True,
        "--recursive/--no-recursive", "-r",
        help="Watch subdirectories recursively",
    ),
    tags: Optional[List[str]] = typer.Option(
        None,
        "--tags", "-t",
        help="Always add these tags to every new file",
    ),
    preset: Optional[str] = typer.Option(
        None,
        "--preset",
        help="Apply a saved tag preset to every new file",
    ),
    no_auto: bool = typer.Option(
        False,
        "--no-auto",
        help="Disable extension-based auto-tagging",
    ),
    clean_on_delete: bool = typer.Option(
        False,
        "--clean-on-delete",
        help="Remove tag entry when a watched file is deleted",
    ),
    ignore: Optional[List[str]] = typer.Option(
        None,
        "--ignore", "-i",
        help="Glob patterns to ignore (e.g. '*.pyc'). Default ignores common noise.",
    ),
    plain: bool = typer.Option(
        False,
        "--plain",
        help="Plain line output instead of Rich live display",
    ),
):
    """Watch a directory and auto-tag files as they are created or moved"""
    ignore_patterns = list(ignore) if ignore else list(_DEFAULT_IGNORE)
    handle_watch_command(
        watch_path=path,
        recursive=recursive,
        extra_tags=list(tags) if tags else [],
        preset_name=preset,
        auto_tag=not no_auto,
        on_delete_clean=clean_on_delete,
        ignore_patterns=ignore_patterns,
        plain=plain,
    )


# ---------------------------------------------------------------------------
# Graph visualizer
# ---------------------------------------------------------------------------

@app.command("graph")
def graph(
    mode: str = typer.Option(
        "tag",
        "--mode", "-m",
        help="Graph mode: tag (co-occurrence), file (Jaccard similarity), mixed (bipartite)",
    ),
    three_d: bool = typer.Option(
        False,
        "--3d",
        help="Start in 3D mode (default: 2D; toggle available in the browser UI)",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output", "-o",
        help="Save the HTML to this path instead of a temp file",
    ),
    export_format: Optional[str] = typer.Option(
        None,
        "--export",
        help="Also export graph data: gexf | graphml",
    ),
    export_path: Optional[str] = typer.Option(
        None,
        "--export-path",
        help="Destination path for the exported graph file",
    ),
    min_weight: int = typer.Option(
        1,
        "--min-weight",
        help="Minimum edge weight (co-occurrences) to include",
        min=1,
    ),
    threshold: float = typer.Option(
        0.2,
        "--threshold",
        help="Jaccard similarity threshold for file mode (0–1)",
    ),
    no_open: bool = typer.Option(
        False,
        "--no-open",
        help="Generate HTML but do not open it in the browser",
    ),
    no_server: bool = typer.Option(
        False,
        "--no-server",
        help="Disable the local helper server (disables click-to-open-file)",
    ),
):
    """Visualize tag relationships as an interactive network graph (2D/3D)"""
    handle_graph_command(
        mode=mode,
        three_d=three_d,
        output=output,
        export_format=export_format,
        export_path=export_path,
        min_weight=min_weight,
        threshold=threshold,
        no_open=no_open,
        no_server=no_server,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the TagManager CLI."""
    app()


if __name__ == "__main__":
    main()
