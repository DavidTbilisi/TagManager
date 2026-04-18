from typing import Dict, List
from ...config_manager import get_config_manager


def get_aliases() -> Dict[str, str]:
    """Return the current alias map {alias: canonical_tag}."""
    mgr = get_config_manager()
    return mgr.get("aliases", {}) or {}


def add_alias(alias: str, canonical: str) -> bool:
    """Map alias -> canonical. Returns False if alias == canonical."""
    alias = alias.strip().lower()
    canonical = canonical.strip().lower()
    if not alias or not canonical or alias == canonical:
        return False
    mgr = get_config_manager()
    aliases = get_aliases()
    aliases[alias] = canonical
    mgr.set_raw("aliases", aliases)
    return True


def remove_alias(alias: str) -> bool:
    """Remove an alias. Returns False if it didn't exist."""
    alias = alias.strip().lower()
    mgr = get_config_manager()
    aliases = get_aliases()
    if alias not in aliases:
        return False
    del aliases[alias]
    mgr.set_raw("aliases", aliases)
    return True


def clear_aliases() -> int:
    """Remove all aliases. Returns count removed."""
    mgr = get_config_manager()
    aliases = get_aliases()
    count = len(aliases)
    mgr.set_raw("aliases", {})
    return count


def apply_aliases(tags: List[str]) -> List[str]:
    """
    Replace any tag that matches a known alias with its canonical form.
    Deduplicates the result while preserving order.
    """
    aliases = get_aliases()
    if not aliases:
        return tags
    seen = []
    for tag in tags:
        resolved = aliases.get(tag.lower(), tag)
        if resolved not in seen:
            seen.append(resolved)
    return seen
