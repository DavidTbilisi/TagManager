"""Append-only JSONL journal of mutating tag operations for ``tm undo``."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..helpers import get_tag_file_path, load_tags, save_tags
from ...config_manager import get_config_manager


def _journal_file_path() -> str:
    base = os.path.dirname(os.path.abspath(get_tag_file_path()))
    return os.path.join(base, "tag_operations.jsonl")


def journal_enabled() -> bool:
    env = os.environ.get("TAGMANAGER_JOURNAL", "").lower()
    if env in ("1", "true", "yes", "on"):
        return True
    if env in ("0", "false", "no", "off"):
        return False
    try:
        return bool(get_config_manager().get("journal.enabled", False))
    except Exception:
        return False


def _max_undo_bytes() -> int:
    try:
        return int(get_config_manager().get("journal.max_undo_bytes", 5_000_000))
    except Exception:
        return 5_000_000


def append_entry(op: str, inverse: Dict[str, Any]) -> None:
    if not journal_enabled():
        return
    raw = json.dumps(inverse, ensure_ascii=False)
    if len(raw.encode("utf-8")) > _max_undo_bytes():
        return
    path = _journal_file_path()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    entry = {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "op": op,
        "inverse": inverse,
    }
    line = json.dumps(entry, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(line)


def _read_all_entries() -> List[Dict[str, Any]]:
    path = _journal_file_path()
    if not os.path.isfile(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _write_entries(entries: List[Dict[str, Any]]) -> None:
    path = _journal_file_path()
    if not entries:
        if os.path.isfile(path):
            os.remove(path)
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")


def apply_inverse(inverse: Dict[str, Any]) -> bool:
    """Apply a path patch or full-database snapshot."""
    if inverse.get("type") == "full_replace":
        before = inverse.get("before")
        if not isinstance(before, dict):
            return False
        return save_tags(dict(before))

    paths = inverse.get("paths")
    if not isinstance(paths, dict):
        return False
    data = load_tags()
    for path, val in paths.items():
        if val is None:
            data.pop(path, None)
        elif isinstance(val, list):
            data[path] = list(val)
        else:
            return False
    return save_tags(data)


def undo_last(count: int = 1) -> Tuple[bool, str, int]:
    """
    Undo the last ``count`` journal entries (most recent first).
    Returns (success, message, applied_count).
    """
    if count < 1:
        return False, "count must be >= 1", 0
    all_e = _read_all_entries()
    if not all_e:
        return False, "No operations in journal to undo.", 0
    n = min(count, len(all_e))
    tail = all_e[-n:]
    remaining = all_e[:-n]

    applied = 0
    for ent in reversed(tail):
        inv = ent.get("inverse")
        if not isinstance(inv, dict):
            continue
        if not apply_inverse(inv):
            return False, f"Undo failed while applying entry {ent.get('id')}", applied
        applied += 1

    _write_entries(remaining)
    return True, f"Undid {applied} operation(s).", applied


def journal_path_for_display() -> str:
    return _journal_file_path()
