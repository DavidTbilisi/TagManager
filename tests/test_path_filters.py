#!/usr/bin/env python3
"""Glob filters for recursive add / auto-tag."""

import os
import sys
import tempfile
import unittest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestPathFilters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_include_basename_glob(self):
        from tagmanager.app.autotag.path_filters import filter_walk_files

        root = self.tmp
        a = os.path.join(root, "a.py")
        b = os.path.join(root, "b.js")
        open(a, "w").close()
        open(b, "w").close()
        files = [a, b]
        out = filter_walk_files(files, root, include_globs=["*.py"])
        self.assertEqual(sorted(out), sorted([os.path.abspath(a)]))

    def test_exclude_wins(self):
        from tagmanager.app.autotag.path_filters import filter_walk_files

        root = self.tmp
        a = os.path.join(root, "a.py")
        open(a, "w").close()
        files = [a]
        out = filter_walk_files(files, root, include_globs=["*.py"], exclude_globs=["*.py"])
        self.assertEqual(out, [])

    def test_auto_exclude_skips_autotag(self):
        from tagmanager.app.autotag.path_filters import should_apply_autotag_for_path

        root = self.tmp
        p = os.path.join(root, "x.log")
        self.assertFalse(
            should_apply_autotag_for_path(
                os.path.abspath(p), root, None, ["*.log"]
            )
        )
        self.assertTrue(
            should_apply_autotag_for_path(
                os.path.abspath(p), root, None, ["*.txt"]
            )
        )

    def test_auto_include_restricts(self):
        from tagmanager.app.autotag.path_filters import should_apply_autotag_for_path

        root = self.tmp
        py = os.path.join(root, "m.py")
        js = os.path.join(root, "n.js")
        self.assertTrue(
            should_apply_autotag_for_path(os.path.abspath(py), root, ["*.py"], None)
        )
        self.assertFalse(
            should_apply_autotag_for_path(os.path.abspath(js), root, ["*.py"], None)
        )


if __name__ == "__main__":
    unittest.main()
