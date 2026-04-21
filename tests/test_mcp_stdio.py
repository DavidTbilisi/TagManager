#!/usr/bin/env python3
"""MCP stdio server (optional ``mcp`` dependency)."""

import asyncio
import json
import os
import shutil
import sys
import tempfile
import unittest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def _has_mcp() -> bool:
    try:
        import mcp  # noqa: F401
        return True
    except ImportError:
        return False


class TestMcpTagsForPath(unittest.TestCase):
    """Helpers that do not require the MCP SDK."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tags_file = os.path.join(self.test_dir, "test_tags.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_tags_for_path_no_print(self):
        from unittest.mock import patch

        from tagmanager.mcp_stdio import _tags_for_path

        inner = os.path.join(self.test_dir, "inner", "foo.txt")
        os.makedirs(os.path.dirname(inner), exist_ok=True)
        open(inner, "w", encoding="utf-8").write("x")
        key = os.path.abspath(inner)

        with open(self.test_tags_file, "w", encoding="utf-8") as f:
            json.dump({key: ["a", "b"]}, f)

        with patch(
            "tagmanager.app.helpers.get_tag_file_path", return_value=self.test_tags_file
        ):
            with patch("os.getcwd", return_value=os.path.dirname(inner)):
                out = _tags_for_path("foo.txt")
        self.assertEqual(out, ["a", "b"])


@unittest.skipUnless(_has_mcp(), "mcp package not installed")
class TestMcpServerBuild(unittest.TestCase):
    def test_list_tools(self):
        from tagmanager.mcp_stdio import _build_mcp

        async def _run():
            m = _build_mcp()
            tools = await m.list_tools()
            names = sorted(t.name for t in tools)
            self.assertIn("list_distinct_tags", names)
            self.assertIn("search_files_by_tag_list", names)
            self.assertIn("add_tags_to_file", names)

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
