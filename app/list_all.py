from app.helpers import load_tags, config
import os


def print_list_tags_all_table():
    tags = load_tags()
    # Determine the maximum length for formatting
    if config["LIST_ALL"]["DISPLAY_FILE_AS"] == "PATH":
        max_file_len = max(len(file) for file in tags)
    else:
        max_file_len = max(len(os.path.split(file)[1]) for file in tags)

    max_tag_len = max(len(tag) for file in tags for tag in tags[file])

    # Create header
    print(f"\n\n{'File'.ljust(max_file_len)} | Tags")
    print(f"{'-' * max_file_len}-+{'-' * max_tag_len}")

    # Print each file and its tags
    for file, file_tags in tags.items():
        tags_str = ', '.join(file_tags)
        # Split path and filename
        if config["LIST_ALL"]["DISPLAY_FILE_AS"] == "FILENAME":
            file = os.path.split(file)[1]
        print(f"{file.ljust(max_file_len)} | {tags_str}".encode('utf-8', 'replace').decode('utf-8'))
