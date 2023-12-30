import os
from app.helpers import load_tags, save_tags

def add_tags(file_path, tags):
    # Check if the file exists
    file_path = os.path.abspath(os.path.join(os.getcwd(),file_path))
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return
    

    existing_tags = load_tags()
    existing_tags[file_path] = list(set(existing_tags.get(file_path, [])).union(set(tags)))
    save_tags(existing_tags)
    try:
        print(f"Tags added to '{file_path}'\n".encode('utf-8', 'replace').decode('utf-8'))
    except UnicodeEncodeError as e:
        print("Error while printing:", e)