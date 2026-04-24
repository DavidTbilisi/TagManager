from typing import Any, Dict, List

from ..helpers import load_tags, save_tags
import os


def remove_all_tags(file_path: str) -> dict:
    """
    Clear all tags from a file while keeping the file entry in the database.
    Returns a result dict so callers can give feedback without printing directly.

    Idempotent: unknown paths or paths that already have no tags succeed with a clear message.
    """
    path = os.path.normpath(os.path.abspath(file_path))
    tags = load_tags()

    if path not in tags:
        return {
            "success": True,
            "path": path,
            "cleared": [],
            "message": f"No tags to clear (path not in database): '{path}'",
        }

    previous = list(tags[path])
    if not previous:
        return {
            "success": True,
            "path": path,
            "cleared": [],
            "message": f"No tags on file (already empty): '{path}'",
        }

    tags[path] = []
    save_tags(tags)
    return {
        "success": True,
        "path": path,
        "cleared": previous,
        "message": f"Cleared {len(previous)} tag(s) from '{path}'",
    }


def remove_tag_from_file(file_path: str, tag: str) -> Dict[str, Any]:
    """Remove a single tag from one file (case-insensitive tag match)."""
    path = os.path.normpath(os.path.abspath(file_path))
    needle = str(tag).strip()
    if not needle:
        return {"success": False, "path": path, "message": "Tag name is empty"}

    data = load_tags()
    if path not in data:
        return {"success": False, "path": path, "message": f"'{path}' not found in TagManager"}

    before = list(data[path])
    new_tags = [t for t in before if t.lower() != needle.lower()]
    if len(new_tags) == len(before):
        return {
            "success": False,
            "path": path,
            "message": f"Tag {needle!r} not present on file",
        }

    data[path] = new_tags
    if not save_tags(data):
        return {"success": False, "path": path, "message": "Failed to save tags"}

    return {
        "success": True,
        "path": path,
        "tags": new_tags,
        "message": f"Removed tag {needle!r} from '{path}'",
    }


def remove_path(file_path: str) -> Dict[str, Any]:
    """
    Remove a file path from the tags file.

    :return: ``success``, ``message``, ``path``, and ``removed_tags`` when removed.
    """
    path = os.path.normpath(os.path.abspath(file_path))
    tags = load_tags()
    popped_tags = tags.pop(path, None)
    if popped_tags is None:
        return {
            "success": False,
            "path": path,
            "removed_tags": None,
            "message": f"Could not find {path} in TagManager",
        }
    save_tags(tags)
    return {
        "success": True,
        "path": path,
        "removed_tags": popped_tags,
        "message": f"Removed {path} from TagManager",
    }


def remove_invalid_paths() -> Dict[str, Any]:
    """
    Remove paths from the tag DB that do not exist on disk.

    :return: ``success``, ``message``, ``removed_paths``, ``count``.
    """
    to_remove: List[str] = []
    tags = load_tags()
    for file_path in list(tags.keys()):
        if not os.path.exists(file_path):
            to_remove.append(file_path)
            tags.pop(file_path, None)

    if len(to_remove) == 0:
        return {
            "success": True,
            "message": "No invalid paths found",
            "removed_paths": [],
            "count": 0,
        }

    save_tags(tags)
    return {
        "success": True,
        "message": f"Removed {len(to_remove)} invalid path(s) from TagManager",
        "removed_paths": to_remove,
        "count": len(to_remove),
    }
