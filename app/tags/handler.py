from app.tags.service import list_tags_all, list_files_by_tags, open_list_files_by_tag_result


def handle_tags_command(args):
    if args.search and args.open:
        open_list_files_by_tag_result(
            list_files_by_tags(args.search, args.exact)
        )
    elif args.search:
        result = list_files_by_tags(args.search, args.exact)
        for i, file in enumerate(result, start=1):
            print(f"{i}. {file}")
    else:
        for i, tag in enumerate(list_tags_all(), start=1):
            print(f"{i}. {tag}")
