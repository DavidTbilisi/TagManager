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

    def test_default_tag_backup_path_next_to_db(self):
        from tagmanager.app.exportdata.service import default_tag_backup_path

        fake_db = os.path.join(self.tmp, "home", "file_tags.json")
        with patch("tagmanager.app.exportdata.service.get_tag_file_path", return_value=fake_db):
            p = default_tag_backup_path()
        self.assertTrue(p.endswith("file_tags.backup.json"))
        self.assertEqual(os.path.dirname(p), os.path.dirname(os.path.abspath(fake_db)))

    def test_backup_tag_database_delegates_to_export(self):
        from tagmanager.app import exportdata
        from tagmanager.app.exportdata.service import backup_tag_database

        with patch.object(
            exportdata.service, "export_tags_json", return_value={"success": True, "message": "ok"}
        ) as ex:
            with patch.object(exportdata.service, "default_tag_backup_path", return_value="/x/b.json"):
                r = backup_tag_database(None)
        ex.assert_called_once_with("/x/b.json")
        self.assertTrue(r["success"])

    def test_restore_tag_database_delegates_to_import(self):
        from tagmanager.app import exportdata
        from tagmanager.app.exportdata.service import restore_tag_database

        with patch.object(
            exportdata.service, "import_tags", return_value={"success": True, "message": "ok"}
        ) as im:
            with patch.object(exportdata.service, "default_tag_backup_path", return_value="/x/b.json"):
                r = restore_tag_database(None, dry_run=True)
        self.assertTrue(r["success"])
        im.assert_called_once()
        ca = im.call_args
        self.assertEqual(ca[0][0], "/x/b.json")
        self.assertTrue(ca[1]["dry_run"])


if __name__ == "__main__":
    unittest.main()
