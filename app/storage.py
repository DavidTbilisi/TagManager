import configparser
import os

config = configparser.ConfigParser()
path = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(path)
config_file = os.path.join(root_dir, "config.ini")
config.read(config_file)


def show_storage_location():
    return config['DEFAULT']['TAG_FILE']


def open_storage_location():
    os.startfile(config['DEFAULT']['TAG_FILE'])