import os
from typing import Dict, Optional, Tuple

from ..helpers import load_tags, save_tags


def move_path(old_path: str, new_path: str) -> Tuple[bool, str]:
    """
    Rename/move a file's entry in the tag database.

    Returns (success, message).
    Does NOT touch the actual file on disk — only updates the tag record.
    """
    old_path = os.path.normpath(os.path.abspath(old_path))
    new_path = os.path.normpath(os.path.abspath(new_path))

    if old_path == new_path:
        return False, "Source and destination are the same path."

    tags = load_tags()

    if old_path not in tags:
        return False, f"'{old_path}' is not tracked in TagManager."

    if new_path in tags:
        return False, f"'{new_path}' is already tracked. Remove it first if you want to overwrite."

    tags[new_path] = tags.pop(old_path)
    if not save_tags(tags):
        return False, "Failed to save tag database."

    return True, f"Moved tag record: '{old_path}' → '{new_path}'"


def clean_missing(dry_run: bool = False) -> Dict:
    """
    Remove tag entries for files that no longer exist on disk.

    Returns a result dict with lists of removed paths.
    """
    tags = load_tags()
    missing = [p for p in tags if not os.path.exists(p)]

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "missing": missing,
            "count": len(missing),
            "message": f"Would remove {len(missing)} missing path(s).",
        }

    for path in missing:
        del tags[path]

    if missing:
        save_tags(tags)

    return {
        "success": True,
        "dry_run": False,
        "missing": missing,
        "count": len(missing),
        "message": f"Removed {len(missing)} missing path(s).",
    }
