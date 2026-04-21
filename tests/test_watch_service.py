#!/usr/bin/env python3
"""Tests for tagmanager.app.watch.service"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestTagFileSilently(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tag_file = os.path.join(self.test_dir, "tags.json")
        with open(self.test_tag_file, "w") as f:
            json.dump({}, f)
        self.patcher = patch(
            "tagmanager.app.helpers.get_tag_file_path",
            return_value=self.test_tag_file,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _make_file(self, name="test.py"):
        path = os.path.join(self.test_dir, name)
        with open(path, "w") as f:
            f.write("# test\n")
        return path

    def test_tags_file_with_auto_tag(self):
        from tagmanager.app.watch.service import tag_file_silently
        path = self._make_file("script.py")
        result = tag_file_silently(path, [], None, auto_tag=True)
        self.assertTrue(result["success"])
        self.assertIn("python", result["tags"])

    def test_tags_file_with_extra_tags(self):
        from tagmanager.app.watch.service import tag_file_silently
        path = self._make_file("notes.txt")
        result = tag_file_silently(path, ["important", "work"], None, auto_tag=False)
        self.assertTrue(result["success"])
        self.assertIn("important", result["tags"])
        self.assertIn("work", result["tags"])

    def test_no_tags_no_auto_returns_failure(self):
        from tagmanager.app.watch.service import tag_file_silently
        path = self._make_file("unknown.xyz")
        with patch("tagmanager.app.watch.service.suggest_tags_for_file", return_value=[]):
            result = tag_file_silently(path, [], None, auto_tag=True)
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "no tags to apply")

    def test_nonexistent_file_returns_failure(self):
        from tagmanager.app.watch.service import tag_file_silently
        result = tag_file_silently("/nonexistent/path/file.txt", ["tag"], None, auto_tag=False)
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "file not found")

    def test_tags_are_persisted(self):
        from tagmanager.app.watch.service import tag_file_silently
        from tagmanager.app.helpers import load_tags
        path = self._make_file("doc.md")
        tag_file_silently(path, ["docs", "project"], None, auto_tag=False)
        saved = load_tags()
        abs_path = os.path.abspath(path)
        self.assertIn(abs_path, saved)
        self.assertIn("docs", saved[abs_path])

    def test_preset_tags_applied(self):
        from tagmanager.app.watch.service import tag_file_silently
        path = self._make_file("app.js")
        with patch("tagmanager.app.watch.service._get_preset_safe", return_value=["webproject", "frontend"]):
            result = tag_file_silently(path, [], "webproject", auto_tag=False)
        self.assertTrue(result["success"])
        self.assertIn("webproject", result["tags"])

    def test_duplicate_tags_deduplicated(self):
        from tagmanager.app.watch.service import tag_file_silently
        path = self._make_file("run.py")
        # python will be added by auto-tag AND manually
        result = tag_file_silently(path, ["python", "backend"], None, auto_tag=True)
        self.assertTrue(result["success"])
        self.assertEqual(result["tags"].count("python"), 1)

    def test_incremental_tag_accumulation(self):
        from tagmanager.app.watch.service import tag_file_silently
        path = self._make_file("file.txt")
        tag_file_silently(path, ["first"], None, auto_tag=False)
        tag_file_silently(path, ["second"], None, auto_tag=False)
        from tagmanager.app.helpers import load_tags
        saved = load_tags()
        tags = saved[os.path.abspath(path)]
        self.assertIn("first", tags)
        self.assertIn("second", tags)


class TestWatchEvent(unittest.TestCase):
    def test_event_fields(self):
        from tagmanager.app.watch.service import WatchEvent
        ev = WatchEvent("created", "/some/file.py", True, ["python"], reason="")
        self.assertEqual(ev.kind, "created")
        self.assertEqual(ev.path, "/some/file.py")
        self.assertTrue(ev.success)
        self.assertIn("python", ev.tags)
        self.assertIsNotNone(ev.timestamp)

    def test_moved_event_has_dest(self):
        from tagmanager.app.watch.service import WatchEvent
        ev = WatchEvent("moved", "/old.py", True, dest="/new.py")
        self.assertEqual(ev.dest, "/new.py")


class TestIgnorePattern(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tag_file = os.path.join(self.test_dir, "tags.json")
        with open(self.test_tag_file, "w") as f:
            json.dump({}, f)
        self.patcher = patch(
            "tagmanager.app.helpers.get_tag_file_path",
            return_value=self.test_tag_file,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_handler_ignores_pyc(self):
        """Files matching ignore patterns must not be tagged."""
        from tagmanager.app.watch.service import _TagManagerHandler, WATCHDOG_AVAILABLE
        if not WATCHDOG_AVAILABLE:
            self.skipTest("watchdog not installed")

        events_received = []

        handler = _TagManagerHandler(
            extra_tags=["test"],
            preset_name=None,
            auto_tag=False,
            on_delete_clean=False,
            ignore_patterns=["*.pyc"],
            on_event=events_received.append,
        )

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = "/some/module.pyc"
        handler.on_created(mock_event)

        self.assertEqual(len(events_received), 0)

    def test_handler_does_not_ignore_normal_file(self):
        """Files not matching ignore patterns should fire an event."""
        from tagmanager.app.watch.service import _TagManagerHandler, WATCHDOG_AVAILABLE
        if not WATCHDOG_AVAILABLE:
            self.skipTest("watchdog not installed")

        path = os.path.join(self.test_dir, "new_file.txt")
        with open(path, "w") as f:
            f.write("content")

        events_received = []

        handler = _TagManagerHandler(
            extra_tags=["test"],
            preset_name=None,
            auto_tag=False,
            on_delete_clean=False,
            ignore_patterns=["*.pyc"],
            on_event=events_received.append,
        )

        mock_event = MagicMock()
        mock_event.is_directory = False
        mock_event.src_path = path
        handler.on_created(mock_event)

        self.assertEqual(len(events_received), 1)
        self.assertTrue(events_received[0].success)


class TestStartWatchingNoWatchdog(unittest.TestCase):
    def test_raises_import_error_when_no_watchdog(self):
        from tagmanager.app.watch import service as svc
        original = svc.WATCHDOG_AVAILABLE
        try:
            svc.WATCHDOG_AVAILABLE = False
            with self.assertRaises(ImportError):
                svc.start_watching(
                    path=".",
                    recursive=True,
                    extra_tags=[],
                    preset_name=None,
                    auto_tag=True,
                    on_delete_clean=False,
                    ignore_patterns=[],
                    on_event=lambda e: None,
                )
        finally:
            svc.WATCHDOG_AVAILABLE = original


class TestIntegrationWithWatchdog(unittest.TestCase):
    """Integration test: actually start an observer and create a real file."""

    def setUp(self):
        try:
            import watchdog  # noqa: F401
        except ImportError:
            self.skipTest("watchdog not installed")
        self.test_dir = tempfile.mkdtemp()
        self.test_tag_file = os.path.join(self.test_dir, "tags.json")
        with open(self.test_tag_file, "w") as f:
            json.dump({}, f)
        self.patcher = patch(
            "tagmanager.app.helpers.get_tag_file_path",
            return_value=self.test_tag_file,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_creation_triggers_tagging(self):
        from tagmanager.app.watch.service import start_watching, WatchEvent
        from tagmanager.app.helpers import load_tags

        received: list = []

        observer = start_watching(
            path=self.test_dir,
            recursive=False,
            extra_tags=["watched"],
            preset_name=None,
            auto_tag=False,
            on_delete_clean=False,
            ignore_patterns=[],
            on_event=received.append,
        )

        try:
            new_file = os.path.join(self.test_dir, "watched_file.txt")
            with open(new_file, "w") as f:
                f.write("hello")

            # Give watchdog time to detect the event
            deadline = time.time() + 5.0
            while not received and time.time() < deadline:
                time.sleep(0.1)
        finally:
            observer.stop()
            observer.join()

        self.assertGreater(len(received), 0, "No events received within 5s")
        ev = received[0]
        self.assertEqual(ev.kind, "created")
        self.assertTrue(ev.success)
        self.assertIn("watched", ev.tags)

        saved = load_tags()
        abs_new = os.path.abspath(new_file)
        self.assertIn(abs_new, saved)
        self.assertIn("watched", saved[abs_new])


if __name__ == "__main__":
    unittest.main()
