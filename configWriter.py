import configparser
import os

config = configparser.ConfigParser(allow_no_value=True)
config.optionxform = str  # Make the config keys case-sensitive
config['DEFAULT'] = {
    "TAG_FILE": "~/file_tags.json",
}

config["LIST_ALL"] = {
    "# PATH or FILENAME": None,
    "DISPLAY_FILE_AS": "PATH",
    "MAX_PATH_LENGTH": "70",
}

config['DEFAULT']['TAG_FILE'] = os.path.expanduser(config['DEFAULT']['TAG_FILE'])

with open('config.ini', 'w') as configfile:
    config.write(configfile)
