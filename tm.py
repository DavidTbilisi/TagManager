import argparse
import sys
from app.tags import open_list_files_by_tag_result, list_files_by_tags, list_tags_all, search_tags
from app.paths import path_tags, fuzzy_search_path
from app.add import add_tags
from app.remove import remove_tags
from app.list_all import print_list_tags_all_table
from app.storage import show_storage_location, open_storage_location

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(
        prog="tm",
        description="Tag Manager - File Tagging System",
    )
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for add
    parser_add = subparsers.add_parser('add', help='Add tags to a file')
    parser_add.add_argument("file", help="Path to the file")
    parser_add.add_argument("--tags", nargs='+', required=True, help="Tags to add")
    # parser_add.add_argument("--desc", help="Description for the file")

    # Subparser for remove
    parser_remove = subparsers.add_parser('remove', help='Remove tags from a file')
    parser_remove.add_argument("file", help="Path to the file")
    parser_remove.add_argument("--tags", nargs='+', required=True, help="Tags to remove")

    # Subparser for path
    parser_path = subparsers.add_parser('path', help='List tags of a file')
    parser_path.add_argument("filepath", help="Path to the file")
    parser_path.add_argument("--fuzzy", action="store_true", help="Type of search to use")
    parser_path.add_argument("--folder", action="store_true", help="Search for a folder instead of a file")
    parser_path.add_argument("--exact", action="store_true", help="Exact match for file path")

    # Subparser for list all
    parser_list_all = subparsers.add_parser('ls', help='List files and tags in a table')
    parser_list_all.add_argument("--all", help="List files with a specific extension")
    parser_list_all.add_argument("--ext", help="List files with a specific extension")

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
    parser_list_files_by_tag.add_argument("--where", action="store_true", help="Display the path of the file")

    args = parser.parse_args()

    if args.command == 'add':
        add_tags(args.file, args.tags)
    elif args.command == 'remove':
        remove_tags(args.file, args.tags)
    elif args.command == 'path':
        if args.fuzzy:
            print(fuzzy_search_path(args.filepath))
        elif args.exact:
            print(path_tags(args.filepath))
        else:
            print(fuzzy_search_path(args.filepath))
    elif args.command == 'ls':
        print_list_tags_all_table()
    elif args.command == 'tags':
        if args.search:
            print(search_tags(args.search))
        else:
            print(list_tags_all())
    elif args.command == 'tag-search':
        by_tags = list_files_by_tags(args.tag, args.exact)
        if args.open:
            # interactive mode
            open_list_files_by_tag_result(by_tags)
        elif args.where:
            # interactive mode
            print(open_list_files_by_tag_result(by_tags, True))
        else:
            for index, file in enumerate(by_tags, start=1):
                print(index, file)
    elif args.command == 'storage':
        if args.open:
            open_storage_location()
        else:
            print(show_storage_location())
    else:
        parser.print_help()


"""
TODO: Refactoring
def handle_add_command(args):
    add_tags(args.file, args.tags)

def handle_remove_command(args):
    remove_tags(args.file, args.tags)

def handle_path_command(args):
    if args.exact:
        print(path_tags(args.filepath))
    else:  # Default to fuzzy search
        print(fuzzy_search_path(args.filepath))

# ... similar functions for other commands ...

args = parser.parse_args()

command_handlers = {
    'add': handle_add_command,
    'remove': handle_remove_command,
    'path': handle_path_command,
    # ... other commands ...
}

handler = command_handlers.get(args.command)
if handler:
    handler(args)
else:
    parser.print_help()
"""
if __name__ == "__main__":
    main()
