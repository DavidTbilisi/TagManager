import os
import sys
from app.helpers import load_tags, save_tags

def display_menu(array_of_file_path):
    print("\n\n")
    for i, file in enumerate(array_of_file_path):
        print(f"{i}. {file}")
    print("q. Quit")
    return input("Enter choice: ")

def open_directory (file_path):
    if sys.platform.startswith('darwin'):
        os.system(f"open {file_path}") # open in finder
    elif sys.platform.startswith('win32'):
        os.system(f"explorer {file_path}") # open in explorer
    elif sys.platform.startswith('linux'):
        os.system(f"xdg-open {file_path}") # open in xdg-open
    else:
        print('Unsupported OS')

# after list_files_by_tags, suggest to open the file
def open_list_files_by_tag_result(array_of_file_path):

    if len(array_of_file_path) == 0:
        print("No files found with that tag.")
        return
    while True:
        choice = display_menu(array_of_file_path)
        if choice == 'q':
            break
        else:
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
    return tags


def list_files_by_tags (tag):
    tags = load_tags()
    files = []
    for file in tags:
        if tag in tags[file]:
            files.append(file)
    return files
