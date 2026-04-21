#!/usr/bin/env python3
"""Tests for operation journal and undo."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestJournalService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tags_file = os.path.join(self.test_dir, "test_tags.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _patch_path(self):
        return patch(
            "tagmanager.app.helpers.get_tag_file_path", return_value=self.test_tags_file
        )

    def test_undo_applies_path_inverse(self):
        from tagmanager.app.helpers import load_tags, save_tags
        from tagmanager.app.journal.service import append_entry, undo_last

        with open(self.test_tags_file, "w", encoding="utf-8") as f:
            json.dump({"/f": ["t"]}, f)

        with self._patch_path(), patch.dict(os.environ, {"TAGMANAGER_JOURNAL": "1"}):
            self.assertEqual(load_tags(), {"/f": ["t"]})
            append_entry("add_tags", {"paths": {"/f": None}})
            ok, msg, n = undo_last(1)
            self.assertTrue(ok)
            self.assertEqual(n, 1)
            self.assertEqual(load_tags(), {})

    def test_undo_empty_journal(self):
        from tagmanager.app.journal.service import undo_last

        with self._patch_path(), patch.dict(os.environ, {"TAGMANAGER_JOURNAL": "1"}):
            open(self.test_tags_file, "w", encoding="utf-8").write("{}")
            ok, msg, n = undo_last(1)
            self.assertFalse(ok)
            self.assertEqual(n, 0)


class TestImportDryRun(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tags_file = os.path.join(self.test_dir, "test_tags.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_import_dry_run_does_not_persist(self):
        from tagmanager.app.exportdata.service import import_tags
        from tagmanager.app.helpers import load_tags

        imp = os.path.join(self.test_dir, "in.json")
        with open(imp, "w", encoding="utf-8") as f:
            json.dump({"/new": ["a", "b"]}, f)

        with open(self.test_tags_file, "w", encoding="utf-8") as f:
            json.dump({"/old": ["x"]}, f)

        with patch(
            "tagmanager.app.helpers.get_tag_file_path", return_value=self.test_tags_file
        ):
            r = import_tags(imp, dry_run=True)
            self.assertTrue(r["success"])
            self.assertTrue(r.get("dry_run"))
            self.assertEqual(load_tags(), {"/old": ["x"]})


if __name__ == "__main__":
    unittest.main()
