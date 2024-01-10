import os
import sys
import re
from app.helpers import load_tags, save_tags


def display_menu(array_of_file_path):
    print("Select a file to open:")
    for i, file in enumerate(array_of_file_path, start=1):
        print(f"{i}. {file}")
    print("q. Quit")
    return input("Enter choice: ")


def open_directory(file_path):
    if sys.platform.startswith('darwin'):
        os.system(f"open {file_path}")  # open in finder
    elif sys.platform.startswith('win32'):
        os.system(f"explorer {file_path}")  # open in explorer
    elif sys.platform.startswith('linux'):
        os.system(f"xdg-open {file_path}")  # open in xdg-open
    else:
        print('Unsupported OS')


# after list_files_by_tags, suggest to open the file
def open_list_files_by_tag_result(array_of_file_path, show_path=False):
    if len(array_of_file_path) == 0:
        print("No files found with that tag.")
        return
    while True:
        choice = display_menu(array_of_file_path)
        if choice == 'q':
            break
        else:
            choice = int(choice) - 1
            if show_path:
                return array_of_file_path[int(choice)]
            try:
                # if directory, open in finder or explorer or xdg-open for linux. depending on OS
                if os.path.isdir(array_of_file_path[int(choice)]):
                    open_directory(array_of_file_path[int(choice)])
                    break
                # if file, open in default application depending on OS
                else:
                    os.startfile(array_of_file_path[int(choice)])
                    break
            except IndexError:
                print("Invalid choice, try again.")
                continue
            except ValueError:
                print("Invalid choice, try again.")
                continue


def list_tags_all():
    tags = load_tags()
    all_tags = []
    for file, file_tags in tags.items():
        for tag in file_tags:
            if tag not in all_tags:
                all_tags.append(tag)
    all_tags.sort()
    return all_tags


def list_files_by_tags(tag, exact=False):
    tags = load_tags()
    files = []
    for file, file_tags in tags.items():
        if exact:
            if tag in file_tags:
                files.append(file)
        else:
            for file_tag in file_tags:
                if re.search(tag, file_tag, re.IGNORECASE):
                    files.append(file)
    return files


def search_tags(tag):
    tags = load_tags()
    tag_list = []
    for file, file_tags in tags.items():
        for file_tag in file_tags:
            if re.search(tag, file_tag, re.IGNORECASE):
                tag_list.append(file_tag)
    return tag_list



