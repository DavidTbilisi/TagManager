#!/usr/bin/env python3
"""CLI ``tm watch`` with ``--json``."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from typer.testing import CliRunner

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class _DeadObserver:
    def is_alive(self):
        return False

    def stop(self):
        pass

    def join(self, timeout=None):
        pass


class TestCliWatchJson(unittest.TestCase):
    def test_watch_json_no_watchdog(self):
        from tagmanager.cli import app

        with patch("tagmanager.app.watch.handler.WATCHDOG_AVAILABLE", False):
            r = CliRunner().invoke(app, ["--json", "watch", "."])
        self.assertEqual(r.exit_code, 1, r.stdout)
        data = json.loads(r.stdout)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "watchdog_not_installed")

    def test_watch_json_not_a_directory(self):
        from tagmanager.cli import app

        with patch("tagmanager.app.watch.handler.WATCHDOG_AVAILABLE", True):
            r = CliRunner().invoke(app, ["--json", "watch", "___not_a_real_dir_tm_test___"])
        self.assertEqual(r.exit_code, 1)
        data = json.loads(r.stdout)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "not_a_directory")

    def test_watch_json_starts_and_stops_ndjson(self):
        from tagmanager.cli import app

        with tempfile.TemporaryDirectory() as tmp:
            with patch("tagmanager.app.watch.handler.WATCHDOG_AVAILABLE", True):
                with patch(
                    "tagmanager.app.watch.handler.start_watching",
                    return_value=_DeadObserver(),
                ):
                    r = CliRunner().invoke(app, ["--json", "watch", tmp])
        self.assertEqual(r.exit_code, 0, r.stdout)
        lines = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
        self.assertGreaterEqual(len(lines), 2)
        start = json.loads(lines[0])
        self.assertEqual(start.get("event"), "watch_started")
        self.assertTrue(start.get("ok"))
        end = json.loads(lines[-1])
        self.assertEqual(end.get("event"), "watch_stopped")
        self.assertTrue(end.get("ok"))
        self.assertEqual(end.get("events_processed"), 0)


if __name__ == "__main__":
    unittest.main()
