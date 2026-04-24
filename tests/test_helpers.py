#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.helpers
"""

import unittest
import tempfile
import os
import json
import shutil
import sys
from unittest.mock import patch, MagicMock

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestHelpers(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tags_file = os.path.join(self.test_dir, "test_tags.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _patch_path(self, path=None):
        """Return a patcher that makes get_tag_file_path return the given path."""
        target = path if path is not None else self.test_tags_file
        return patch('tagmanager.app.helpers.get_tag_file_path', return_value=target)

    def test_load_tags_existing_file(self):
        """Test loading tags from existing file"""
        from tagmanager.app.helpers import load_tags

        test_data = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        with open(self.test_tags_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        with self._patch_path():
            result = load_tags()

        self.assertEqual(result, test_data)

    def test_load_tags_nonexistent_file(self):
        """Test loading tags from non-existent file"""
        from tagmanager.app.helpers import load_tags

        nonexistent = os.path.join(self.test_dir, "nonexistent.json")
        with self._patch_path(nonexistent):
            result = load_tags()

        self.assertEqual(result, {})

    def test_load_tags_empty_file(self):
        """Test loading tags from empty file"""
        from tagmanager.app.helpers import load_tags

        with open(self.test_tags_file, 'w') as f:
            pass

        with self._patch_path():
            result = load_tags()

        self.assertEqual(result, {})

    def test_load_tags_invalid_json(self):
        """Test loading tags from file with invalid JSON"""
        from tagmanager.app.helpers import load_tags

        with open(self.test_tags_file, 'w') as f:
            f.write("invalid json content {")

        with self._patch_path():
            result = load_tags()

        self.assertEqual(result, {})

    def test_load_tags_unicode_content(self):
        """Test loading tags with Unicode content"""
        from tagmanager.app.helpers import load_tags

        test_data = {
            "/path/file.py": ["python", "测试"],
            "/path/cafe.js": ["javascript", "naïve"]
        }
        with open(self.test_tags_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)

        with self._patch_path():
            result = load_tags()

        self.assertEqual(result, test_data)

    def test_load_tags_large_file(self):
        """Test loading tags from large file"""
        from tagmanager.app.helpers import load_tags

        large_data = {f"/path/file_{i}.py": [f"tag_{j}" for j in range(10)] for i in range(10000)}
        with open(self.test_tags_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f)

        with self._patch_path():
            result = load_tags()

        self.assertEqual(len(result), 10000)

    def test_load_tags_permission_error(self):
        """Test loading tags with permission error"""
        from tagmanager.app.helpers import load_tags

        with open(self.test_tags_file, 'w') as f:
            f.write('{"key": ["val"]}')

        with self._patch_path(), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = load_tags()

        self.assertEqual(result, {})

    def test_save_tags_new_file(self):
        """Test saving tags to new file"""
        from tagmanager.app.helpers import save_tags

        test_data = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        with self._patch_path():
            save_tags(test_data)

        self.assertTrue(os.path.exists(self.test_tags_file))
        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), test_data)

    def test_save_tags_overwrite_existing(self):
        """Test saving tags overwrites existing file"""
        from tagmanager.app.helpers import save_tags

        old_data = {"/old/file.py": ["old", "tags"]}
        with open(self.test_tags_file, 'w', encoding='utf-8') as f:
            json.dump(old_data, f)

        new_data = {"/path/file1.py": ["python", "backend"]}
        with self._patch_path():
            save_tags(new_data)

        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), new_data)

    def test_save_tags_empty_data(self):
        """Test saving empty tags data"""
        from tagmanager.app.helpers import save_tags

        with self._patch_path():
            save_tags({})

        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), {})

    def test_save_tags_unicode_data(self):
        """Test saving tags with Unicode data"""
        from tagmanager.app.helpers import save_tags

        unicode_data = {"/path/file.py": ["python", "测试"]}
        with self._patch_path():
            save_tags(unicode_data)

        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), unicode_data)

    def test_save_tags_special_characters(self):
        """Test saving tags with special characters"""
        from tagmanager.app.helpers import save_tags

        special_data = {
            "/path/file with spaces.py": ["python-3", "web@dev"],
            "/path/file&symbols!.js": ["node.js", "front-end"],
        }
        with self._patch_path():
            save_tags(special_data)

        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), special_data)

    def test_save_tags_large_data(self):
        """Test saving large amount of tags data"""
        from tagmanager.app.helpers import save_tags

        large_data = {f"/path/file_{i}.py": [f"tag_{j}" for j in range(10)] for i in range(10000)}
        with self._patch_path():
            save_tags(large_data)

        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            self.assertEqual(len(json.load(f)), 10000)

    def test_save_tags_permission_error(self):
        """Test saving tags with permission error returns False"""
        from tagmanager.app.helpers import save_tags

        with self._patch_path(), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = save_tags({"/path/file.py": ["python"]})

        self.assertFalse(result)

    def test_save_tags_os_error(self):
        """Test saving tags with OS error returns False"""
        from tagmanager.app.helpers import save_tags

        with self._patch_path(), \
             patch('builtins.open', side_effect=OSError("Disk full")):
            result = save_tags({"/path/file.py": ["python"]})

        self.assertFalse(result)

    def test_save_tags_directory_creation(self):
        """Test saving tags creates directory if it doesn't exist"""
        from tagmanager.app.helpers import save_tags

        nested_file = os.path.join(self.test_dir, "nested", "deep", "tags.json")
        with self._patch_path(nested_file):
            save_tags({"/path/file.py": ["python"]})

        self.assertTrue(os.path.exists(nested_file))
        with open(nested_file, 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), {"/path/file.py": ["python"]})

    def test_save_tags_json_serialization_error(self):
        """Test saving tags with non-serializable data returns False"""
        from tagmanager.app.helpers import save_tags

        non_serializable = {"/path/file.py": [lambda x: x]}
        with self._patch_path():
            result = save_tags(non_serializable)

        self.assertFalse(result)

    def test_load_save_roundtrip(self):
        """Test that load and save operations are consistent"""
        from tagmanager.app.helpers import load_tags, save_tags

        original_data = {
            "/path/file1.py": ["python", "backend", "api"],
            "/path/file2.js": ["javascript", "frontend", "web"],
        }
        with self._patch_path():
            save_tags(original_data)
            loaded_data = load_tags()

        self.assertEqual(loaded_data, original_data)

    def test_concurrent_access_simulation(self):
        """Test atomic write: second save is visible on next load"""
        from tagmanager.app.helpers import load_tags, save_tags

        initial_data = {"/path/file1.py": ["python"]}
        modified_data = {"/path/file2.py": ["javascript"]}

        with self._patch_path():
            save_tags(initial_data)
            loaded_data1 = load_tags()
            save_tags(modified_data)
            loaded_data2 = load_tags()

        self.assertEqual(loaded_data1, initial_data)
        self.assertEqual(loaded_data2, modified_data)

    def test_tag_file_path_configuration(self):
        """Test that get_tag_file_path returns a valid path string"""
        from tagmanager.app.helpers import get_tag_file_path

        tag_file_path = get_tag_file_path()
        self.assertIsInstance(tag_file_path, str)
        self.assertTrue(len(tag_file_path) > 0)

    @patch("tagmanager.app.helpers.get_config", side_effect=RuntimeError("no config"))
    def test_get_tag_file_path_falls_back_to_config_reader(self, mock_get_config):
        from tagmanager.app import helpers

        path = helpers.get_tag_file_path()
        self.assertIsInstance(path, str)
        self.assertTrue(len(path) > 0)

    def test_levenshtein_swaps_when_s1_shorter(self):
        from tagmanager.app.helpers import levenshtein_distance

        self.assertEqual(levenshtein_distance("a", "abc"), 2)

    def test_levenshtein_empty_second_string(self):
        from tagmanager.app.helpers import levenshtein_distance

        self.assertEqual(levenshtein_distance("hello", ""), 5)

    def test_normalized_levenshtein_both_empty(self):
        from tagmanager.app.helpers import normalized_levenshtein_distance

        self.assertEqual(normalized_levenshtein_distance("", ""), 1.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
