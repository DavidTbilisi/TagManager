import os
import re
from typing import Any, Dict, FrozenSet, List, Optional, Set

from ...config_manager import get_config_manager

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

# Built-in substring/regex → tags when ``autotag.content_enabled`` is true.
# Merged with ``autotag.content_rules`` (user rules after defaults). Disable
# defaults with ``autotag.content_use_defaults``: false.
DEFAULT_CONTENT_RULES: List[Dict[str, Any]] = [
    # Python web
    {"contains": "django.", "tags": ["django", "web"]},
    {"contains": "from django", "tags": ["django", "web"]},
    {"contains": "from flask", "tags": ["flask", "web"]},
    {"contains": "import flask", "tags": ["flask", "web"]},
    {"contains": "fastapi", "tags": ["fastapi", "web"]},
    {"contains": "starlette", "tags": ["starlette", "web"]},
    {"contains": "uvicorn", "tags": ["uvicorn", "server"]},
    {"contains": "gunicorn", "tags": ["gunicorn", "server"]},
    {"contains": "tornado.", "tags": ["tornado", "web"]},
    {"contains": "sanic", "tags": ["sanic", "web"]},
    # Data / ML
    {"contains": "import pandas", "tags": ["pandas", "data"]},
    {"contains": "import numpy", "tags": ["numpy", "data"]},
    {"pattern": r"\bimport\s+torch\b", "tags": ["pytorch", "ml"]},
    {"contains": "tensorflow", "tags": ["tensorflow", "ml"]},
    {"contains": "sklearn", "tags": ["scikit-learn", "ml"]},
    {"contains": "polars", "tags": ["polars", "data"]},
    # ORM / DB tooling
    {"contains": "sqlalchemy", "tags": ["sqlalchemy", "database"]},
    {"contains": "pydantic", "tags": ["pydantic"]},
    {"contains": "prisma", "tags": ["prisma", "database"]},
    # Async / messaging
    {"contains": "celery", "tags": ["celery", "async"]},
    {"contains": "kafka", "tags": ["kafka", "messaging"]},
    {"contains": "rabbitmq", "tags": ["rabbitmq", "messaging"]},
    # Testing
    {"contains": "pytest", "tags": ["pytest", "testing"]},
    {"pattern": r"\bjest\b", "tags": ["jest", "testing"]},
    {"contains": "mocha", "tags": ["mocha", "testing"]},
    # CLI frameworks
    {"contains": "import typer", "tags": ["typer", "cli"]},
    {"contains": "import click", "tags": ["click", "cli"]},
    # JS / TS UI
    {"contains": "from \"react\"", "tags": ["react", "frontend"]},
    {"contains": "from 'react'", "tags": ["react", "frontend"]},
    {"contains": "from \"vue\"", "tags": ["vue", "frontend"]},
    {"contains": "from 'vue'", "tags": ["vue", "frontend"]},
    {"pattern": r"@angular/", "tags": ["angular", "frontend"]},
    {"contains": "svelte", "tags": ["svelte", "frontend"]},
    # Bundlers / lint
    {"contains": "eslint", "tags": ["eslint", "lint"]},
    {"contains": "webpack", "tags": ["webpack", "bundler"]},
    {"pattern": r"\bvite\b", "tags": ["vite", "bundler"]},
    {"contains": "rollup", "tags": ["rollup", "bundler"]},
    # Rust ecosystem
    {"contains": "tokio::", "tags": ["tokio", "async", "rust"]},
    {"contains": "serde::", "tags": ["serde", "rust"]},
    # Containers (Dockerfile)
    {"pattern": r"(?m)^FROM\s+\S+", "tags": ["docker", "container"]},
    # Infra
    {"contains": "terraform", "tags": ["terraform", "infra"]},
    {"contains": "kubernetes", "tags": ["kubernetes", "infra"]},
    {"contains": "helm", "tags": ["helm", "kubernetes", "infra"]},
]


def get_merged_content_rules() -> List[Dict[str, Any]]:
    """Defaults plus ``autotag.content_rules``, unless ``content_use_defaults`` is false."""
    mgr = get_config_manager()
    extra = mgr.get("autotag.content_rules") or []
    if not isinstance(extra, list):
        extra = []
    if not mgr.get("autotag.content_use_defaults", True):
        return list(extra)
    return list(DEFAULT_CONTENT_RULES) + list(extra)


def get_recursive_skip_dir_names() -> FrozenSet[str]:
    """Names of directories to skip when recursing (defaults + config extras)."""
    mgr = get_config_manager()
    extra = mgr.get("autotag.recursive_skip_dirs") or []
    if not isinstance(extra, (list, tuple)):
        return DEFAULT_RECURSIVE_SKIP_DIRS
    return DEFAULT_RECURSIVE_SKIP_DIRS | frozenset(str(x) for x in extra)


def iter_files_recursive(root_dir: str) -> List[str]:
    """
    List all regular files under root_dir (recursive, rule-based — no AI).

    Honors ``files.follow_symlinks``, ``files.include_hidden_files`` (via
    ``files.include_hidden``), and ``autotag.recursive_skip_dirs`` from config.
    """
    root_dir = os.path.abspath(os.path.join(os.getcwd(), root_dir))
    if not os.path.isdir(root_dir):
        return []

    mgr = get_config_manager()
    follow_links = bool(mgr.get("files.follow_symlinks", False))
    include_hidden = bool(mgr.get("files.include_hidden", False))
    skip_dirs = get_recursive_skip_dir_names()

    out: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=follow_links):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in skip_dirs and (include_hidden or not d.startswith("."))
        ]
        for name in filenames:
            if not include_hidden and name.startswith("."):
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


def suggest_tags_from_content(file_path: str) -> List[str]:
    """
    Apply built-in and configured content rules to a file prefix.

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
    if snippet is None:
        return []

    hay_lower = snippet.lower()
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

        pattern = rule.get("pattern")
        if isinstance(pattern, str) and pattern.strip():
            try:
                flags = 0 if rule.get("case_sensitive") else re.IGNORECASE
                if re.search(pattern, snippet, flags):
                    out.extend(tag_list)
            except re.error:
                continue
            continue

        needle = rule.get("contains")
        if not isinstance(needle, str) or not needle.strip():
            continue
        if rule.get("case_sensitive"):
            if needle in snippet:
                out.extend(tag_list)
        else:
            if needle.lower() in hay_lower:
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
    Suggested tags: file extension map, optionally plus content rules
    (``DEFAULT_CONTENT_RULES`` merged with ``autotag.content_rules`` when
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
