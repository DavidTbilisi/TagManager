#!/usr/bin/env python3
"""Thin GUI HTTP routes (stdlib server)."""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from typing import Optional

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestThinGuiHttp(unittest.TestCase):
    def setUp(self):
        self.httpd = None  # type: Optional[ThreadingHTTPServer]
        self.thread = None  # type: Optional[threading.Thread]
        self.port = 0

    def tearDown(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.thread:
            self.thread.join(timeout=3.0)

    def _start(self):
        from tagmanager.app.http_api import _TagManagerHandler

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _TagManagerHandler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(0.05)

    def _get(self, path: str) -> tuple[int, bytes]:
        url = f"http://127.0.0.1:{self.port}{path}"
        with urllib.request.urlopen(url, timeout=2) as r:
            return r.status, r.read()

    def test_gui_page_is_html(self):
        self._start()
        status, body = self._get("/gui")
        self.assertEqual(status, 200)
        self.assertIn(b"<html", body.lower())

    def test_preview_page_is_html(self):
        self._start()
        status, body = self._get("/preview")
        self.assertEqual(status, 200)
        self.assertIn(b"<html", body.lower())
        self.assertIn(b"preview", body.lower())
        self.assertIn(b"Saved tag database", body)
        self.assertIn(b"/api/v1/tags", body)

    def test_path_tags_json(self):
        self._start()
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        tf = os.path.join(self.test_dir, "a.txt")
        open(tf, "w", encoding="utf-8").write("x")
        tag_file = os.path.join(self.test_dir, "tags.json")
        import json as _json

        with open(tag_file, "w", encoding="utf-8") as fh:
            _json.dump({os.path.abspath(tf): ["p"]}, fh)

        from unittest.mock import patch

        with patch("tagmanager.app.helpers.get_tag_file_path", return_value=tag_file):
            status, raw = self._get(
                "/api/v1/gui/path-tags?path=" + urllib.parse.quote(tf, safe="")
            )
        self.assertEqual(status, 200)
        data = json.loads(raw.decode("utf-8"))
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("tags"), ["p"])

    def test_files_tags_alias_matches_path_tags(self):
        self._start()
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        tf = os.path.join(self.test_dir, "a.txt")
        open(tf, "w", encoding="utf-8").write("x")
        tag_file = os.path.join(self.test_dir, "tags.json")
        import json as _json

        with open(tag_file, "w", encoding="utf-8") as fh:
            _json.dump({os.path.abspath(tf): ["p"]}, fh)

        from unittest.mock import patch

        with patch("tagmanager.app.helpers.get_tag_file_path", return_value=tag_file):
            status, raw = self._get(
                "/api/v1/files/tags?path=" + urllib.parse.quote(tf, safe="")
            )
        self.assertEqual(status, 200)
        data = json.loads(raw.decode("utf-8"))
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("tags"), ["p"])

    def test_gui_root_blocks_path(self):
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        inner = os.path.join(self.test_dir, "in")
        os.makedirs(inner, exist_ok=True)
        tf = os.path.join(inner, "b.txt")
        open(tf, "w", encoding="utf-8").write("x")

        from unittest.mock import patch

        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": inner}):
            from tagmanager.app.http_api import _TagManagerHandler

            self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _TagManagerHandler)
            self.port = self.httpd.server_address[1]
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
            time.sleep(0.05)
            # path outside inner/
            bad = os.path.join(self.test_dir, "outside.txt")
            open(bad, "w").write("y")
            url = f"http://127.0.0.1:{self.port}/api/v1/gui/path-tags?path={urllib.parse.quote(bad)}"
            try:
                with urllib.request.urlopen(url, timeout=2) as r:
                    raw = r.read()
            except urllib.error.HTTPError as e:
                raw = e.read()
            data = json.loads(raw.decode("utf-8"))
            self.assertFalse(data.get("ok"))


if __name__ == "__main__":
    unittest.main()
