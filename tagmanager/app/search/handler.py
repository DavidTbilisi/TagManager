from typing import List, Optional

from .service import (
    combined_search,
    filter_paths_by_exclude_tags,
    search_files_by_path,
    search_files_by_tags,
)


def _resolve_exclude_tags(args) -> Optional[List[str]]:
    raw = getattr(args, "exclude", None)
    if raw is None:
        raw = getattr(args, "exclude_tags", None)
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        return list(raw)
    return None


def handle_search_command(args):
    exclude = _resolve_exclude_tags(args)

    if args.tags and args.path:
        # Combined search by tags and path
        result = combined_search(
            args.tags, args.path, args.match_all, exclude_tags=exclude
        )
    elif args.tags:
        # Search by tags only
        result = search_files_by_tags(
            args.tags, args.match_all, args.exact, exclude_tags=exclude
        )
    elif args.path:
        # Search by path only
        result = search_files_by_path(args.path)
        if exclude:
            result = filter_paths_by_exclude_tags(result, exclude)
    else:
        print("No search criteria provided.")
        print("Example: tm search -t python -p C:\\Users\\User\\Documents")
        print("Example: tm search -t python -t linux")
        print("Example: tm search -p C:\\Users\\User\\Documents")
        print(
            "Example: tm search -p C:\\Users\\User\\Documents -p C:\\Users\\User\\Downloads"
        )
        return

    if result:
        for i, file in enumerate(result, start=1):
            print(f"{i}. {file}")
        print()
    else:
        print("No files found matching the criteria.")
