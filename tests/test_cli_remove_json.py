#!/usr/bin/env python3
"""CLI ``tm remove`` with ``--json``."""

import json
import os
import sys
import unittest
from unittest.mock import patch

from typer.testing import CliRunner

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestCliRemoveJson(unittest.TestCase):
    def test_remove_path_json(self):
        from tagmanager.cli import app

        fake = {
            "success": True,
            "path": "/x/y.txt",
            "removed_tags": ["a"],
            "message": "Removed /x/y.txt from TagManager",
        }
        with patch("tagmanager.cli.remove_path", return_value=fake):
            r = CliRunner().invoke(app, ["--json", "remove", "-p", "/x/y.txt"])
        self.assertEqual(r.exit_code, 0, r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data["success"])
        self.assertEqual(data["removed_tags"], ["a"])

    def test_remove_path_json_failure_exit_code(self):
        from tagmanager.cli import app

        fake = {"success": False, "path": "/nope", "removed_tags": None, "message": "missing"}
        with patch("tagmanager.cli.remove_path", return_value=fake):
            r = CliRunner().invoke(app, ["--json", "remove", "-p", "/nope"])
        self.assertEqual(r.exit_code, 1)
        data = json.loads(r.stdout)
        self.assertFalse(data["success"])

    def test_remove_invalid_json(self):
        from tagmanager.cli import app

        fake = {
            "success": True,
            "message": "Removed 2 invalid path(s) from TagManager",
            "removed_paths": ["/a", "/b"],
            "count": 2,
        }
        with patch("tagmanager.cli.remove_invalid_paths", return_value=fake):
            r = CliRunner().invoke(app, ["--json", "remove", "--invalid"])
        self.assertEqual(r.exit_code, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["count"], 2)

    def test_remove_no_args_json(self):
        from tagmanager.cli import app

        r = CliRunner().invoke(app, ["--json", "remove"])
        self.assertEqual(r.exit_code, 0)
        data = json.loads(r.stdout)
        self.assertFalse(data["success"])


if __name__ == "__main__":
    unittest.main()
