#!/usr/bin/env python3
"""CLI ``tm export`` with ``--json``."""

import json
import os
import sys
import unittest
from unittest.mock import patch

from typer.testing import CliRunner

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestCliExportJson(unittest.TestCase):
    def test_export_json_stdout(self):
        from tagmanager.cli import app

        fake = {
            "success": True,
            "path": "/tmp/out.json",
            "file_count": 3,
            "message": "Exported 3 file(s) to /tmp/out.json",
        }
        with patch("tagmanager.cli.export_tags_json", return_value=fake):
            r = CliRunner().invoke(
                app, ["--json", "export", "-o", "out.json", "-f", "json"]
            )
        self.assertEqual(r.exit_code, 0, r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["success"])
        self.assertEqual(data["file_count"], 3)

    def test_export_csv_json_failure(self):
        from tagmanager.cli import app

        fake = {"success": False, "path": "/bad/out.csv", "message": "permission denied"}
        with patch("tagmanager.cli.export_tags_csv", return_value=fake):
            r = CliRunner().invoke(
                app, ["--json", "export", "-o", "out.csv", "-f", "csv"]
            )
        self.assertEqual(r.exit_code, 1)
        data = json.loads(r.stdout)
        self.assertFalse(data["success"])


if __name__ == "__main__":
    unittest.main()
