import copy
import csv
import json
import os
from typing import Dict, List, Optional

from ..helpers import get_tag_file_path, load_tags, save_tags


def _export_path_key(
    path: str,
    relative_to: Optional[str],
    strip_prefix: Optional[str],
) -> str:
    """Map a stored absolute path to an export key (relative or stripped)."""
    path_abs = os.path.normpath(os.path.abspath(path))
    if relative_to:
        root = os.path.normpath(os.path.abspath(relative_to))
        try:
            return os.path.relpath(path_abs, root)
        except ValueError:
            return path_abs
    if strip_prefix:
        sp = os.path.normpath(os.path.abspath(strip_prefix.rstrip("/\\")))
        if path_abs == sp:
            return "."
        if path_abs.startswith(sp + os.sep):
            rest = path_abs[len(sp) + 1 :]
            return rest if rest else "."
    return path_abs


def export_tags_json(
    output_path: str,
    relative_to: Optional[str] = None,
    strip_prefix: Optional[str] = None,
) -> Dict:
    """Export all tag data to a JSON file."""
    if relative_to and strip_prefix:
        return {
            "success": False,
            "path": output_path,
            "message": "Use only one of relative_to or strip_prefix, not both.",
        }
    data = load_tags()
    mapped: Dict[str, List[str]] = {}
    for path, tags in data.items():
        key = _export_path_key(path, relative_to, strip_prefix)
        mapped[key] = list(tags)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mapped, f, indent=2, ensure_ascii=False)
        return {
            "success": True,
            "path": output_path,
            "file_count": len(data),
            "message": f"Exported {len(data)} file(s) to {output_path}",
        }
    except OSError as e:
        return {"success": False, "path": output_path, "message": str(e)}


def export_tags_csv(
    output_path: str,
    relative_to: Optional[str] = None,
    strip_prefix: Optional[str] = None,
) -> Dict:
    """Export all tag data to a CSV file (one row per file-tag pair)."""
    if relative_to and strip_prefix:
        return {
            "success": False,
            "path": output_path,
            "message": "Use only one of relative_to or strip_prefix, not both.",
        }
    data = load_tags()
    rows = 0
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["file_path", "tags"])
            for path, tags in data.items():
                key = _export_path_key(path, relative_to, strip_prefix)
                writer.writerow([key, ",".join(tags)])
                rows += 1
        return {
            "success": True,
            "path": output_path,
            "file_count": rows,
            "message": f"Exported {rows} file(s) to {output_path}",
        }
    except OSError as e:
        return {"success": False, "path": output_path, "message": str(e)}


def import_tags(
    input_path: str,
    replace: bool = False,
    merge_strategy: str = "union",
    strict_paths: bool = False,
    dry_run: bool = False,
) -> Dict:
    """
    Import tag data from a JSON or CSV file.

    :param replace: If True, replace the entire database (ignores merge_strategy).
    :param merge_strategy: ``union`` (default), ``incoming_wins``, or ``keep_existing``.
    :param strict_paths: Skip paths that do not exist on disk.
    :param dry_run: Compute merge result without saving or writing the journal.
    """
    if not os.path.exists(input_path):
        return {"success": False, "message": f"File not found: {input_path}"}

    ext = os.path.splitext(input_path)[1].lower()

    try:
        if ext == ".json":
            with open(input_path, "r", encoding="utf-8") as f:
                raw_imported: Dict[str, List[str]] = json.load(f)
            if not isinstance(raw_imported, dict):
                return {"success": False, "message": "Invalid JSON format: expected an object"}
        elif ext == ".csv":
            raw_imported = {}
            with open(input_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    path = row.get("file_path", "").strip()
                    tags_raw = row.get("tags", "").strip()
                    if path:
                        raw_imported[path] = [t.strip() for t in tags_raw.split(",") if t.strip()]
        else:
            return {"success": False, "message": f"Unsupported format '{ext}'. Use .json or .csv"}
    except (json.JSONDecodeError, KeyError, csv.Error) as e:
        return {"success": False, "message": f"Failed to parse file: {e}"}

    imported: Dict[str, List[str]] = {}
    skipped_strict = 0
    for path, tags in raw_imported.items():
        if not isinstance(path, str):
            continue
        path = path.strip()
        if not path:
            continue
        if not isinstance(tags, list):
            tags = [tags]  # type: ignore[list-item]
        norm_tags = [str(t).strip() for t in tags if str(t).strip()]
        if strict_paths and not os.path.exists(path):
            skipped_strict += 1
            continue
        imported[path] = norm_tags

    if not imported:
        return {"success": False, "message": "No valid rows to import."}

    full_before = copy.deepcopy(load_tags())
    ms = (merge_strategy or "union").lower().strip()

    if replace:
        existing: Dict[str, List[str]] = {k: list(v) for k, v in imported.items()}
        conflicts = 0
    else:
        existing = load_tags()
        conflicts = 0
        for path, tags in imported.items():
            if path in existing:
                if ms == "incoming_wins":
                    if set(tags) != set(existing[path]):
                        conflicts += 1
                    existing[path] = list(tags)
                elif ms == "keep_existing":
                    continue
                else:
                    merged = list(set(existing[path]) | set(tags))
                    if set(merged) != set(existing.get(path, [])):
                        conflicts += 1
                    existing[path] = merged
            else:
                existing[path] = list(tags)

    msg_parts = [
        f"Imported {len(imported)} file(s).",
        f" {conflicts} path(s) touched in merge. " if conflicts else "",
        f" Total: {len(existing)} file(s).",
    ]
    if skipped_strict:
        msg_parts.append(f" Skipped {skipped_strict} missing path(s) (--strict-paths).")

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "imported": len(imported),
            "conflicts_merged": conflicts,
            "total_files": len(existing),
            "skipped_paths": skipped_strict,
            "message": "[dry-run] " + "".join(msg_parts),
        }

    if not save_tags(existing):
        return {"success": False, "message": "Failed to save tags after import."}

    try:
        from ..journal.service import append_entry

        append_entry("import_tags", {"type": "full_replace", "before": full_before})
    except Exception:
        pass

    return {
        "success": True,
        "imported": len(imported),
        "conflicts_merged": conflicts,
        "total_files": len(existing),
        "skipped_paths": skipped_strict,
        "message": "".join(msg_parts),
    }


def default_tag_backup_path() -> str:
    """JSON path next to the live tag file (``file_tags.backup.json`` in the same directory)."""
    tf = os.path.normpath(os.path.abspath(os.path.expanduser(get_tag_file_path())))
    parent = os.path.dirname(tf) or "."
    return os.path.join(parent, "file_tags.backup.json")


def backup_tag_database(output_path: Optional[str] = None) -> Dict:
    """Write a full JSON export; default path from :func:`default_tag_backup_path`."""
    out = output_path or default_tag_backup_path()
    return export_tags_json(out)


def restore_tag_database(
    input_path: Optional[str] = None,
    replace: bool = False,
    merge_strategy: str = "union",
    strict_paths: bool = False,
    dry_run: bool = False,
) -> Dict:
    """Merge or replace from a JSON/CSV backup; default file from :func:`default_tag_backup_path`."""
    src = input_path or default_tag_backup_path()
    return import_tags(
        src,
        replace=replace,
        merge_strategy=merge_strategy,
        strict_paths=strict_paths,
        dry_run=dry_run,
    )
