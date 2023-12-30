import configparser
import os

config = configparser.ConfigParser()
config['DEFAULT'] = {
    "TAG_FILE": "~/file_tags.json",
}



config['DEFAULT']['TAG_FILE'] = os.path.expanduser(config['DEFAULT']['TAG_FILE'])

with open('config.ini', 'w') as configfile:
    config.write(configfile)