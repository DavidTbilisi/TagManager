import os
import re
from typing import Any, Dict, FrozenSet, List, Optional, Set

from ...config_manager import get_config_manager

from .content_rule_groups import CONTENT_RULE_GROUPS, DEFAULT_CONTENT_RULES

# Directory names skipped when walking a tree for recursive auto-tagging.
DEFAULT_RECURSIVE_SKIP_DIRS: FrozenSet[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".tox",
        "dist",
        "build",
        ".mypy_cache",
        ".eggs",
        ".idea",
        ".nox",
    }
)

DEFAULT_EXTENSION_TAGS: Dict[str, List[str]] = {
    ".py": ["python"],
    ".js": ["javascript"],
    ".ts": ["typescript"],
    ".jsx": ["javascript", "react"],
    ".tsx": ["typescript", "react"],
    ".rs": ["rust"],
    ".go": ["golang"],
    ".java": ["java"],
    ".kt": ["kotlin"],
    ".rb": ["ruby"],
    ".php": ["php"],
    ".cs": ["csharp"],
    ".cpp": ["cpp"],
    ".c": ["c"],
    ".h": ["c", "header"],
    ".swift": ["swift"],
    ".sh": ["shell", "script"],
    ".bash": ["shell", "script"],
    ".bat": ["batch", "script"],
    ".ps1": ["powershell", "script"],
    ".md": ["markdown", "docs"],
    ".rst": ["docs"],
    ".txt": ["text"],
    ".pdf": ["pdf", "document"],
    ".epub": ["epub", "ebook"],
    ".mobi": ["mobi", "ebook"],
    ".azw": ["kindle", "ebook"],
    ".azw3": ["kindle", "ebook"],
    ".docx": ["word", "document"],
    ".xlsx": ["excel", "spreadsheet"],
    ".csv": ["csv", "data"],
    ".json": ["json", "data"],
    ".yaml": ["yaml", "config"],
    ".yml": ["yaml", "config"],
    ".toml": ["toml", "config"],
    ".ini": ["ini", "config"],
    ".env": ["env", "config"],
    ".html": ["html", "web"],
    ".css": ["css", "web"],
    ".scss": ["scss", "web"],
    ".sql": ["sql", "database"],
    ".db": ["database"],
    ".jpg": ["image"],
    ".jpeg": ["image"],
    ".png": ["image"],
    ".gif": ["image"],
    ".svg": ["svg", "image"],
    ".mp4": ["video"],
    ".mov": ["video"],
    ".mp3": ["audio"],
    ".wav": ["audio"],
    ".zip": ["archive"],
    ".tar": ["archive"],
    ".gz": ["archive"],
    ".dockerfile": ["docker"],
    ".tf": ["terraform", "infrastructure"],
}

# Built-in rules live in ``content_rule_groups`` (grouped for ``autotag.content_pattern_groups``).
# Each rule may use any of: ``contains`` / ``pattern`` (file prefix),
# ``title_contains`` / ``title_pattern`` (stem without extension),
# ``filename_contains`` / ``filename_pattern`` (basename). Present facets
# must all match (AND). Merged with ``autotag.content_rules``. Disable
# defaults with ``autotag.content_use_defaults``: false.


def _filtered_default_content_rules(mgr) -> List[Dict[str, Any]]:
    """
    Built-in rules respecting ``autotag.content_pattern_groups``.

    Missing or ``null`` key → all groups. Empty list ``[]`` → no built-in rules
    (custom ``autotag.content_rules`` still apply when ``content_use_defaults`` is true).
    Unknown group ids in config are ignored.
    """
    raw = mgr.get("autotag.content_pattern_groups")
    if raw is None:
        return list(DEFAULT_CONTENT_RULES)
    if not isinstance(raw, list):
        return list(DEFAULT_CONTENT_RULES)
    allowed = frozenset(str(x) for x in raw)
    if not allowed:
        return []
    out: List[Dict[str, Any]] = []
    for group in CONTENT_RULE_GROUPS:
        if group["id"] in allowed:
            out.extend(group["rules"])
    return out


def get_merged_content_rules() -> List[Dict[str, Any]]:
    """Defaults (optionally filtered by group) plus ``autotag.content_rules``."""
    mgr = get_config_manager()
    extra = mgr.get("autotag.content_rules") or []
    if not isinstance(extra, list):
        extra = []
    if not mgr.get("autotag.content_use_defaults", True):
        return list(extra)
    return _filtered_default_content_rules(mgr) + list(extra)


def get_recursive_skip_dir_names() -> FrozenSet[str]:
    """Names of directories to skip when recursing (defaults + config extras)."""
    mgr = get_config_manager()
    extra = mgr.get("autotag.recursive_skip_dirs") or []
    if not isinstance(extra, (list, tuple)):
        return DEFAULT_RECURSIVE_SKIP_DIRS
    return DEFAULT_RECURSIVE_SKIP_DIRS | frozenset(str(x) for x in extra)


def iter_files_recursive(root_dir: str, max_depth: Optional[int] = None) -> List[str]:
    """
    List all regular files under root_dir (recursive, rule-based — no AI).

    Honors ``files.follow_symlinks``, ``files.include_hidden_files`` (via
    ``files.include_hidden``), and ``autotag.recursive_skip_dirs`` from config.

    :param max_depth: If ``1``, only files directly inside ``root_dir`` (no subfolders).
        If ``2``, root plus one level of subdirectories, etc. ``None`` means unlimited.
    """
    root_dir = os.path.abspath(os.path.join(os.getcwd(), root_dir))
    if not os.path.isdir(root_dir):
        return []

    mgr = get_config_manager()
    follow_links = bool(mgr.get("files.follow_symlinks", False))
    include_hidden = bool(mgr.get("files.include_hidden", False))
    skip_dirs = get_recursive_skip_dir_names()

    if max_depth is not None and max_depth < 1:
        return []

    if max_depth == 1:
        out: List[str] = []
        try:
            for name in os.listdir(root_dir):
                if not include_hidden and name.startswith("."):
                    continue
                fp = os.path.join(root_dir, name)
                if os.path.isfile(fp):
                    out.append(fp)
        except OSError:
            return []
        return out

    out = []
    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=follow_links):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in skip_dirs and (include_hidden or not d.startswith("."))
        ]
        rel_d = os.path.relpath(dirpath, root_dir)
        dlev = 0 if rel_d in (".", os.curdir) else rel_d.count(os.sep) + 1
        if max_depth is not None and dlev + 1 >= max_depth:
            dirnames[:] = []
        for name in filenames:
            if not include_hidden and name.startswith("."):
                continue
            if max_depth is not None and dlev >= max_depth:
                continue
            fp = os.path.join(dirpath, name)
            if os.path.isfile(fp):
                out.append(fp)
    return out


def get_extension_tags_map() -> Dict[str, List[str]]:
    """Return extension→tags map, merging config overrides with defaults."""
    mgr = get_config_manager()
    overrides = mgr.get("autotag.extension_tags", {}) or {}
    merged = dict(DEFAULT_EXTENSION_TAGS)
    merged.update(overrides)
    return merged


def _read_file_snippet(file_path: str, max_bytes: int) -> Optional[str]:
    """Read up to max_bytes for content rules; None if unreadable or likely binary."""
    if not os.path.isfile(file_path):
        return None
    max_bytes = max(256, min(int(max_bytes), 2_000_000))
    try:
        with open(file_path, "rb") as fh:
            raw = fh.read(max_bytes)
    except (OSError, PermissionError):
        return None
    if not raw:
        return ""
    if b"\x00" in raw[: min(8192, len(raw))]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def _facet_match(
    text: Optional[str],
    rule: Dict[str, Any],
    pattern_key: str,
    contains_key: str,
) -> bool:
    """
    Match one facet (content, title, or filename). No keys for this facet → True.
    Keys present but *text* is None (e.g. unreadable/binary snippet) → False.
    """
    pat_raw = rule.get(pattern_key)
    has_pat = isinstance(pat_raw, str) and pat_raw.strip()
    con_raw = rule.get(contains_key)
    has_con = isinstance(con_raw, str) and con_raw.strip()
    if not has_pat and not has_con:
        return True
    if text is None:
        return False
    if has_pat:
        try:
            flags = 0 if rule.get("case_sensitive") else re.IGNORECASE
            return bool(re.search(pat_raw, text, flags))
        except re.error:
            return False
    if rule.get("case_sensitive"):
        return con_raw in text
    return con_raw.lower() in text.lower()


def _rule_has_match_clause(rule: Dict[str, Any]) -> bool:
    for key in (
        "pattern",
        "contains",
        "title_pattern",
        "title_contains",
        "filename_pattern",
        "filename_contains",
    ):
        v = rule.get(key)
        if isinstance(v, str) and v.strip():
            return True
    return False


def _rule_matches_snippet_and_names(
    rule: Dict[str, Any],
    snippet: Optional[str],
    title: str,
    filename: str,
) -> bool:
    """All present facets (content / title / filename) must match."""
    if not _rule_has_match_clause(rule):
        return False
    if not _facet_match(snippet, rule, "pattern", "contains"):
        return False
    if not _facet_match(title, rule, "title_pattern", "title_contains"):
        return False
    if not _facet_match(filename, rule, "filename_pattern", "filename_contains"):
        return False
    return True


def suggest_tags_from_content(file_path: str) -> List[str]:
    """
    Apply built-in and configured rules to file prefix, basename, and stem.

    Opt-in via ``autotag.content_enabled``. Built-ins are
    ``DEFAULT_CONTENT_RULES`` unless ``autotag.content_use_defaults`` is false.
    Not semantic AI — substring / pattern matching only.
    """
    mgr = get_config_manager()
    if not mgr.get("autotag.content_enabled", False):
        return []

    rules = get_merged_content_rules()
    if not rules:
        return []

    max_bytes = int(mgr.get("autotag.content_max_bytes", 65536) or 65536)
    snippet = _read_file_snippet(file_path, max_bytes)
    basename = os.path.basename(file_path)
    title = os.path.splitext(basename)[0]

    out: List[str] = []

    for rule in rules:
        if not isinstance(rule, dict):
            continue
        raw_tags = rule.get("tags")
        if not isinstance(raw_tags, list):
            continue
        tag_list = [t for t in raw_tags if isinstance(t, str) and t.strip()]
        if not tag_list:
            continue

        if not _rule_matches_snippet_and_names(rule, snippet, title, basename):
            continue
        out.extend(tag_list)

    seen: Set[str] = set()
    deduped: List[str] = []
    for t in out:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def suggest_tags_for_file(file_path: str, *, include_content: bool = True) -> List[str]:
    """
    Suggested tags: file extension map, optionally plus content/title/filename
    rules (``DEFAULT_CONTENT_RULES`` merged with ``autotag.content_rules`` when
    ``autotag.content_enabled``). Disabled when ``autotag.enabled`` is false.
    """
    mgr = get_config_manager()
    if not mgr.get("autotag.enabled", True):
        return []

    ext = os.path.splitext(file_path)[1].lower()
    mapping = get_extension_tags_map()
    out: List[str] = list(mapping.get(ext, []))

    if include_content:
        out.extend(suggest_tags_from_content(file_path))

    seen: Set[str] = set()
    deduped: List[str] = []
    for t in out:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def set_extension_tags(extension: str, tags: List[str]) -> None:
    """Override the tag list for a specific extension in config."""
    if not extension.startswith("."):
        extension = "." + extension
    extension = extension.lower()
    mgr = get_config_manager()
    block_raw: Any = mgr.get("autotag")
    block: Dict[str, Any] = dict(block_raw) if isinstance(block_raw, dict) else {}
    overrides = dict(block.get("extension_tags") or {})
    overrides[extension] = tags
    block["extension_tags"] = overrides
    block.setdefault("enabled", True)
    mgr.set_raw("autotag", block)
