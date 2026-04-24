#!/usr/bin/env python3
"""Windows context menu helpers (batch writers; install skips on non-Windows)."""

import os
import sys
import tempfile
import unittest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestWinContextMenu(unittest.TestCase):
    @unittest.skipIf(sys.platform == "win32", "install path only validated off Windows")
    def test_install_requires_windows(self):
        from tagmanager import win_context_menu as wcm

        code, msg = wcm.install_context_menu()
        self.assertEqual(code, 1)
        self.assertIn("only supported on windows", msg.lower())

    def test_install_dry_run_returns_plan_on_any_os(self):
        from tagmanager import win_context_menu as wcm

        code, msg = wcm.install_context_menu(dry_run=True)
        self.assertEqual(code, 0, msg)
        self.assertIn("Launcher directory:", msg)
        self.assertIn("HKEY_CURRENT_USER", msg)
        self.assertIn("TagManager", msg)

    def test_write_batch_uses_tilde1(self):
        from pathlib import Path

        import tagmanager.win_context_menu as wcm

        tmp = tempfile.mkdtemp()
        orig_ld = wcm._launcher_dir
        try:

            def _ld():
                return Path(tmp)

            wcm._launcher_dir = _ld  # type: ignore[method-assign]
            p = wcm._write_batch("test_stem", 'path "{path}"')
            text = p.read_text(encoding="utf-8")
            self.assertIn("path", text)
            self.assertIn("%~1", text)
            self.assertTrue(text.upper().startswith("@ECHO OFF"))
        finally:
            wcm._launcher_dir = orig_ld  # type: ignore[method-assign]
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
