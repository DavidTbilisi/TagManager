import os
from typing import Dict, List

from ...config_manager import get_config_manager

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


def get_extension_tags_map() -> Dict[str, List[str]]:
    """Return extension→tags map, merging config overrides with defaults."""
    mgr = get_config_manager()
    overrides = mgr.get("autotag.extension_tags", {}) or {}
    merged = dict(DEFAULT_EXTENSION_TAGS)
    merged.update(overrides)
    return merged


def suggest_tags_for_file(file_path: str) -> List[str]:
    """
    Return suggested tags based on the file extension.
    Returns [] if no mapping exists or auto-tagging is disabled.
    """
    mgr = get_config_manager()
    if not mgr.get("autotag.enabled", True):
        return []

    ext = os.path.splitext(file_path)[1].lower()
    mapping = get_extension_tags_map()
    return list(mapping.get(ext, []))


def set_extension_tags(extension: str, tags: List[str]) -> None:
    """Override the tag list for a specific extension in config."""
    if not extension.startswith("."):
        extension = "." + extension
    extension = extension.lower()
    mgr = get_config_manager()
    overrides = mgr.get("autotag.extension_tags", {}) or {}
    overrides[extension] = tags
    mgr.set_raw("autotag", {"enabled": mgr.get("autotag.enabled", True), "extension_tags": overrides})
