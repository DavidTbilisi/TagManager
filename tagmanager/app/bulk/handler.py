from typing import List
import typer

from tagmanager import runtime

from .service import (
    bulk_add_tags,
    bulk_remove_by_tag,
    bulk_retag,
    bulk_remove_tag_from_files,
)


def _emit_bulk_result(result: dict) -> None:
    """Human table or machine JSON depending on global ``--json`` / ``TM_JSON``."""
    if runtime.json_mode():
        runtime.emit_json(result)
    else:
        typer.echo(format_bulk_result(result))


def format_bulk_result(result: dict) -> str:
    """Format bulk operation results for display."""
    output = []

    if result["dry_run"]:
        output.append("🔍 DRY RUN - No changes made")
        output.append("")

    if result["success"]:
        output.append(f"✅ {result['message']}")

        if result["files_found"]:
            output.append("")
            output.append("📁 Files affected:")
            for i, file_path in enumerate(result["files_found"][:10], 1):
                # Show just filename for readability
                import os

                filename = os.path.basename(file_path)
                output.append(f"   {i}. {filename}")

            if len(result["files_found"]) > 10:
                output.append(
                    f"   ... and {len(result['files_found']) - 10} more files"
                )
    else:
        output.append(f"❌ {result['message']}")

    return "\n".join(output)


def handle_bulk_add(
    pattern: str, tags: List[str], base_path: str = ".", dry_run: bool = False
):
    """Handle bulk add command."""
    if not tags:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "success": False,
                    "message": "No tags provided. Use --tags to specify tags to add.",
                    "files_found": [],
                    "dry_run": dry_run,
                }
            )
        else:
            typer.echo("❌ No tags provided. Use --tags to specify tags to add.")
        return

    if not pattern:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "success": False,
                    "message": "No pattern provided. Specify a glob like '*.py' or '**/*.txt'.",
                    "files_found": [],
                    "dry_run": dry_run,
                }
            )
        else:
            typer.echo(
                "❌ No pattern provided. Specify a file pattern like '*.py' or '**/*.txt'."
            )
        return

    result = bulk_add_tags(pattern, tags, base_path, dry_run)
    _emit_bulk_result(result)


def handle_bulk_remove(tag: str = None, remove_tag: str = None, dry_run: bool = False):
    """Handle bulk remove command."""
    if tag:
        # Remove files with this tag
        result = bulk_remove_by_tag(tag, dry_run)
        _emit_bulk_result(result)
    elif remove_tag:
        # Remove tag from all files
        result = bulk_remove_tag_from_files(remove_tag, dry_run)
        _emit_bulk_result(result)
    else:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "success": False,
                    "message": "Specify either --tag (remove files with tag) or --remove-tag (strip tag from all files).",
                    "files_found": [],
                    "dry_run": dry_run,
                }
            )
        else:
            typer.echo(
                "❌ Specify either --tag (to remove files) or --remove-tag (to remove tag from files)."
            )
            typer.echo("Examples:")
            typer.echo(
                "  tm bulk remove --tag deprecated        # Remove all files with 'deprecated' tag"
            )
            typer.echo(
                "  tm bulk remove --remove-tag old        # Remove 'old' tag from all files"
            )


def handle_bulk_retag(from_tag: str, to_tag: str, dry_run: bool = False):
    """Handle bulk retag command."""
    if not from_tag or not to_tag:
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "success": False,
                    "message": "Both --from and --to tags are required.",
                    "files_found": [],
                    "dry_run": dry_run,
                }
            )
        else:
            typer.echo("❌ Both --from and --to tags are required.")
            typer.echo("Example: tm bulk retag --from old-name --to new-name")
        return

    if from_tag.lower() == to_tag.lower():
        if runtime.json_mode():
            runtime.emit_json(
                {
                    "success": False,
                    "message": "Source and destination tags cannot be the same.",
                    "files_found": [],
                    "dry_run": dry_run,
                }
            )
        else:
            typer.echo("❌ Source and destination tags cannot be the same.")
        return

    result = bulk_retag(from_tag, to_tag, dry_run)
    _emit_bulk_result(result)
