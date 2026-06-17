"""Glob filters for recursive tagging (which files to touch / when to auto-tag)."""

from __future__ import annotations

import fnmatch
import os
from typing import List, Optional, Sequence


def _norm_patterns(patterns: Optional[Sequence[str]]) -> List[str]:
    out: List[str] = []
    for p in patterns or []:
        s = str(p).strip()
        if s:
            out.append(s)
    return out


def path_matches_any_glob(path_abs: str, root_abs: str, patterns: Sequence[str]) -> bool:
    """
    True if ``path_abs`` matches any glob in ``patterns``.

    Tries, in order: path relative to ``root_abs`` (posix slashes), basename only,
    and full ``path_abs`` (posix slashes). This makes patterns like ``*.py``,
    ``src/*.py``, and absolute-style globs usable.
    """
    if not patterns:
        return False
    root_abs = os.path.abspath(os.path.normpath(root_abs))
    path_abs = os.path.abspath(os.path.normpath(path_abs))
    try:
        rel = os.path.relpath(path_abs, root_abs).replace("\\", "/")
    except ValueError:
        rel = path_abs.replace("\\", "/")
    base = os.path.basename(path_abs)
    px = path_abs.replace("\\", "/")
    candidates = (rel, base, px)
    for pat in patterns:
        pat_n = pat.replace("\\", "/")
        for candidate in candidates:
            if fnmatch.fnmatch(candidate, pat_n):
                return True
    return False


def filter_walk_files(
    files: List[str],
    root_dir: str,
    include_globs: Optional[Sequence[str]] = None,
    exclude_globs: Optional[Sequence[str]] = None,
) -> List[str]:
    """
    Drop paths excluded by globs; if ``include_globs`` is non-empty, keep only
    paths matching at least one include pattern. Exclude wins over include.
    """
    root_dir = os.path.abspath(os.path.normpath(root_dir))
    inc = _norm_patterns(include_globs)
    exc = _norm_patterns(exclude_globs)
    out: List[str] = []
    for fp in files:
        fp_a = os.path.abspath(os.path.normpath(fp))
        if exc and path_matches_any_glob(fp_a, root_dir, exc):
            continue
        if inc and not path_matches_any_glob(fp_a, root_dir, inc):
            continue
        out.append(fp_a)
    return out


def should_apply_autotag_for_path(
    path_abs: str,
    root_dir: str,
    auto_include_globs: Optional[Sequence[str]] = None,
    auto_exclude_globs: Optional[Sequence[str]] = None,
) -> bool:
    """
    Whether to run extension/content auto-tagging for this file.

    If ``auto_exclude_globs`` matches, returns False. If ``auto_include_globs``
    is non-empty and nothing matches, returns False. Otherwise True.
    """
    root_dir = os.path.abspath(os.path.normpath(root_dir))
    path_abs = os.path.abspath(os.path.normpath(path_abs))
    exc = _norm_patterns(auto_exclude_globs)
    inc = _norm_patterns(auto_include_globs)
    if exc and path_matches_any_glob(path_abs, root_dir, exc):
        return False
    if inc and not path_matches_any_glob(path_abs, root_dir, inc):
        return False
    return True
