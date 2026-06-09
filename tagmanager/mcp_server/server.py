"""
TagManager MCP Server
Exposes tag management as MCP tools for Claude and other AI clients.
Run with: py -m tagmanager.mcp_server
"""
import asyncio
import json
import os
import sys
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Import TagManager services directly (no subprocess overhead)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from tagmanager.app.add.service import add_tags as _add_tags
from tagmanager.app.remove.service import remove_all_tags as _remove_all_tags
from tagmanager.app.search.service import search_files_by_tags, combined_search
from tagmanager.app.helpers import load_tags, save_tags
from tagmanager.app.stats.service import get_overall_statistics

server = Server("tagmanager")

# ── tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    types.Tool(
        name="tm_add_tags",
        description=(
            "Add one or more tags to a file. Creates the file entry if it doesn't exist. "
            "Tags are case-insensitive and stored lowercase."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the file to tag",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tags to add (e.g. ['python', 'script', 'automation'])",
                },
            },
            "required": ["file_path", "tags"],
        },
    ),
    types.Tool(
        name="tm_remove_tags",
        description="Remove specific tags from a file. Other tags are preserved.",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to remove",
                },
            },
            "required": ["file_path", "tags"],
        },
    ),
    types.Tool(
        name="tm_remove_all_tags",
        description="Remove ALL tags from a file, leaving it untagged.",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file"},
            },
            "required": ["file_path"],
        },
    ),
    types.Tool(
        name="tm_get_tags",
        description="Get all tags currently assigned to a specific file.",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Absolute path to the file"},
            },
            "required": ["file_path"],
        },
    ),
    types.Tool(
        name="tm_search",
        description=(
            "Search for files by tags. Supports AND (match_all=true), OR (default), "
            "and NOT (exclude_tags). Returns matching file paths."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to search for",
                },
                "match_all": {
                    "type": "boolean",
                    "description": "If true, file must have ALL tags (AND). Default false (OR).",
                    "default": False,
                },
                "exclude_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exclude files that have any of these tags (NOT filter)",
                },
                "path_query": {
                    "type": "string",
                    "description": "Optional substring to filter file paths",
                },
            },
            "required": ["tags"],
        },
    ),
    types.Tool(
        name="tm_list_all",
        description=(
            "List all tagged files with their tags. Optionally filter by a path substring. "
            "Returns a JSON object mapping file paths to tag lists."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "path_filter": {
                    "type": "string",
                    "description": "Optional substring to filter file paths (case-insensitive)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max files to return (default 100)",
                    "default": 100,
                },
            },
        },
    ),
    types.Tool(
        name="tm_stats",
        description=(
            "Get tag statistics: total files, total tags, most-used tags, "
            "files with most tags, and untagged file count."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    types.Tool(
        name="tm_tag_directory",
        description=(
            "Add tags to ALL files in a directory (non-recursive by default). "
            "Useful for bulk-tagging a folder of documents."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Absolute path to the directory"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to apply to every file in the directory",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Also tag files in subdirectories",
                    "default": False,
                },
                "extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Only tag files with these extensions e.g. ['pdf','docx']",
                },
            },
            "required": ["directory", "tags"],
        },
    ),
]


# ── tool handlers ─────────────────────────────────────────────────────────────

def _ok(data: Any) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]


def _err(msg: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=json.dumps({"error": msg}, ensure_ascii=False))]


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "tm_add_tags":
            success = _add_tags(arguments["file_path"], arguments["tags"])
            tags_now = load_tags().get(os.path.normpath(os.path.abspath(arguments["file_path"])), [])
            return _ok({"success": success, "file": arguments["file_path"], "tags": tags_now})

        elif name == "tm_remove_tags":
            path = os.path.normpath(os.path.abspath(arguments["file_path"]))
            tags_to_remove = [t.lower() for t in arguments["tags"]]
            data = load_tags()
            if path not in data:
                return _err(f"File not found in TagManager: {path}")
            before = data[path]
            data[path] = [t for t in before if t.lower() not in tags_to_remove]
            save_tags(data)
            return _ok({"success": True, "file": path, "removed": tags_to_remove, "tags": data[path]})

        elif name == "tm_remove_all_tags":
            result = _remove_all_tags(arguments["file_path"])
            return _ok(result)

        elif name == "tm_get_tags":
            path = os.path.normpath(os.path.abspath(arguments["file_path"]))
            data = load_tags()
            tags = data.get(path, [])
            return _ok({"file": path, "tags": tags, "count": len(tags)})

        elif name == "tm_search":
            tags = arguments["tags"]
            match_all = arguments.get("match_all", False)
            exclude = arguments.get("exclude_tags", [])
            path_q = arguments.get("path_query", "").lower()
            fuzzy_threshold = 0.6

            # Search directly on raw data to always return full paths
            data = load_tags()
            from tagmanager.app.helpers import normalized_levenshtein_distance
            matched: set = set()
            for path, file_tags in data.items():
                def _matches(tag, ft):
                    tl, ftl = tag.lower(), ft.lower()
                    return tl in ftl or normalized_levenshtein_distance(tl, ftl) >= fuzzy_threshold

                if match_all:
                    hit = all(any(_matches(t, ft) for ft in file_tags) for t in tags)
                else:
                    hit = any(any(_matches(t, ft) for ft in file_tags) for t in tags)
                if hit:
                    matched.add(path)

            if exclude:
                matched = {
                    p for p in matched
                    if not any(e.lower() in ft.lower() for e in exclude for ft in data[p])
                }
            if path_q:
                matched = {p for p in matched if path_q in p.lower()}

            return _ok({"count": len(matched), "files": sorted(matched)})

        elif name == "tm_list_all":
            data = load_tags()
            path_filter = arguments.get("path_filter", "").lower()
            limit = int(arguments.get("limit", 100))

            filtered = {
                path: tags
                for path, tags in data.items()
                if not path_filter or path_filter in path.lower()
            }
            items = sorted(filtered.items())[:limit]
            return _ok({"total": len(filtered), "returned": len(items), "files": dict(items)})

        elif name == "tm_stats":
            from collections import Counter
            data = load_tags()
            tag_counter: Counter = Counter()
            file_tag_counts = {}
            for path, tags in data.items():
                tag_counter.update(tags)
                file_tag_counts[path] = len(tags)

            return _ok({
                "total_files": len(data),
                "total_unique_tags": len(tag_counter),
                "untagged_files": sum(1 for t in data.values() if not t),
                "top_tags": [{"tag": t, "count": c} for t, c in tag_counter.most_common(20)],
                "most_tagged_files": [
                    {"file": f, "tag_count": c}
                    for f, c in sorted(file_tag_counts.items(), key=lambda x: -x[1])[:10]
                ],
            })

        elif name == "tm_tag_directory":
            directory = arguments["directory"]
            tags = arguments["tags"]
            recursive = arguments.get("recursive", False)
            extensions = [e.lower().lstrip(".") for e in arguments.get("extensions", [])]

            if not os.path.isdir(directory):
                return _err(f"Not a directory: {directory}")

            walker = os.walk(directory) if recursive else [(directory, [], os.listdir(directory))]
            tagged, skipped = [], []
            for root, _, files in walker:
                for fname in files:
                    if fname.startswith("."):
                        continue
                    ext = os.path.splitext(fname)[1].lstrip(".").lower()
                    if extensions and ext not in extensions:
                        continue
                    full = os.path.join(root, fname)
                    if os.path.isfile(full):
                        _add_tags(full, tags)
                        tagged.append(full)

            return _ok({
                "tagged": len(tagged),
                "files": tagged,
                "tags_applied": tags,
            })

        else:
            return _err(f"Unknown tool: {name}")

    except Exception as exc:
        return _err(f"{type(exc).__name__}: {exc}")


# ── entrypoint ────────────────────────────────────────────────────────────────

async def _run():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    asyncio.run(_run())


if __name__ == "__main__":
    main()
