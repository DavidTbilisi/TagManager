import json
import configparser
import os

config = configparser.ConfigParser()
path = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(path)
config_file = os.path.join(root_dir, "config.ini")
config.read(config_file)

TAG_FILE = config['DEFAULT']['TAG_FILE']


def load_tags():
    if not os.path.exists(TAG_FILE):
        return {}
    with open(TAG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_tags(tags):
    with open(TAG_FILE, "w", encoding="utf-8") as file:
        json.dump(tags, file, indent=4)
