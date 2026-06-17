"""Named saved searches (tags/path/match options) in config under ``saved_searches``."""

from typing import Any, Dict, List, Optional, Tuple

from ...config_manager import get_config_manager
from ..search.service import (
    combined_search,
    filter_paths_by_exclude_tags,
    search_files_by_path,
    search_files_by_tags,
)


def _flatten_option_tags(groups: Optional[List[str]]) -> List[str]:
    flat: List[str] = []
    for g in groups or []:
        flat.extend(x.strip() for x in g.split(",") if x.strip())
    return flat


def get_saved_searches() -> Dict[str, Dict[str, Any]]:
    mgr = get_config_manager()
    raw = mgr.get("saved_searches")
    return raw if isinstance(raw, dict) else {}


def get_saved_search(name: str) -> Optional[Dict[str, Any]]:
    return get_saved_searches().get(name.strip().lower())


def save_saved_search(
    name: str,
    tags: Optional[List[str]] = None,
    path: Optional[str] = None,
    match_all: bool = False,
    exact: bool = False,
    exclude: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    name = name.strip().lower()
    if not name:
        return False, "Name cannot be empty."
    flat_tags = _flatten_option_tags(tags)
    path_clean = (path or "").strip() or None
    flat_exc = _flatten_option_tags(exclude)
    if not flat_tags and not path_clean:
        return False, "Provide at least one --tags or --path."
    mgr = get_config_manager()
    all_sq = dict(get_saved_searches())
    all_sq[name] = {
        "tags": flat_tags,
        "path": path_clean,
        "match_all": bool(match_all),
        "exact": bool(exact),
        "exclude": flat_exc,
    }
    mgr.set_raw("saved_searches", all_sq)
    return True, ""


def delete_saved_search(name: str) -> bool:
    name = name.strip().lower()
    mgr = get_config_manager()
    all_sq = dict(get_saved_searches())
    if name not in all_sq:
        return False
    del all_sq[name]
    mgr.set_raw("saved_searches", all_sq)
    return True


def list_saved_search_names() -> List[str]:
    return sorted(get_saved_searches().keys())


def run_saved_search(name: str) -> Tuple[List[str], str]:
    """
    Execute a saved search. Returns (paths, error_message).
    """
    spec = get_saved_search(name)
    if not spec:
        return [], f"Saved search '{name}' not found."

    tags = [str(t) for t in (spec.get("tags") or []) if str(t).strip()]
    path = spec.get("path")
    if isinstance(path, str):
        path = path.strip() or None
    else:
        path = None
    match_all = bool(spec.get("match_all", False))
    exact = bool(spec.get("exact", False))
    exclude = [str(t) for t in (spec.get("exclude") or []) if str(t).strip()]
    ex = exclude if exclude else None

    if tags and path:
        result = combined_search(tags, path, match_all, exclude_tags=ex)
    elif tags:
        result = search_files_by_tags(tags, match_all, exact, exclude_tags=ex)
    elif path:
        result = search_files_by_path(path)
        if ex:
            result = filter_paths_by_exclude_tags(result, exclude)
    else:
        return [], "Saved search has no tags or path."

    return result, ""
