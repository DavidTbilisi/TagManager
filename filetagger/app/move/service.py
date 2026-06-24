import os
from typing import Dict, Optional, Tuple

from ..helpers import load_tags, save_tags
from ..journal.service import append_entry


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
        return False, f"'{old_path}' is not tracked in FileTagger."

    if new_path in tags:
        return False, f"'{new_path}' is already tracked. Remove it first if you want to overwrite."

    old_tags = list(tags[old_path])
    tags[new_path] = tags.pop(old_path)
    if not save_tags(tags):
        return False, "Failed to save tag database."

    # Undo restores the old path and drops the new entry (which was not tracked
    # before — we returned early above if new_path already existed).
    append_entry("move_path", {"paths": {old_path: old_tags, new_path: None}})
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

    removed_map = {p: list(tags[p]) for p in missing}
    for path in missing:
        del tags[path]

    if missing:
        save_tags(tags)
        append_entry("clean_missing", {"paths": removed_map})

    return {
        "success": True,
        "dry_run": False,
        "missing": missing,
        "count": len(missing),
        "message": f"Removed {len(missing)} missing path(s).",
    }
