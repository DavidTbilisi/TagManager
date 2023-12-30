import argparse
import sys
from app.tags import open_list_files_by_tag_result, list_files_by_tags, list_tags_all, search_tags
from app.list import list_tags
from app.add import add_tags
from app.remove import remove_tags
from app.list_all import print_list_tags_all_table
from app.storage import show_storage_location, open_storage_location

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="File Tagging System")
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for add
    parser_add = subparsers.add_parser('add', help='Add tags to a file')
    parser_add.add_argument("file", help="Path to the file")
    parser_add.add_argument("--tags", nargs='+', required=True, help="Tags to add")

    # Subparser for remove
    parser_remove = subparsers.add_parser('remove', help='Remove tags from a file')
    parser_remove.add_argument("file", help="Path to the file")
    parser_remove.add_argument("--tags", nargs='+', required=True, help="Tags to remove")

    # Subparser for list
    parser_list = subparsers.add_parser('list', help='List tags of a file')
    parser_list.add_argument("file", help="Path to the file")

    # Subparser for list all
    subparsers.add_parser('list-all', help='List all files and tags in a table')

    # Subparser for storage
    parser_storage = subparsers.add_parser('storage', help='Display storage location of the tag file')
    parser_storage.add_argument("--open", action="store_true", help="Open the storage location")

    # Subparser for tags
    tags_parser = subparsers.add_parser('tags', help='List all tags')
    tags_parser.add_argument('--search', help='List files by a specific tag')

    # Subparser for list files by tag
    parser_list_files_by_tag = subparsers.add_parser('tag-search', help='List files by a specific tag')
    parser_list_files_by_tag.add_argument("tag", help="Tag to list files for")
    parser_list_files_by_tag.add_argument("--open", action="store_true", help="Open the file")
    parser_list_files_by_tag.add_argument("--exact", action="store_true", help="Exact match for tag")

    args = parser.parse_args()

    if args.command == 'add':
        add_tags(args.file, args.tags)
    elif args.command == 'remove':
        remove_tags(args.file, args.tags)
    elif args.command == 'list':
        print(list_tags(args.file))
    elif args.command == 'list-all':
        print_list_tags_all_table()
    elif args.command == 'tags':
        if args.search:
            print(search_tags(args.search))
        else:
            print(list_tags_all())
    elif args.command == 'tag-search':
        if args.open:
            open_list_files_by_tag_result(list_files_by_tags(args.tag, args.exact))
        else:
            print(list_files_by_tags(args.tag, args.exact))
    elif args.command == 'storage':
        if args.open:
            open_storage_location()
        else:
            print(show_storage_location())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
