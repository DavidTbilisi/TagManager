#!/usr/bin/env python3
"""Tests for list_all.service (truncate + table rendering)."""

import configparser
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestTruncate(unittest.TestCase):
    def test_length_under_four_returns_prefix_only(self):
        from tagmanager.app.list_all.service import truncate

        self.assertEqual(truncate("abcd", 3), "abc")

    def test_long_string_gets_ellipsis(self):
        from tagmanager.app.list_all.service import truncate

        self.assertEqual(truncate("abcdefghij", 6), "abc...")

    def test_short_string_unchanged(self):
        from tagmanager.app.list_all.service import truncate

        self.assertEqual(truncate("hi", 10), "hi")


class TestPrintListTagsAllTable(unittest.TestCase):
    @patch("tagmanager.app.list_all.service.load_tags", return_value={})
    def test_empty_tags_shows_panel(self, mock_load):
        from tagmanager.app.list_all.service import print_list_tags_all_table

        mock_console = MagicMock()
        with patch("tagmanager.app.list_all.service.Console", return_value=mock_console):
            print_list_tags_all_table()
        mock_console.print.assert_called()

    @patch("tagmanager.app.list_all.service.load_tags", return_value={r"C:\p\file.py": ["alpha", "beta"]})
    def test_non_empty_builds_table(self, mock_load):
        from tagmanager.app.list_all.service import print_list_tags_all_table

        cfg = configparser.ConfigParser()
        cfg["LIST_ALL"] = {"DISPLAY_FILE_AS": "PATH", "MAX_PATH_LENGTH": "500"}
        mock_console = MagicMock()
        with patch("tagmanager.app.list_all.service.config", cfg), patch(
            "tagmanager.app.list_all.service.Console", return_value=mock_console
        ):
            print_list_tags_all_table()
        mock_console.print.assert_called()

    @patch("tagmanager.app.list_all.service.load_tags", return_value={r"C:\deep\file.py": ["t"]})
    def test_display_file_as_basename(self, mock_load):
        from tagmanager.app.list_all.service import print_list_tags_all_table

        cfg = configparser.ConfigParser()
        cfg["LIST_ALL"] = {"DISPLAY_FILE_AS": "NAME", "MAX_PATH_LENGTH": "500"}
        mock_console = MagicMock()
        with patch("tagmanager.app.list_all.service.config", cfg), patch(
            "tagmanager.app.list_all.service.Console", return_value=mock_console
        ):
            print_list_tags_all_table()
        mock_console.print.assert_called()


if __name__ == "__main__":
    unittest.main()
