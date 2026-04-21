import csv
import json
import os
from typing import Dict, List, Optional

from ..helpers import load_tags, save_tags


def export_tags_json(output_path: str) -> Dict:
    """Export all tag data to a JSON file."""
    data = load_tags()
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return {
            "success": True,
            "path": output_path,
            "file_count": len(data),
            "message": f"Exported {len(data)} file(s) to {output_path}",
        }
    except OSError as e:
        return {"success": False, "path": output_path, "message": str(e)}


def export_tags_csv(output_path: str) -> Dict:
    """Export all tag data to a CSV file (one row per file-tag pair)."""
    data = load_tags()
    rows = 0
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["file_path", "tags"])
            for path, tags in data.items():
                writer.writerow([path, ",".join(tags)])
                rows += 1
        return {
            "success": True,
            "path": output_path,
            "file_count": rows,
            "message": f"Exported {rows} file(s) to {output_path}",
        }
    except OSError as e:
        return {"success": False, "path": output_path, "message": str(e)}


def import_tags(input_path: str, replace: bool = False) -> Dict:
    """
    Import tag data from a JSON or CSV file.

    :param input_path: Path to the import file (.json or .csv).
    :param replace: If True, replace the entire database. If False, merge (new wins on conflict).
    :return: Result dict with success status and counts.
    """
    if not os.path.exists(input_path):
        return {"success": False, "message": f"File not found: {input_path}"}

    ext = os.path.splitext(input_path)[1].lower()

    try:
        if ext == ".json":
            with open(input_path, "r", encoding="utf-8") as f:
                imported: Dict[str, List[str]] = json.load(f)
            if not isinstance(imported, dict):
                return {"success": False, "message": "Invalid JSON format: expected an object"}
        elif ext == ".csv":
            imported = {}
            with open(input_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    path = row.get("file_path", "").strip()
                    tags_raw = row.get("tags", "").strip()
                    if path:
                        imported[path] = [t.strip() for t in tags_raw.split(",") if t.strip()]
        else:
            return {"success": False, "message": f"Unsupported format '{ext}'. Use .json or .csv"}
    except (json.JSONDecodeError, KeyError, csv.Error) as e:
        return {"success": False, "message": f"Failed to parse file: {e}"}

    if replace:
        existing = {}
    else:
        existing = load_tags()

    conflicts = 0
    for path, tags in imported.items():
        if path in existing and not replace:
            # Merge: union of tag sets
            merged = list(set(existing[path]) | set(tags))
            if set(merged) != set(existing.get(path, [])):
                conflicts += 1
            existing[path] = merged
        else:
            existing[path] = tags

    save_tags(existing)

    return {
        "success": True,
        "imported": len(imported),
        "conflicts_merged": conflicts,
        "total_files": len(existing),
        "message": (
            f"Imported {len(imported)} file(s). "
            + (f"{conflicts} merged with existing tags. " if conflicts else "")
            + f"Total: {len(existing)} file(s) in database."
        ),
    }
