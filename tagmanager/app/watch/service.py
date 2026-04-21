import fnmatch
import os
import time
import threading
from datetime import datetime
from typing import Callable, Dict, List, Optional

from ..helpers import load_tags, save_tags
from ..autotag.service import suggest_tags_for_file
from ..move.service import move_path
from ..remove.service import remove_path


def _apply_aliases_safe(tags: List[str]) -> List[str]:
    try:
        from ..alias.service import apply_aliases
        return apply_aliases(tags)
    except Exception:
        return tags


def _get_preset_safe(name: str) -> List[str]:
    try:
        from ..preset.service import get_preset
        return get_preset(name) or []
    except Exception:
        return []


def tag_file_silently(
    file_path: str,
    extra_tags: List[str],
    preset_name: Optional[str],
    auto_tag: bool,
    content_tag: bool = True,
) -> Dict:
    """
    Tag a file without any print output. Returns a result dict.
    Unlike add_tags(), this works with an empty tag list (auto-tags only).
    """
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return {"success": False, "path": abs_path, "tags": [], "reason": "file not found"}

    tags: List[str] = list(extra_tags)

    if preset_name:
        tags.extend(_get_preset_safe(preset_name))

    if auto_tag:
        suggested = suggest_tags_for_file(abs_path, include_content=content_tag)
        for t in suggested:
            if t not in tags:
                tags.append(t)

    if not tags:
        return {"success": False, "path": abs_path, "tags": [], "reason": "no tags to apply"}

    tags = _apply_aliases_safe(tags)

    existing = load_tags()
    existing[abs_path] = list(set(existing.get(abs_path, [])).union(set(tags)))
    ok = save_tags(existing)

    return {
        "success": ok,
        "path": abs_path,
        "tags": existing[abs_path],
        "reason": "" if ok else "save failed",
    }


class WatchEvent:
    """Represents one processed file system event."""
    __slots__ = ("kind", "path", "dest", "tags", "success", "reason", "timestamp")

    def __init__(
        self,
        kind: str,
        path: str,
        success: bool,
        tags: Optional[List[str]] = None,
        dest: Optional[str] = None,
        reason: str = "",
    ) -> None:
        self.kind = kind          # "created" | "moved" | "deleted" | "modified"
        self.path = path
        self.dest = dest          # only for "moved"
        self.tags = tags or []
        self.success = success
        self.reason = reason
        self.timestamp = datetime.now()


try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler as _Base
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    _Base = object


class _TagManagerHandler(_Base):  # type: ignore[misc]
    def __init__(
        self,
        extra_tags: List[str],
        preset_name: Optional[str],
        auto_tag: bool,
        content_tag: bool,
        on_delete_clean: bool,
        ignore_patterns: List[str],
        on_event: Callable[[WatchEvent], None],
    ) -> None:
        if WATCHDOG_AVAILABLE:
            super().__init__()
        self.extra_tags = extra_tags
        self.preset_name = preset_name
        self.auto_tag = auto_tag
        self.content_tag = content_tag
        self.on_delete_clean = on_delete_clean
        self.ignore_patterns = ignore_patterns
        self.on_event = on_event
        self._lock = threading.Lock()

    def _ignored(self, path: str) -> bool:
        name = os.path.basename(path)
        for pat in self.ignore_patterns:
            if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(path, pat):
                return True
        return False

    def on_created(self, event) -> None:
        if event.is_directory or self._ignored(event.src_path):
            return
        with self._lock:
            result = tag_file_silently(
                event.src_path,
                self.extra_tags,
                self.preset_name,
                self.auto_tag,
                self.content_tag,
            )
        self.on_event(WatchEvent(
            kind="created",
            path=event.src_path,
            success=result["success"],
            tags=result.get("tags", []),
            reason=result.get("reason", ""),
        ))

    def on_moved(self, event) -> None:
        if event.is_directory or self._ignored(event.src_path):
            return
        with self._lock:
            result = move_path(event.src_path, event.dest_path)
        self.on_event(WatchEvent(
            kind="moved",
            path=event.src_path,
            dest=event.dest_path,
            success=result.get("success", False),
            reason=result.get("message", ""),
        ))

    def on_deleted(self, event) -> None:
        if event.is_directory or self._ignored(event.src_path) or not self.on_delete_clean:
            return
        with self._lock:
            result = remove_path(event.src_path)
        self.on_event(WatchEvent(
            kind="deleted",
            path=event.src_path,
            success=result.get("success", False),
            reason=result.get("message", ""),
        ))

    def on_modified(self, event) -> None:
        # We don't re-tag on modify — tags are set on creation.
        pass


def start_watching(
    path: str,
    recursive: bool,
    extra_tags: List[str],
    preset_name: Optional[str],
    auto_tag: bool,
    content_tag: bool,
    on_delete_clean: bool,
    ignore_patterns: List[str],
    on_event: Callable[[WatchEvent], None],
) -> "Observer":
    """Start a watchdog Observer and return it (already started)."""
    if not WATCHDOG_AVAILABLE:
        raise ImportError(
            "watchdog is required for watch mode.\n"
            "Install it with:  pip install watchdog\n"
            "Or:               pip install tagmanager-cli[watch]"
        )

    handler = _TagManagerHandler(
        extra_tags=extra_tags,
        preset_name=preset_name,
        auto_tag=auto_tag,
        content_tag=content_tag,
        on_delete_clean=on_delete_clean,
        ignore_patterns=ignore_patterns,
        on_event=on_event,
    )
    observer = Observer()
    observer.schedule(handler, path=path, recursive=recursive)
    observer.start()
    return observer
