from typing import Dict, List, Optional
from ...config_manager import get_config_manager


def get_presets() -> Dict[str, List[str]]:
    """Return all saved presets {name: [tags]}."""
    mgr = get_config_manager()
    return mgr.get("presets", {}) or {}


def save_preset(name: str, tags: List[str]) -> bool:
    """Save a named preset. Returns False if name or tags are invalid."""
    name = name.strip().lower()
    tags = [t.strip() for t in tags if t.strip()]
    if not name or not tags:
        return False
    mgr = get_config_manager()
    presets = get_presets()
    presets[name] = tags
    mgr.set_raw("presets", presets)
    return True


def delete_preset(name: str) -> bool:
    """Delete a preset by name. Returns False if it doesn't exist."""
    name = name.strip().lower()
    mgr = get_config_manager()
    presets = get_presets()
    if name not in presets:
        return False
    del presets[name]
    mgr.set_raw("presets", presets)
    return True


def get_preset(name: str) -> Optional[List[str]]:
    """Return tags for a named preset, or None if not found."""
    return get_presets().get(name.strip().lower())


def list_presets() -> Dict[str, List[str]]:
    """Alias for get_presets() — explicit for readability."""
    return get_presets()
