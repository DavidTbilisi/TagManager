from ..helpers import load_tags, normalized_levenshtein_distance
from ...configReader import config
from ...config_manager import get_config
from typing import List, Optional, Set


def search_files_by_tags(
    tags: List[str],
    match_all: bool = False,
    exact_match: bool = False,
    exclude_tags: Optional[List[str]] = None,
) -> List[str]:
    """
    Search for files by tags.

    :param tags: A list of tags to search for.
    :param match_all: If True, only return files that match all tags (AND).
    :param exact_match: If True, only return files that match tags exactly.
    :param exclude_tags: Files carrying ANY of these tags are excluded (NOT).
    :return: A list of files that match the tags.
    """
    data = load_tags()
    fuzzy_threshold = get_config("search.fuzzy_threshold", 0.6)
    matched_files: Set[str] = set()

    for file, file_tags in data.items():
        if exact_match:
            def matches(tag, file_tag):
                return tag.lower() == file_tag.lower()
        else:
            def matches(tag, file_tag):
                tl, ftl = tag.lower(), file_tag.lower()
                return tl in ftl or normalized_levenshtein_distance(tl, ftl) >= fuzzy_threshold

        if match_all:
            if all(
                any(matches(tag, file_tag) for file_tag in file_tags)
                for tag in tags
            ):
                matched_files.add(file)
        else:
            if any(
                any(matches(tag, file_tag) for file_tag in file_tags)
                for tag in tags
            ):
                matched_files.add(file)

    # Apply NOT filter — remove any file that carries an excluded tag
    if exclude_tags:
        def _excluded(file_tags_list: List[str]) -> bool:
            return any(
                any(
                    exc.lower() == ft.lower() or exc.lower() in ft.lower()
                    for ft in file_tags_list
                )
                for exc in exclude_tags
            )
        matched_files = {f for f in matched_files if not _excluded(data[f])}

    file_or_path = config["LIST_ALL"]["DISPLAY_FILE_AS"]
    max_path_length = int(config["LIST_ALL"]["MAX_PATH_LENGTH"])

    if file_or_path == "FILENAME":
        matched_files = {file.split("\\")[-1] for file in matched_files}

    matched_files = {
        file[: max_path_length - 3] + "..." if len(file) > max_path_length else file
        for file in matched_files
    }

    return list(matched_files)


def search_files_by_path(query: str) -> List[str]:
    """
    Search for files whose paths contain the query.

    :param query: The path or part of the path to search for.
    :return: A list of files that match the path query.
    """
    data = load_tags()
    return [file for file in data if query.lower() in file.lower()]


def combined_search(
    tags: Optional[List[str]] = None,
    path_query: Optional[str] = None,
    match_all_tags: bool = False,
    exclude_tags: Optional[List[str]] = None,
) -> List[str]:
    """
    Perform a combined search by tags and/or path.

    :param tags: A list of tags to search for.
    :param path_query: The path or part of the path to search for.
    :param match_all_tags: If True, only return files that match all tags.
    :param exclude_tags: Files carrying ANY of these tags are excluded (NOT).
    :return: A list of files that match the search criteria.
    """
    if not tags and not path_query:
        return []

    data = load_tags()
    all_files = set(data.keys())

    tag_matched_files = (
        set(search_files_by_tags(tags, match_all_tags, exclude_tags=exclude_tags)) if tags else all_files
    )
    path_matched_files = (
        set(search_files_by_path(path_query)) if path_query else all_files
    )

    return list(tag_matched_files & path_matched_files)


def search_by_tags(tags: List[str]) -> List[str]:
    """
    Simple search by tags function for compatibility with tests
    :param tags: List of tags to search for
    :return: List of files that contain ALL the specified tags
    """
    if not tags:
        return []

    data = load_tags()
    matched_files = []

    for file_path, file_tags in data.items():
        if all(tag in file_tags for tag in tags):
            matched_files.append(file_path)

    return matched_files
