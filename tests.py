import unittest
import configparser
import os
from time import sleep

from app.helpers import load_tags, save_tags
from app.tags.service import open_list_files_by_tag_result, search_files_by_tag, list_all_tags
from app.paths.service import path_tags
from app.add.service import add_tags
from app.remove.service import remove_path
from app.list_all.service import print_list_tags_all_table
from app.storage.service import show_storage_location, open_storage_location

config = configparser.ConfigParser()
path = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(path)
config_file = os.path.join(root_dir, "test_config.ini")
config.read(config_file)


class TestApp(unittest.TestCase):

    # Invalid tests for now
    def test_a_save_tags_none_existing(self):
        save_tags({})
        self.assertEqual(save_tags({"C:\\laragon\\www\\python\\TagManager\\tests\\non_existing_test.txt": ["test1", "test2"]}), True)

    def test_b_save_tags(self):
        self.assertEqual(save_tags({"C:\\laragon\\www\\python\\TagManager\\tests\\test.txt": ["test1", "test2"]}), True)

    def test_c_load_tags(self):
        self.assertEqual(load_tags(), {"C:\\laragon\\www\\python\\TagManager\\tests\\test.txt": ["test1", "test2"]})

    def test_d_list_tags(self):
        self.assertEqual(path_tags("C:\\laragon\\www\\python\\TagManager\\tests\\test.txt"), ['test1', 'test2'])

    def test_e_add_tags(self):
        add_tags("C:\\laragon\\www\\python\\TagManager\\tests\\test.txt", ["test3"])
        path_tags_result = path_tags("C:\\laragon\\www\\python\\TagManager\\tests\\test.txt")
        self.assertEqual( path_tags_result.sort(), ['test2', 'test3', 'test1'].sort())


