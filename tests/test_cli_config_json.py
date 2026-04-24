#!/usr/bin/env python3
"""CLI ``tm config`` with ``--json``."""

import json
import os
import sys
import unittest

from typer.testing import CliRunner

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestCliConfigJson(unittest.TestCase):
    def test_config_categories_json(self):
        from tagmanager.cli import app

        r = CliRunner().invoke(app, ["--json", "config", "categories"])
        self.assertEqual(r.exit_code, 0, r.stdout)
        data = json.loads(r.stdout)
        self.assertTrue(data.get("ok"))
        self.assertIsInstance(data.get("categories"), list)

    def test_config_get_unknown_key_exit_1(self):
        from tagmanager.cli import app

        r = CliRunner().invoke(
            app, ["--json", "config", "get", "not.a.valid.key.tagmanager.test"]
        )
        self.assertEqual(r.exit_code, 1)
        data = json.loads(r.stdout)
        self.assertFalse(data.get("ok"))

    def test_config_reset_requires_yes(self):
        from tagmanager.cli import app

        r = CliRunner().invoke(
            app, ["--json", "config", "reset", "display.emojis"]
        )
        self.assertEqual(r.exit_code, 1)
        data = json.loads(r.stdout)
        self.assertEqual(data.get("error"), "confirmation_required")


if __name__ == "__main__":
    unittest.main()
