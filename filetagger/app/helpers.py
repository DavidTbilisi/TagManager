import json
import os
from ..config_manager import get_config


path = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(path)


def get_tag_file_path():
    """Get the tag file path from configuration, with fallback to legacy config"""
    try:
        tag_path = get_config("storage.tag_file_path", "~/file_tags.json")
    except Exception:
        from ..configReader import config
        tag_path = config["DEFAULT"]["TAG_FILE"]

    return os.path.expanduser(tag_path)


def load_tags() -> dict:
    """
    Load tags from the tag file
    :return: json object of tags
    """
    tag_file = get_tag_file_path()
    if not os.path.exists(tag_file):
        return {}
    try:
        with open(tag_file, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        print(f"Warning: Tag file '{tag_file}' is corrupted. Returning empty data.")
        return {}
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not read tag file '{tag_file}': {e}")
        return {}


def save_tags(tags: dict) -> bool:
    """
    Save tags to the tag file atomically (write-to-temp then rename).
    :param tags: Tags to save in dict format {file_path: [tags]}
    :return: True if successful, False otherwise
    """
    tag_file = get_tag_file_path()
    try:
        tag_dir = os.path.dirname(tag_file)
        if tag_dir:
            os.makedirs(tag_dir, exist_ok=True)

        tmp_file = tag_file + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as file:
            json.dump(tags, file, indent=4)
        os.replace(tmp_file, tag_file)
        return True

    except OSError as e:
        print(f"Error while saving tags: {e}")
        return False
    except Exception as e:
        print("Error while saving tags:", e)
        return False


def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def normalized_levenshtein_distance(s1, s2):
    if len(s1) == 0 and len(s2) == 0:
        return 1.0

    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return (max_len - distance) / max_len
