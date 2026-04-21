import subprocess
import sys

from ..helpers import get_tag_file_path


def show_storage_location():
    return get_tag_file_path()


def open_storage_location():
    tag_file = get_tag_file_path()
    if sys.platform.startswith("win"):
        import os
        os.startfile(tag_file)
    elif sys.platform == "darwin":
        subprocess.run(["open", tag_file])
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", tag_file])
    else:
        print("Unsupported OS")
