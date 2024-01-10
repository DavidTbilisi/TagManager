import argparse
import sys

from app.add.handler import handle_add_command
from app.list_all.handler import handle_list_all_command
from app.paths.handler import handle_path_command
from app.remove.handler import handle_remove_command
from app.search.handler import handle_search_command
from app.storage.handler import handle_storage_command
from app.tags.handler import handle_tags_command


sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

command_handlers = {
    'add': handle_add_command,
    'remove': handle_remove_command,
    'path': handle_path_command,
    'ls': handle_list_all_command,
    'storage': handle_storage_command,
    'tags': handle_tags_command,
    'search': handle_search_command,
}


def main():
    parser = argparse.ArgumentParser(
        prog="tm",
        description="Tag Manager - File Tagging System",
    )

    subparsers = parser.add_subparsers(dest='command')

    # Subparser for add
    parser_add = subparsers.add_parser('add', help='Add tags to a file')
    parser_add.add_argument("file", help="Path to the file")
    parser_add.add_argument("-t", "--tags", nargs='+', required=True, help="Tags to add")
    # parser_add.add_argument("--desc", help="Description for the file")

    # Subparser for remove
    parser_remove = subparsers.add_parser('remove', help='Remove path from tags')
    parser_remove.add_argument("-p", "--path", help="Path to the file")
    parser_remove.add_argument("-i", "--invalid", action="store_true", help="Remove invalid paths from tags")

    # Subparser for list all
    parser_list_all = subparsers.add_parser('ls', help='List files and tags in a table')
    parser_list_all.add_argument("--all", help="Not implemented")
    parser_list_all.add_argument("--ext", help="Not implemented")

    # Subparser for path
    parser_path = subparsers.add_parser('path', help='List tags of a file')
    parser_path.add_argument("filepath", help="Path to the file")
    parser_path.add_argument("-f", "--fuzzy", action="store_true", help="Type of search to use")
    parser_path.add_argument("-F", "--folder", action="store_true", help="Search for a folder instead of a file")
    parser_path.add_argument("-e", "--exact", action="store_true", help="Exact match for file path")

    # Subparser for tags
    tags_parser = subparsers.add_parser('tags', help='List all tags')
    tags_parser.add_argument("-s", "--search", help="List files by a specific tag")
    tags_parser.add_argument("-o", "--open", action="store_true", help="Open the file")
    tags_parser.add_argument("-e", "--exact", action="store_true", help="Exact match for tag")
    tags_parser.add_argument("-w", "--where", action="store_true", help="Display the path of the file")

    # Subparser for storage
    parser_storage = subparsers.add_parser('storage', help='Display storage location of the tag file')
    parser_storage.add_argument("-o", "--open", action="store_true", help="Open the storage location")

    # Subparser for search
    search_parser = subparsers.add_parser('search', help='Search files by tags or path')
    search_parser.add_argument("-t", "--tags", nargs='+', help="List of tags to search for")
    search_parser.add_argument("-p", "--path", help="Path query to search for")
    search_parser.add_argument("-a", "--match_all", action="store_true", help="Match all specified tags (AND operation)")
    search_parser.add_argument("-e", "--exact", action="store_true", help="Exact match for tags")
    search_parser.add_argument("-o", "--open", action="store_true", help="Open the file")

    args = parser.parse_args()

    if args.command in command_handlers:
        command_handlers.get(args.command)(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
