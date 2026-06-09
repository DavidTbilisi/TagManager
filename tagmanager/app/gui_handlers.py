"""Shared handlers for the local web GUI (used by :mod:`tagmanager.app.http_api`).

Wraps service-layer functions in JSON-shaped responses, with a single safety
gate (``TAGMANAGER_GUI_ROOT``) that restricts path-touching operations to
a subtree if the user opts in.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from .add.service import add_tags
from .helpers import load_tags, save_tags
from .remove.service import remove_all_tags, remove_path as _remove_path


def gui_allowed_root() -> Optional[str]:
    """If ``TAGMANAGER_GUI_ROOT`` is set, restrict GUI to paths under it."""
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


def _compute_add_preview(
    abs_path: str,
    new_tags: List[str],
    apply_aliases: bool,
    auto_tag: bool,
) -> Optional[Tuple[List[str], List[str]]]:
    """Simulate add_tags() without writing. Returns (merged, before) or None.

    Mirrors the side-effect-free part of :func:`add.service.add_tags` so the
    preview page can render before/after chips.
    """
    flat = [t.strip() for t in (new_tags or []) if t and str(t).strip()]

    # Extension-based auto-tag rules (same call order as add_tags()).
    if auto_tag:
        try:
            from .autotag.service import suggest_tags_for_file
            for t in suggest_tags_for_file(abs_path):
                if t not in flat:
                    flat.append(t)
        except Exception:
            pass

    # Alias resolution.
    if apply_aliases:
        try:
            from .alias.service import apply_aliases as _resolve
            flat = _resolve(flat)
        except Exception:
            pass

    if not flat:
        return None

    before = list(load_tags().get(abs_path, []) or [])
    merged = list(before)
    for t in flat:
        if t not in merged:
            merged.append(t)
    return merged, before


def post_add_tags(
    path: str,
    tags: List[str],
    dry_run: bool = False,
    no_auto: bool = False,
    no_aliases: bool = False,
    no_content: bool = False,  # accepted for HTML compatibility; not used
) -> Dict[str, Any]:
    """Add tags to a file (or preview the merge when ``dry_run`` is set)."""
    del no_content  # current pipeline has no content-rule stage
    allowed = gui_allowed_root()
    abs_path = normalize_gui_path(path)
    ok, msg = path_allowed(abs_path, allowed)
    if not ok:
        return {"ok": False, "error": msg}
    if not os.path.isfile(abs_path):
        return {"ok": False, "error": "not a file or does not exist"}

    flat = [str(t).strip() for t in tags if str(t).strip()]

    if dry_run:
        comp = _compute_add_preview(
            abs_path, flat,
            apply_aliases=not no_aliases,
            auto_tag=not no_auto,
        )
        if comp is None:
            return {
                "ok": False,
                "error": "nothing to merge (no tags after auto-tag/alias rules)",
            }
        merged, before = comp
        return {
            "ok": True,
            "dry_run": True,
            "path": abs_path,
            "tags_before": before,
            "tags_after_preview": merged,
            "tags": merged,
        }

    if not flat and no_auto:
        return {"ok": False, "error": "no tags provided"}

    success = add_tags(
        abs_path,
        flat or [""],
        apply_aliases=not no_aliases,
        auto_tag=not no_auto,
    )
    if not success:
        return {"ok": False, "error": "add_tags failed (see server stderr or invalid input)"}
    after = list(load_tags().get(abs_path, []))
    return {"ok": True, "dry_run": False, "path": abs_path, "tags": after}


def post_remove(
    path: str,
    mode: str,
    tag: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Remove tags or paths.

    ``mode``:
      * ``path``       — drop the DB entry entirely
      * ``clear_tags`` — empty the tag list, keep the entry
      * ``one_tag``    — strip ``tag`` from the file's tag list
    """
    allowed = gui_allowed_root()
    abs_path = normalize_gui_path(path)
    ok, msg = path_allowed(abs_path, allowed)
    if not ok:
        return {"ok": False, "error": msg}

    if mode == "path":
        if dry_run:
            return {"ok": True, "dry_run": True,
                    "message": f"would remove path from DB: {abs_path}"}
        # remove_path() in the current code prints + returns None; check the
        # store before/after to give the GUI a real success/failure signal.
        before = load_tags()
        if abs_path not in before:
            return {"ok": False, "error": "path not in tag database", "path": abs_path}
        _remove_path(abs_path)
        return {"ok": True, "message": f"removed {abs_path}", "path": abs_path}

    if mode == "clear_tags":
        if dry_run:
            return {"ok": True, "dry_run": True,
                    "message": f"would clear all tags on: {abs_path}"}
        r = remove_all_tags(abs_path)
        return {"ok": r.get("success", False),
                "message": r.get("message", ""), "path": abs_path}

    if mode == "one_tag":
        if not tag or not str(tag).strip():
            return {"ok": False, "error": "tag required for one_tag mode"}
        if dry_run:
            return {"ok": True, "dry_run": True,
                    "message": f"would remove tag {tag!r} from {abs_path}"}
        data = load_tags()
        if abs_path not in data:
            return {"ok": False, "error": "path not in tag database"}
        before = list(data[abs_path])
        target = str(tag).strip().lower()
        new_tags = [t for t in before if t.lower() != target]
        if len(new_tags) == len(before):
            return {"ok": False, "error": "tag not present on file"}
        data[abs_path] = new_tags
        if not save_tags(data):
            return {"ok": False, "error": "save failed"}
        return {"ok": True, "path": abs_path, "tags": new_tags}

    return {"ok": False, "error": f"unknown mode: {mode}"}


# ---------------------------------------------------------------------------
# Read-only inventory helpers — used by the GUI's archive / autocomplete / stats
# ---------------------------------------------------------------------------


def get_all_tags_with_counts() -> Dict[str, Any]:
    """Return every distinct tag with its usage count."""
    counts: Dict[str, int] = {}
    try:
        store = load_tags() or {}
    except Exception:
        store = {}
    for tags in store.values():
        if not isinstance(tags, list):
            continue
        for t in tags:
            if isinstance(t, str) and t.strip():
                counts[t] = counts.get(t, 0) + 1
    items = [{"tag": t, "count": c}
             for t, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))]
    return {
        "ok": True,
        "tags": items,
        "unique": len(items),
        "total_files": len(store),
    }


def get_stats() -> Dict[str, Any]:
    """Wrap stats.service.get_overall_statistics into a {ok, …} envelope."""
    try:
        from .stats.service import get_overall_statistics
        stats = get_overall_statistics() or {}
        return {"ok": True, **stats}
    except Exception as exc:
        return {"ok": False, "error": f"stats unavailable: {exc}"}


# ---------------------------------------------------------------------------
# Aliases — read + add/delete
# ---------------------------------------------------------------------------


def get_aliases_handler() -> Dict[str, Any]:
    try:
        from .alias.service import get_aliases
        return {"ok": True, "aliases": dict(get_aliases() or {})}
    except Exception as exc:
        return {"ok": False, "error": f"aliases unavailable: {exc}"}


def set_alias_handler(alias: str, canonical: str) -> Dict[str, Any]:
    alias = (alias or "").strip()
    canonical = (canonical or "").strip()
    if not alias or not canonical:
        return {"ok": False, "error": "alias and canonical required"}
    try:
        from .alias.service import add_alias
        if not add_alias(alias, canonical):
            return {"ok": False, "error": "alias == canonical or invalid"}
        return {"ok": True, "alias": alias.lower(), "canonical": canonical.lower()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def delete_alias_handler(alias: str) -> Dict[str, Any]:
    alias = (alias or "").strip()
    if not alias:
        return {"ok": False, "error": "alias required"}
    try:
        from .alias.service import remove_alias
        if not remove_alias(alias):
            return {"ok": False, "error": "alias not found"}
        return {"ok": True, "alias": alias.lower()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Presets — read + add/delete
# ---------------------------------------------------------------------------


def get_presets_handler() -> Dict[str, Any]:
    try:
        from .preset.service import get_presets
        return {"ok": True, "presets": dict(get_presets() or {})}
    except Exception as exc:
        return {"ok": False, "error": f"presets unavailable: {exc}"}


def set_preset_handler(name: str, tags: List[str]) -> Dict[str, Any]:
    name = (name or "").strip()
    clean = [str(t).strip() for t in (tags or []) if str(t).strip()]
    if not name or not clean:
        return {"ok": False, "error": "name and at least one tag required"}
    try:
        from .preset.service import save_preset
        if not save_preset(name, clean):
            return {"ok": False, "error": "save_preset rejected input"}
        return {"ok": True, "name": name.lower(), "tags": clean}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def delete_preset_handler(name: str) -> Dict[str, Any]:
    name = (name or "").strip()
    if not name:
        return {"ok": False, "error": "name required"}
    try:
        from .preset.service import delete_preset
        if not delete_preset(name):
            return {"ok": False, "error": "preset not found"}
        return {"ok": True, "name": name.lower()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Bulk — preview + apply (wraps bulk.service)
# ---------------------------------------------------------------------------


def _filter_to_allowed_root(paths: List[str]) -> List[str]:
    """If TAGMANAGER_GUI_ROOT is set, drop anything outside the allowed tree."""
    root = gui_allowed_root()
    if not root:
        return list(paths)
    return [
        p for p in paths
        if os.path.normpath(os.path.abspath(p)) == root
        or os.path.normpath(os.path.abspath(p)).startswith(root + os.sep)
    ]


def bulk_preview_handler(pattern: str, tags: List[str], base_path: str = ".") -> Dict[str, Any]:
    pattern = (pattern or "").strip() or "**/*"
    clean = [str(t).strip() for t in (tags or []) if str(t).strip()]
    if not clean:
        return {"ok": False, "error": "at least one tag required"}
    try:
        from .bulk.service import find_files_by_pattern
        files = find_files_by_pattern(pattern, (base_path or ".").strip() or ".")
        files = _filter_to_allowed_root(files)
        return {
            "ok": True,
            "dry_run": True,
            "pattern": pattern,
            "tags": clean,
            "files": files,
            "count": len(files),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Open file / containing folder via the OS shell
# ---------------------------------------------------------------------------


def open_path_handler(path: str, mode: str = "file") -> Dict[str, Any]:
    """Launch a file in its default app, or open its containing folder.

    Honours ``TAGMANAGER_GUI_ROOT`` when set — paths outside the allowed
    subtree are refused.  ``mode`` is ``file`` (default) or ``folder``.
    On Windows the folder mode uses ``explorer /select,<path>`` so the
    record is highlighted inside its folder.
    """
    import subprocess
    import sys

    if not path or not str(path).strip():
        return {"ok": False, "error": "path required"}

    abs_path = normalize_gui_path(str(path))
    allowed = gui_allowed_root()
    ok, msg = path_allowed(abs_path, allowed)
    if not ok:
        return {"ok": False, "error": msg, "path": abs_path}

    if not os.path.exists(abs_path):
        return {"ok": False, "error": "path does not exist on disk", "path": abs_path}

    mode = (mode or "file").strip().lower()
    if mode not in ("file", "folder"):
        return {"ok": False, "error": f"unknown mode: {mode}"}

    try:
        if sys.platform.startswith("win"):
            if mode == "folder":
                # /select highlights the file inside its parent folder.
                subprocess.Popen(["explorer", f"/select,{abs_path}"])
            else:
                # os.startfile is the right call for default-app launch on Win.
                os.startfile(abs_path)  # noqa: S606 (intentional)
        elif sys.platform == "darwin":
            if mode == "folder":
                subprocess.Popen(["open", "-R", abs_path])
            else:
                subprocess.Popen(["open", abs_path])
        else:
            target = os.path.dirname(abs_path) if mode == "folder" else abs_path
            subprocess.Popen(["xdg-open", target])
    except Exception as exc:
        return {"ok": False, "error": f"launch failed: {exc}", "path": abs_path}

    return {
        "ok": True,
        "mode": mode,
        "path": abs_path,
        "message": f"opened {'folder of' if mode == 'folder' else ''} {abs_path}".strip(),
    }


# ---------------------------------------------------------------------------
# Per-tag statistics (drives the GUI's tag-detail drawer)
# ---------------------------------------------------------------------------


def get_tag_stats_handler(tag: str) -> Dict[str, Any]:
    """Return rich stats for a single tag — files, co-occurrences, file types."""
    tag = (tag or "").strip()
    if not tag:
        return {"ok": False, "error": "tag required"}
    try:
        from .stats.service import get_tag_statistics
        info = get_tag_statistics(tag) or {}
        return {"ok": True, **info}
    except Exception as exc:
        return {"ok": False, "error": f"tag stats unavailable: {exc}"}


# ---------------------------------------------------------------------------
# Filter dashboards — wrap filter.service functions in {ok: …} envelopes
# ---------------------------------------------------------------------------


def filter_duplicates_handler() -> Dict[str, Any]:
    try:
        from .filter.service import find_duplicate_tags
        res = find_duplicate_tags() or {}
        # Tuple keys (sorted tag tuples) won't survive JSON — convert to lists.
        dupes = res.get("duplicates", {}) or {}
        out_groups = [
            {"tags": list(sig), "files": list(files)}
            for sig, files in dupes.items()
        ]
        return {
            "ok": True,
            "groups": out_groups,
            "group_count": res.get("duplicate_groups", len(out_groups)),
            "file_count": res.get("duplicate_files_count", sum(len(g["files"]) for g in out_groups)),
            "total_files": res.get("total_files", 0),
            "message": res.get("message", ""),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def filter_orphans_handler() -> Dict[str, Any]:
    try:
        from .filter.service import find_orphaned_files
        res = find_orphaned_files() or {}
        return {
            "ok": True,
            "orphans": list(res.get("orphans", []) or []),
            "count": res.get("orphan_count", 0),
            "total_files": res.get("total_files", 0),
            "message": res.get("message", ""),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def filter_clusters_handler(min_size: int = 2) -> Dict[str, Any]:
    try:
        from .filter.service import find_tag_clusters
        try:
            min_size = max(2, int(min_size))
        except Exception:
            min_size = 2
        res = find_tag_clusters(min_cluster_size=min_size) or {}
        # Shape into a JSON-friendly list of {tag, file_count, percentage, files}.
        clusters = res.get("clusters", {}) or {}
        out = [
            {
                "tag": tag,
                "file_count": info.get("file_count", 0),
                "percentage": round(info.get("percentage", 0), 2),
                "files": list(info.get("files", []) or []),
            }
            for tag, info in clusters.items()
        ]
        return {
            "ok": True,
            "clusters": out,
            "count": len(out),
            "min_size": min_size,
            "total_files": res.get("total_files", 0),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def filter_isolated_handler(max_shared: int = 1) -> Dict[str, Any]:
    try:
        from .filter.service import find_isolated_files
        try:
            max_shared = max(0, int(max_shared))
        except Exception:
            max_shared = 1
        res = find_isolated_files(max_shared_tags=max_shared) or {}
        return {
            "ok": True,
            "isolated": list(res.get("isolated_files", []) or []),
            "count": len(res.get("isolated_files", []) or []),
            "max_shared": max_shared,
            "total_files": res.get("total_files", 0),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Clean — remove tag entries for files that no longer exist on disk
# ---------------------------------------------------------------------------


def clean_handler(dry_run: bool = True) -> Dict[str, Any]:
    """Wrap move.service.clean_missing in a JSON-shaped response."""
    try:
        from .move.service import clean_missing
        res = clean_missing(dry_run=bool(dry_run)) or {}
        return {
            "ok": bool(res.get("success", False)),
            "dry_run": bool(res.get("dry_run", dry_run)),
            "missing": list(res.get("missing", []) or []),
            "count": int(res.get("count", 0)),
            "message": res.get("message", ""),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def bulk_apply_handler(pattern: str, tags: List[str], base_path: str = ".") -> Dict[str, Any]:
    pattern = (pattern or "").strip() or "**/*"
    clean = [str(t).strip() for t in (tags or []) if str(t).strip()]
    if not clean:
        return {"ok": False, "error": "at least one tag required"}
    root = gui_allowed_root()
    try:
        from .bulk.service import find_files_by_pattern, bulk_add_tags
        # When a root restriction is in effect, run the find first, filter, then
        # call bulk_add_tags per-file via add_tags to keep the same alias/auto-tag
        # logic and avoid touching files outside the allowed tree.
        if root:
            files = _filter_to_allowed_root(
                find_files_by_pattern(pattern, (base_path or ".").strip() or ".")
            )
            if not files:
                return {
                    "ok": False, "error": "no files matched within allowed root",
                    "pattern": pattern, "files": [], "count": 0,
                }
            modified = 0
            for f in files:
                if add_tags(f, list(clean), apply_aliases=True, auto_tag=True):
                    modified += 1
            return {
                "ok": True, "pattern": pattern, "tags": clean,
                "files_processed": modified, "files_found": files,
                "message": f"Added tags {clean} to {modified} file(s).",
            }
        result = bulk_add_tags(pattern, clean,
                               (base_path or ".").strip() or ".", dry_run=False)
        result["ok"] = bool(result.get("success", False))
        return result
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
