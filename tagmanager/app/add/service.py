import os
from typing import Any, Dict, List

from ..helpers import load_tags, save_tags


def add_tags(file_path: str, tags: list, apply_aliases: bool = True, auto_tag: bool = True) -> bool:
    """
    Takes an existing file path and adds tags to it.

    :param file_path: path to the file (must exist on disk)
    :param tags: tags to add (may be empty if ``auto_tag`` supplies extension tags)
    :param apply_aliases: whether to resolve tag aliases before saving
    :param auto_tag: whether to merge extension-based auto-tags
    :return: True if successful, False otherwise
    """
    tags = [t for t in tags if t.strip()]

    file_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return False

    # Extension-based auto-tags (rule-based, not AI) — merge before empty check
    if auto_tag:
        try:
            from ..autotag.service import suggest_tags_for_file

            ext_tags = suggest_tags_for_file(file_path)
            for t in ext_tags:
                if t not in tags:
                    tags.append(t)
        except Exception:
            pass

    if not tags:
        print("Error: No valid tags provided (all were empty or whitespace).")
        return False

    if apply_aliases:
        try:
            from ..alias.service import apply_aliases as _apply
            tags = _apply(tags)
        except Exception:
            pass

    existing_tags = load_tags()
    existing_tags[file_path] = list(
        set(existing_tags.get(file_path, [])).union(set(tags))
    )
    is_saved = save_tags(existing_tags)

    if is_saved:
        try:
            print(f"Tags added to '{file_path}'")
        except UnicodeEncodeError:
            pass
        return True
    else:
        print(f"Error: Failed to save tags for '{file_path}'")
        return False


def add_tags_recursive(
    dir_path: str,
    tags: List[str],
    apply_aliases: bool = True,
    auto_tag: bool = True,
) -> Dict[str, Any]:
    """
    Recursively tag every file under ``dir_path`` using the same rules as
    ``add_tags`` (explicit tags + extension map + optional aliases).
    Uses a single load/save for efficiency.
    """
    from ..autotag.service import iter_files_recursive, suggest_tags_for_file

    dir_path = os.path.abspath(os.path.join(os.getcwd(), dir_path))
    if not os.path.isdir(dir_path):
        print(
            f"Error: '{dir_path}' is not a directory "
            "(omit --recursive to tag a single file path)."
        )
        return {"success": False, "files_tagged": 0, "total_files": 0}

    files = iter_files_recursive(dir_path)
    if not files:
        print(f"Error: No files found under '{dir_path}'.")
        return {"success": False, "files_tagged": 0, "total_files": 0}

    data = load_tags()
    base = [t for t in tags if t.strip()]
    files_tagged = 0

    for fp in files:
        merged = list(base)
        if auto_tag:
            try:
                for t in suggest_tags_for_file(fp):
                    if t not in merged:
                        merged.append(t)
            except Exception:
                pass
        if not merged:
            continue
        if apply_aliases:
            try:
                from ..alias.service import apply_aliases as _apply

                merged = _apply(merged)
            except Exception:
                pass
        prev = set(data.get(fp, []))
        new_set = prev.union(set(merged))
        if new_set != prev:
            data[fp] = list(new_set)
            files_tagged += 1

    if files_tagged == 0:
        print(
            f"No changes under '{dir_path}' "
            "(files already had these tags, or nothing to apply with --no-auto)."
        )
        return {
            "success": True,
            "files_tagged": 0,
            "total_files": len(files),
        }

    if not save_tags(data):
        print("Error: Failed to save tags")
        return {"success": False, "files_tagged": 0, "total_files": len(files)}

    try:
        print(f"Tags applied to {files_tagged} file(s) under '{dir_path}'")
    except UnicodeEncodeError:
        pass
    return {
        "success": True,
        "files_tagged": files_tagged,
        "total_files": len(files),
    }
