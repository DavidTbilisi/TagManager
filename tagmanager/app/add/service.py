import copy
import os
from typing import Any, Dict, List, Optional, Sequence

from ..helpers import load_tags, save_tags


def compute_single_file_add_merge(
    file_path: str,
    tags: list,
    apply_aliases: bool = True,
    auto_tag: bool = True,
    content_tag: bool = True,
) -> Optional[tuple[List[str], Optional[List[str]]]]:
    """
    Resolve path, auto-tags, aliases, and merged tag set **without** saving.

    :return: ``(merged_tags, before_tags)`` where ``before_tags`` is ``None`` if the path
        was absent from the DB, or ``None`` if the path does not exist / no tags to apply.
    """
    tags = [t for t in tags if t.strip()]

    abs_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
    if not os.path.exists(abs_path):
        return None

    if auto_tag:
        try:
            from ..autotag.service import suggest_tags_for_file

            ext_tags = suggest_tags_for_file(abs_path, include_content=content_tag)
            for t in ext_tags:
                if t not in tags:
                    tags.append(t)
        except Exception:
            pass

    if not tags:
        return None

    if apply_aliases:
        try:
            from ..alias.service import apply_aliases as _apply

            tags = _apply(tags)
        except Exception:
            pass

    existing_tags = load_tags()
    before_val: Optional[List[str]] = (
        copy.deepcopy(existing_tags[abs_path]) if abs_path in existing_tags else None
    )
    merged = list(set(existing_tags.get(abs_path, [])).union(set(tags)))
    return merged, before_val


def add_tags(
    file_path: str,
    tags: list,
    apply_aliases: bool = True,
    auto_tag: bool = True,
    content_tag: bool = True,
    dry_run: bool = False,
) -> bool:
    """
    Takes an existing file path and adds tags to it.

    :param file_path: path to the file (must exist on disk)
    :param tags: tags to add (may be empty if ``auto_tag`` supplies extension tags)
    :param apply_aliases: whether to resolve tag aliases before saving
    :param auto_tag: whether to merge extension-based auto-tags
    :param content_tag: when auto_tag is on, also apply content keyword/regex rules
    :param dry_run: if True, show outcome without saving (no journal entry)
    :return: True if successful, False otherwise
    """
    abs_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
    if not os.path.exists(abs_path):
        print(f"Error: The file '{abs_path}' does not exist.")
        return False

    computed = compute_single_file_add_merge(
        file_path, tags, apply_aliases, auto_tag, content_tag
    )
    if computed is None:
        print("Error: No valid tags provided (all were empty or whitespace).")
        return False

    merged, before_val = computed
    if dry_run:
        try:
            print(
                f"[dry-run] Would set tags on '{abs_path}' to "
                f"{sorted(merged)} (was {before_val or 'absent'})"
            )
        except UnicodeEncodeError:
            pass
        return True

    existing_tags = load_tags()
    existing_tags[abs_path] = merged
    is_saved = save_tags(existing_tags)

    if is_saved:
        try:
            from ..journal.service import append_entry

            if sorted(before_val or []) != sorted(merged):
                append_entry(
                    "add_tags",
                    {"paths": {abs_path: before_val}},
                )
        except Exception:
            pass

    if is_saved:
        try:
            print(f"Tags added to '{abs_path}'")
        except UnicodeEncodeError:
            pass
        return True
    else:
        print(f"Error: Failed to save tags for '{abs_path}'")
        return False


def add_tags_recursive(
    dir_path: str,
    tags: List[str],
    apply_aliases: bool = True,
    auto_tag: bool = True,
    content_tag: bool = True,
    dry_run: bool = False,
    include_globs: Optional[Sequence[str]] = None,
    exclude_globs: Optional[Sequence[str]] = None,
    auto_include_globs: Optional[Sequence[str]] = None,
    auto_exclude_globs: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Recursively tag every file under ``dir_path`` using the same rules as
    ``add_tags`` (explicit tags + extension map + optional aliases).
    Uses a single load/save for efficiency.

    :param include_globs: If set, only files matching at least one glob are considered.
    :param exclude_globs: Files matching any glob are skipped entirely.
    :param auto_include_globs: When set, extension/content auto-tags apply only to matching files.
    :param auto_exclude_globs: Files matching any glob get explicit tags only (no auto-tags).
    """
    from ..autotag.path_filters import filter_walk_files, should_apply_autotag_for_path
    from ..autotag.service import iter_files_recursive, suggest_tags_for_file

    dir_path = os.path.abspath(os.path.join(os.getcwd(), dir_path))
    if not os.path.isdir(dir_path):
        print(
            f"Error: '{dir_path}' is not a directory "
            "(omit --recursive to tag a single file path)."
        )
        return {"success": False, "files_tagged": 0, "total_files": 0}

    raw_files = iter_files_recursive(dir_path)
    if not raw_files:
        print(f"Error: No files found under '{dir_path}'.")
        return {"success": False, "files_tagged": 0, "total_files": 0}

    files = filter_walk_files(raw_files, dir_path, include_globs, exclude_globs)
    if not files:
        print(
            f"No files matched filters under '{dir_path}' "
            f"({len(raw_files)} scanned). Adjust --include / --exclude."
        )
        return {
            "success": True,
            "files_tagged": 0,
            "total_files": 0,
            "scanned_files": len(raw_files),
        }

    data = load_tags()
    work = copy.deepcopy(data) if dry_run else data
    before_snap = {
        fp: (copy.deepcopy(data[fp]) if fp in data else None) for fp in files
    }
    base = [t for t in tags if t.strip()]
    files_tagged = 0
    touched: List[str] = []

    for fp in files:
        merged = list(base)
        if auto_tag and should_apply_autotag_for_path(
            fp, dir_path, auto_include_globs, auto_exclude_globs
        ):
            try:
                for t in suggest_tags_for_file(fp, include_content=content_tag):
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
        prev = set(work.get(fp, []))
        new_set = prev.union(set(merged))
        if new_set != prev:
            work[fp] = list(new_set)
            files_tagged += 1
            touched.append(fp)

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

    if dry_run:
        try:
            print(
                f"[dry-run] Would update {files_tagged} file(s) under '{dir_path}' "
                f"(of {len(files)} scanned)."
            )
        except UnicodeEncodeError:
            pass
        return {
            "success": True,
            "files_tagged": files_tagged,
            "total_files": len(files),
            "dry_run": True,
        }

    if not save_tags(work):
        print("Error: Failed to save tags")
        return {"success": False, "files_tagged": 0, "total_files": len(files)}

    try:
        from ..journal.service import append_entry

        inv_paths = {fp: before_snap[fp] for fp in touched}
        append_entry("add_tags_recursive", {"paths": inv_paths})
    except Exception:
        pass

    try:
        print(f"Tags applied to {files_tagged} file(s) under '{dir_path}'")
    except UnicodeEncodeError:
        pass
    return {
        "success": True,
        "files_tagged": files_tagged,
        "total_files": len(files),
    }
