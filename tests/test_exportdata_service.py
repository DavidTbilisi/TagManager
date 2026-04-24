#!/usr/bin/env python3
"""Export path rewriting (relative / strip prefix)."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestExportPathRewrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_export_json_relative_to(self):
        from tagmanager.app.exportdata.service import export_tags_json

        root = os.path.join(self.tmp, "proj")
        inner = os.path.join(root, "src", "a.py")
        fake = {inner: ["t1"]}
        out = os.path.join(self.tmp, "out.json")
        with patch("tagmanager.app.exportdata.service.load_tags", return_value=fake):
            r = export_tags_json(out, relative_to=root)
        self.assertTrue(r["success"], r)
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(list(data.keys()), [os.path.join("src", "a.py")])

    def test_export_json_strip_prefix(self):
        from tagmanager.app.exportdata.service import export_tags_json

        base = os.path.join(self.tmp, "monorepo", "app")
        p = os.path.join(base, "x.py")
        fake = {p: ["z"]}
        out = os.path.join(self.tmp, "strip.json")
        with patch("tagmanager.app.exportdata.service.load_tags", return_value=fake):
            r = export_tags_json(out, strip_prefix=os.path.join(self.tmp, "monorepo"))
        self.assertTrue(r["success"], r)
        with open(out, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(list(data.keys()), [os.path.join("app", "x.py")])

    def test_export_mutually_exclusive_options(self):
        from tagmanager.app.exportdata.service import export_tags_json

        r = export_tags_json(
            os.path.join(self.tmp, "x.json"),
            relative_to="/a",
            strip_prefix="/b",
        )
        self.assertFalse(r["success"])


if __name__ == "__main__":
    unittest.main()
