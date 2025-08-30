import sys
from typing import List, Optional

import typer

from app.add.service import add_tags
from app.list_all.service import print_list_tags_all_table
from app.paths.service import path_tags, fuzzy_search_path
from app.remove.service import remove_path, remove_invalid_paths
from app.search.service import combined_search, search_files_by_path, search_files_by_tags
from app.stats.handler import handle_stats_command
from app.storage.service import show_storage_location, open_storage_location
from app.tags.service import list_all_tags, search_files_by_tag, open_list_files_by_tag_result


sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

app = typer.Typer(
    name="tm",
    help="Tag Manager - File Tagging System",
    no_args_is_help=True
)


@app.command()
def add(
    file: str = typer.Argument(..., help="Path to the file"),
    tags: List[str] = typer.Option(..., "-t", "--tags", help="Tags to add")
):
    """Add tags to a file"""
    add_tags(file, tags)


@app.command()
def remove(
    path: Optional[str] = typer.Option(None, "-p", "--path", help="Path to the file"),
    invalid: bool = typer.Option(False, "-i", "--invalid", help="Remove invalid paths from tags")
):
    """Remove path from tags"""
    if path:
        remove_path(path)
    elif invalid:
        remove_invalid_paths()
    else:
        typer.echo("No arguments provided")


@app.command("ls")
def list_all(
    all: Optional[str] = typer.Option(None, "--all", help="Not implemented"),
    ext: Optional[str] = typer.Option(None, "--ext", help="Not implemented")
):
    """List files and tags in a table"""
    print_list_tags_all_table()


@app.command()
def path(
    filepath: str = typer.Argument(..., help="Path to the file"),
    fuzzy: bool = typer.Option(False, "-f", "--fuzzy", help="Type of search to use"),
    folder: bool = typer.Option(False, "-F", "--folder", help="Search for a folder instead of a file"),
    exact: bool = typer.Option(False, "-e", "--exact", help="Exact match for file path")
):
    """List tags of a file"""
    if fuzzy:
        print(fuzzy_search_path(filepath))
    else:
        print(path_tags(filepath))


@app.command()
def tags(
    search: Optional[str] = typer.Option(None, "-s", "--search", help="List files by a specific tag"),
    open: bool = typer.Option(False, "-o", "--open", help="Open the file"),
    exact: bool = typer.Option(False, "-e", "--exact", help="Exact match for tag"),
    where: bool = typer.Option(False, "-w", "--where", help="Display the path of the file")
):
    """List all tags"""
    if search and open:
        open_list_files_by_tag_result(
            search_files_by_tag(search, exact)
        )
    elif search:
        result = search_files_by_tag(search, exact)
        for i, file in enumerate(result, start=1):
            print(f"{i}. {file}")
    else:
        for i, tag in enumerate(list_all_tags(), start=1):
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
    tags: Optional[List[str]] = typer.Option(None, "-t", "--tags", help="List of tags to search for"),
    path: Optional[str] = typer.Option(None, "-p", "--path", help="Path query to search for"),
    match_all: bool = typer.Option(False, "-a", "--match_all", help="Match all specified tags (AND operation)"),
    exact: bool = typer.Option(False, "-e", "--exact", help="Exact match for tags"),
    open: bool = typer.Option(False, "-o", "--open", help="Open the file")
):
    """Search files by tags or path"""
    if tags and path:
        # Combined search by tags and path
        result = combined_search(tags, path, match_all)
    elif tags:
        # Search by tags only
        result = search_files_by_tags(tags, match_all, exact)
    elif path:
        # Search by path only
        result = search_files_by_path(path)
    else:
        typer.echo("No search criteria provided.")
        typer.echo("Example: tm search -t python -p C:\\Users\\User\\Documents")
        typer.echo("Example: tm search -t python -t linux")
        typer.echo("Example: tm search -p C:\\Users\\User\\Documents")
        typer.echo("Example: tm search -p C:\\Users\\User\\Documents -p C:\\Users\\User\\Downloads")
        return

    if result:
        for i, file in enumerate(result, start=1):
            print(f"{i}. {file}")
        print()
    else:
        print("No files found matching the criteria.")


@app.command()
def stats(
    tag: Optional[str] = typer.Option(None, "--tag", help="Show statistics for a specific tag"),
    file_count: bool = typer.Option(False, "--file-count", help="Show files per tag distribution")
):
    """Show tag statistics and analytics"""
    handle_stats_command(tag=tag, file_count=file_count)


if __name__ == "__main__":
    app()