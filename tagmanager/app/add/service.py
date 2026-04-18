import os
from ..helpers import load_tags, save_tags


def add_tags(file_path: str, tags: list, apply_aliases: bool = True, auto_tag: bool = True) -> bool:
    """
    Takes an existing file path and adds tags to it.

    :param file_path: path to the file (must exist on disk)
    :param tags: non-empty list of tags to add
    :param apply_aliases: whether to resolve tag aliases before saving
    :param auto_tag: whether to merge extension-based auto-tags
    :return: True if successful, False otherwise
    """
    tags = [t for t in tags if t.strip()]
    if not tags:
        print("Error: No valid tags provided (all were empty or whitespace).")
        return False

    file_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return False

    # Apply extension-based auto-tags
    if auto_tag:
        try:
            from ..autotag.service import suggest_tags_for_file
            ext_tags = suggest_tags_for_file(file_path)
            for t in ext_tags:
                if t not in tags:
                    tags.append(t)
        except Exception:
            pass

    # Resolve aliases
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
