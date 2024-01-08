import os
from app.helpers import load_tags, save_tags


def list_tags(file_path: str) -> list:
    """
    List tags of a file by file path
    :param file_path: that you want to list tags for
    :return: list of tags for the file
    """
    file_path = os.path.abspath(os.path.join(os.getcwd(), file_path))
    tags = load_tags()
    # find with
    return tags.get(file_path, [])
