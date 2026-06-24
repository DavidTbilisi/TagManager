#!/usr/bin/env python3
"""Tests for the FileTagger MCP server tool handlers (mcp_server/server.py).

Exercises each tool by awaiting call_tool(name, arguments) against an
isolated tag database, parsing the JSON the handler returns. Closes the
0%-coverage gap on the MCP surface.
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestMcpServerTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import filetagger.mcp_server.server as server
        except Exception as exc:  # mcp extra not installed
            raise unittest.SkipTest(f"mcp not available: {exc}")
        cls.server = server

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.tags_file = os.path.join(self.dir, "tags.json")
        with open(self.tags_file, "w", encoding="utf-8") as f:
            f.write("{}")
        self.f1 = os.path.join(self.dir, "a.txt")
        self.f2 = os.path.join(self.dir, "b.txt")
        for p in (self.f1, self.f2):
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("demo")
        self._patch = patch(
            "filetagger.app.helpers.get_tag_file_path", return_value=self.tags_file
        )
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def _call(self, name, args):
        res = asyncio.run(self.server.call_tool(name, args))
        return json.loads(res[0].text)

    def test_list_tools(self):
        tools = asyncio.run(self.server.list_tools())
        names = {t.name for t in tools}
        self.assertIn("tm_add_tags", names)
        self.assertIn("tm_search", names)
        self.assertGreaterEqual(len(tools), 8)

    def test_add_then_get_roundtrip(self):
        # add_tags also applies extension-based auto-tags (e.g. 'text' for .txt)
        # and tag aliases from config (e.g. py -> python), so assert the plain
        # tag survives and the round-trip returns a populated list.
        self._call("tm_add_tags", {"file_path": self.f1, "tags": ["work", "py"]})
        got = self._call("tm_get_tags", {"file_path": self.f1})
        self.assertIn("work", got["tags"])
        self.assertGreaterEqual(got["count"], 2)

    def test_search_or(self):
        self._call("tm_add_tags", {"file_path": self.f1, "tags": ["work"]})
        self._call("tm_add_tags", {"file_path": self.f2, "tags": ["home"]})
        res = self._call("tm_search", {"tags": ["work"]})
        self.assertEqual(res["count"], 1)
        self.assertTrue(any("a.txt" in p for p in res["files"]))

    def test_remove_tags(self):
        self._call("tm_add_tags", {"file_path": self.f1, "tags": ["a", "b"]})
        res = self._call("tm_remove_tags", {"file_path": self.f1, "tags": ["a"]})
        self.assertTrue(res["success"])
        self.assertNotIn("a", res["tags"])
        self.assertIn("b", res["tags"])

    def test_remove_tags_missing_file_errors(self):
        res = self._call("tm_remove_tags", {"file_path": "/no/such/file.txt", "tags": ["x"]})
        self.assertIn("error", res)

    def test_remove_all_tags(self):
        self._call("tm_add_tags", {"file_path": self.f1, "tags": ["a", "b"]})
        self._call("tm_remove_all_tags", {"file_path": self.f1})
        got = self._call("tm_get_tags", {"file_path": self.f1})
        self.assertEqual(got["tags"], [])

    def test_list_all_and_stats(self):
        self._call("tm_add_tags", {"file_path": self.f1, "tags": ["a", "b"]})
        self._call("tm_add_tags", {"file_path": self.f2, "tags": ["a"]})
        lst = self._call("tm_list_all", {})
        self.assertEqual(lst["total"], 2)
        st = self._call("tm_stats", {})
        self.assertEqual(st["total_files"], 2)
        self.assertTrue(any(t["tag"] == "a" for t in st["top_tags"]))

    def test_tag_directory(self):
        res = self._call("tm_tag_directory", {"directory": self.dir, "tags": ["bulk"]})
        self.assertGreaterEqual(res["tagged"], 2)

    def test_tag_directory_bad_path_errors(self):
        res = self._call("tm_tag_directory", {"directory": "/no/such/dir", "tags": ["x"]})
        self.assertIn("error", res)

    def test_unknown_tool_errors(self):
        res = self._call("tm_does_not_exist", {})
        self.assertIn("error", res)


if __name__ == "__main__":
    unittest.main()
