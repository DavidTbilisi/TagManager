import argparse
import sys
from app.tags import open_list_files_by_tag_result, list_files_by_tags
from app.list import list_tags
from app.add import add_tags
from app.remove import remove_tags
from app.list_all import print_list_tags_all_table

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

# Define the file path for the tag file in the user's home directory
# TAG_FILE = os.path.expanduser("~/file_tags.json")

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
    subparsers.add_parser('list-all', help='List all tags')

    # Subparser for list files by tag
    parser_list_files_by_tag = subparsers.add_parser('tagsearch', help='List files by a specific tag')
    parser_list_files_by_tag.add_argument("tag", help="Tag to list files for")


    args = parser.parse_args()

    if args.command == 'add':
        add_tags(args.file, args.tags)
    elif args.command == 'remove':
        remove_tags(args.file, args.tags)
    elif args.command == 'list':
        print(list_tags(args.file))
    elif args.command == 'list-all':
        print_list_tags_all_table()
    elif args.command == 'tagsearch':
        open_list_files_by_tag_result(list_files_by_tags(args.tag))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()