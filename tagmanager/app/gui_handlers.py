"""Shared handlers for the thin local GUI (used by :mod:`tagmanager.app.http_api`)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from .add.service import add_tags
from .helpers import load_tags, save_tags
from .remove.service import remove_all_tags, remove_path


def gui_allowed_root() -> Optional[str]:
    r = os.environ.get("TAGMANAGER_GUI_ROOT", "").strip()
    if not r:
        return None
    return os.path.normpath(os.path.abspath(r))


def normalize_gui_path(path: str) -> str:
    return os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), path.strip())))


def path_allowed(path_abs: str, allowed_root: Optional[str]) -> Tuple[bool, str]:
    if not allowed_root:
        return True, ""
    root = os.path.normpath(os.path.abspath(allowed_root))
    if path_abs == root or path_abs.startswith(root + os.sep):
        return True, ""
    return False, f"path outside allowed root ({root})"


def get_path_tags(path: str) -> Dict[str, Any]:
    allowed = gui_allowed_root()
    abs_path = normalize_gui_path(path)
    ok, msg = path_allowed(abs_path, allowed)
    if not ok:
        return {"ok": False, "error": msg, "path": abs_path, "tags": []}
    tags = list(load_tags().get(abs_path, []))
    return {"ok": True, "path": abs_path, "tags": tags}


def post_add_tags(
    path: str,
    tags: List[str],
    dry_run: bool = False,
    no_auto: bool = False,
    no_aliases: bool = False,
    no_content: bool = False,
) -> Dict[str, Any]:
    allowed = gui_allowed_root()
    abs_path = normalize_gui_path(path)
    ok, msg = path_allowed(abs_path, allowed)
    if not ok:
        return {"ok": False, "error": msg}
    if not os.path.isfile(abs_path):
        return {"ok": False, "error": "not a file or does not exist"}
    flat = [t.strip() for t in tags if t and str(t).strip()]
    success = add_tags(
        abs_path,
        flat,
        apply_aliases=not no_aliases,
        auto_tag=not no_auto,
        content_tag=not no_content,
        dry_run=dry_run,
    )
    if not success:
        return {"ok": False, "error": "add_tags failed (see server stderr or invalid input)"}
    after = list(load_tags().get(abs_path, []))
    return {"ok": True, "dry_run": dry_run, "path": abs_path, "tags": after}


def post_remove(
    path: str,
    mode: str,
    tag: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    ``mode``: ``path`` (drop DB entry), ``clear_tags`` (empty tag list), ``one_tag`` (strip ``tag``).
    """
    allowed = gui_allowed_root()
    abs_path = normalize_gui_path(path)
    ok, msg = path_allowed(abs_path, allowed)
    if not ok:
        return {"ok": False, "error": msg}

    if mode == "path":
        if dry_run:
            return {"ok": True, "dry_run": True, "message": f"would remove path from DB: {abs_path}"}
        r = remove_path(abs_path)
        return {"ok": r.get("success", False), "message": r.get("message", ""), "path": abs_path}

    if mode == "clear_tags":
        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "message": f"would clear all tags on: {abs_path}",
            }
        r = remove_all_tags(abs_path)
        return {"ok": r.get("success", False), "message": r.get("message", ""), "path": abs_path}

    if mode == "one_tag":
        if not tag or not str(tag).strip():
            return {"ok": False, "error": "tag required for one_tag mode"}
        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "message": f"would remove tag {tag!r} from {abs_path}",
            }
        data = load_tags()
        if abs_path not in data:
            return {"ok": False, "error": "path not in tag database"}
        before = list(data[abs_path])
        new_tags = [t for t in before if t.lower() != str(tag).strip().lower()]
        if len(new_tags) == len(before):
            return {"ok": False, "error": "tag not present on file"}
        data[abs_path] = new_tags
        if not save_tags(data):
            return {"ok": False, "error": "save failed"}
        return {"ok": True, "path": abs_path, "tags": new_tags}

    return {"ok": False, "error": f"unknown mode: {mode}"}
