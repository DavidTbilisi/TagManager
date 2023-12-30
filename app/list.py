import os
from app.helpers import load_tags, save_tags


def list_tags(file_path):
    file_path = os.path.abspath(os.path.join(os.getcwd(),file_path))
    tags = load_tags()
    return tags.get(file_path, [])