"""
Model Context Protocol (stdio) server for TagManager.

Exposes search/list/tag tools for Cursor and other MCP clients. Install the
optional dependency::

    pip install 'tagmanager-cli[mcp]'

Plugins (Python 3.10+): register callables via entry point group ``tagmanager.mcp``.
Each entry point must name a callable ``register(mcp)`` where ``mcp`` is the
``FastMCP`` instance (same pattern as ``@mcp.tool()`` in the plugin module).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger("tagmanager.mcp")


def _tags_for_path(file_path: str) -> List[str]:
    """Tags for ``file_path`` without printing to stdout (unlike ``path_tags``)."""
    from .app.helpers import load_tags

    fp = os.path.abspath(os.path.join(os.getcwd(), file_path))
    return list(load_tags().get(fp, []))


def _build_mcp():
    from mcp.server.fastmcp import FastMCP

    from .app.add.service import add_tags
    from .app.helpers import load_tags
    from .app.search.service import combined_search, search_files_by_tags
    from .app.tags.service import list_all_tags, search_files_by_tag

    mcp = FastMCP(
        "TagManager",
        instructions=(
            "Local file tagging: list tags, search files by tag(s), read or add "
            "tags on paths. Prefer dry_run=true for add_tags_to_file unless the "
            "user explicitly wants to persist."
        ),
    )

    @mcp.tool()
    def list_distinct_tags() -> List[str]:
        """Return all distinct tag names across the tag database."""
        return list_all_tags()

    @mcp.tool()
    def get_all_tag_assignments() -> Dict[str, List[str]]:
        """Return the full path -> tags map (can be large)."""
        return dict(load_tags())

    @mcp.tool()
    def get_tags_for_path(file_path: str) -> List[str]:
        """Return tags for a single file path (absolute or cwd-relative)."""
        return _tags_for_path(file_path)

    @mcp.tool()
    def search_files_by_tag_list(
        tags: List[str],
        match_all: bool = False,
        path_substring: Optional[str] = None,
        exclude_tags: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Search files by tag(s). OR semantics unless match_all=true (AND).
        Optional path_substring filters by file path; exclude_tags drops matches.
        """
        tags = [t.strip() for t in (tags or []) if t and str(t).strip()]
        ex = exclude_tags or None
        if path_substring and tags:
            return list(
                combined_search(tags, path_substring, match_all, exclude_tags=ex)
            )
        if tags:
            return list(
                search_files_by_tags(tags, match_all, False, exclude_tags=ex)
            )
        return []

    @mcp.tool()
    def search_files_by_single_tag(tag: str, exact: bool = False) -> List[str]:
        """Find files that have a given tag (substring match unless exact=true)."""
        return list(search_files_by_tag(tag.strip(), exact=exact))

    @mcp.tool()
    def add_tags_to_file(
        file_path: str,
        tags: List[str],
        dry_run: bool = True,
        apply_aliases: bool = True,
        auto_tag: bool = True,
        content_tag: bool = True,
    ) -> str:
        """
        Add tags to one file. Defaults to dry_run=true (preview only). Set
        dry_run=false to persist. Respects extension auto-tagging unless auto_tag=false.
        """
        ok = add_tags(
            file_path,
            list(tags),
            apply_aliases=apply_aliases,
            auto_tag=auto_tag,
            content_tag=content_tag,
            dry_run=dry_run,
        )
        payload = {"ok": ok, "dry_run": dry_run, "file_path": file_path, "tags": tags}
        return json.dumps(payload, ensure_ascii=False)

    _register_entry_point_plugins(mcp)
    return mcp


def _register_entry_point_plugins(mcp: Any) -> None:
    """Load ``tagmanager.mcp`` entry points; each callable is ``register(fastmcp)``."""
    try:
        import importlib.metadata as im
    except ImportError:
        return

    try:
        eps = im.entry_points()
        if hasattr(eps, "select"):
            hooks = eps.select(group="tagmanager.mcp")
        elif hasattr(eps, "get"):
            hooks = eps.get("tagmanager.mcp", [])
        else:
            hooks = ()
    except Exception as e:
        logger.debug("entry_points tagmanager.mcp: %s", e)
        return

    for ep in hooks:
        try:
            register = ep.load()
            if callable(register):
                register(mcp)
        except Exception as e:
            logger.warning("MCP plugin %r failed: %s", getattr(ep, "name", ep), e)


def run_stdio_server() -> None:
    try:
        mcp = _build_mcp()
    except ImportError as e:
        sys.stderr.write(
            "MCP SDK not installed. Use: pip install 'tagmanager-cli[mcp]'\n"
            f"Import error: {e}\n"
        )
        raise SystemExit(1) from e
    mcp.run(transport="stdio")


def main() -> None:
    """Console script entry: ``tm-mcp``."""
    run_stdio_server()


if __name__ == "__main__":
    main()
