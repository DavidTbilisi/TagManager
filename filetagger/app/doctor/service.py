"""Read-only diagnostics for ``tm doctor``."""

from __future__ import annotations

import json
import os
import shutil
import sys
from typing import Any, Dict, List, Optional, Tuple


def _inspect_tag_file(path: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "path": path,
        "exists": os.path.isfile(path),
        "readable": False,
        "invalid_json": False,
        "path_count": 0,
        "empty_file": False,
    }
    if not out["exists"]:
        return out
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as e:
        out["read_error"] = str(e)
        return out
    out["readable"] = True
    if not raw.strip():
        out["empty_file"] = True
        return out
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        out["invalid_json"] = True
        out["json_error"] = str(e)
        return out
    if not isinstance(data, dict):
        out["invalid_json"] = True
        out["json_error"] = "root must be a JSON object"
        return out
    out["path_count"] = len(data)
    return out


def _config_check() -> Dict[str, Any]:
    try:
        from ...config_manager import get_config_manager

        mgr = get_config_manager()
        p = mgr.get("storage.tag_file_path", "")
        return {"ok": True, "storage.tag_file_path": p}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _journal_info() -> Dict[str, Any]:
    try:
        from ..journal.service import journal_enabled, journal_path_for_display

        return {
            "enabled": journal_enabled(),
            "journal_file": journal_path_for_display(),
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)}


def _sample_missing_paths(
    tag_paths: List[str], max_check: int
) -> Tuple[int, int, List[str]]:
    """Return (checked, missing_count, examples)."""
    checked = 0
    missing = 0
    examples: List[str] = []
    for p in tag_paths[:max_check]:
        checked += 1
        if not os.path.exists(p):
            missing += 1
            if len(examples) < 10:
                examples.append(p)
    return checked, missing, examples


def run_doctor(*, max_path_checks: int = 500) -> Dict[str, Any]:
    """
    Run diagnostics. ``ok`` is False only for hard problems (unreadable config,
    unreadable tag file, or invalid tag JSON when file exists and is non-empty).
    """
    from ..helpers import get_tag_file_path, load_tags

    tag_path = os.path.abspath(os.path.expanduser(get_tag_file_path()))
    tag_meta = _inspect_tag_file(tag_path)

    config = _config_check()
    journal = _journal_info()

    tm_exe = shutil.which("tm")
    cli_info = {
        "tm_on_path": tm_exe,
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
    }

    data = load_tags()
    paths = list(data.keys()) if isinstance(data, dict) else []
    checked, missing, examples = _sample_missing_paths(paths, max_path_checks)

    sample_paths = {
        "total_paths_in_db": len(paths),
        "checked": checked,
        "missing_on_disk": missing,
        "missing_examples": examples,
    }

    ok = bool(config.get("ok"))
    if tag_meta.get("read_error"):
        ok = False
    if tag_meta.get("invalid_json"):
        ok = False

    lines = [
        f"Tag file: {tag_meta['path']}",
        f"  exists: {tag_meta['exists']}  readable: {tag_meta.get('readable', False)}",
    ]
    if tag_meta.get("invalid_json"):
        lines.append(f"  INVALID JSON: {tag_meta.get('json_error', '')}")
    elif tag_meta.get("read_error"):
        lines.append(f"  read error: {tag_meta['read_error']}")
    else:
        lines.append(f"  entries (paths): {tag_meta.get('path_count', 0)}")

    lines.append(f"Config OK: {config.get('ok')}")
    if not config.get("ok"):
        lines.append(f"  {config.get('error', '')}")

    lines.append(f"Journal: enabled={journal.get('enabled')}  file={journal.get('journal_file', '')}")
    lines.append(f"CLI: tm={tm_exe or '(not on PATH)'}")
    lines.append(f"     python={cli_info['python_executable']}")
    lines.append(
        f"Paths on disk (sample up to {checked}): {missing} missing "
        f"(of {len(paths)} total in DB)"
    )
    if examples:
        for ex in examples[:5]:
            lines.append(f"  missing: {ex}")

    return {
        "ok": ok,
        "message": "\n".join(lines),
        "checks": {
            "tag_file": tag_meta,
            "config": config,
            "journal": journal,
            "cli": cli_info,
            "sample_paths": sample_paths,
        },
    }
