from app.helpers import load_tags, save_tags

def remove_tags(file_path, tags):
    existing_tags = load_tags()
    existing_tags[file_path] = list(set(existing_tags.get(file_path, [])) - set(tags))
    if not existing_tags[file_path]:
        del existing_tags[file_path]  # Remove entry if no tags left
    save_tags(existing_tags)