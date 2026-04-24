#!/usr/bin/env python3
"""Windows context menu: cascade layout, launchers, install/uninstall (mocked on Windows)."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestWinContextMenu(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _patch_launcher(self):
        import tagmanager.win_context_menu as wcm

        def _ld():
            return Path(self.tmp)

        return patch.object(wcm, "_launcher_dir", _ld)

    @unittest.skipIf(sys.platform == "win32", "install path only validated off Windows")
    def test_install_requires_windows(self):
        from tagmanager import win_context_menu as wcm

        code, msg = wcm.install_context_menu()
        self.assertEqual(code, 1)
        self.assertIn("only supported on windows", msg.lower())

    def test_cascade_parent_registry_state_reads_via_winreg_mock(self):
        """Exercise ``cascade_parent_registry_state_for_tests`` without HKCU writes."""
        import winreg

        import tagmanager.win_context_menu as wcm

        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = object()
        fake_ctx.__exit__.return_value = None
        with patch.object(winreg, "OpenKey", return_value=fake_ctx), patch.object(
            winreg,
            "QueryValueEx",
            side_effect=[
                ("", winreg.REG_SZ),
                ("TagManager", winreg.REG_SZ),
            ],
        ):
            d, m = wcm.cascade_parent_registry_state_for_tests(0, r"Software\TagManager\MockProbe")
        self.assertEqual(d, "")
        self.assertEqual(m, "TagManager")

    def test_cascade_parent_registry_state_oserror_returns_none(self):
        import winreg

        import tagmanager.win_context_menu as wcm

        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = object()
        fake_ctx.__exit__.return_value = None
        with patch.object(winreg, "OpenKey", return_value=fake_ctx), patch.object(
            winreg, "QueryValueEx", side_effect=OSError()
        ):
            d, m = wcm.cascade_parent_registry_state_for_tests(0, r"Software\X")
        self.assertIsNone(d)
        self.assertIsNone(m)

    def test_cascade_parent_registry_state_non_string_types_ignored(self):
        import winreg

        import tagmanager.win_context_menu as wcm

        fake_ctx = MagicMock()
        fake_ctx.__enter__.return_value = object()
        fake_ctx.__exit__.return_value = None
        with patch.object(winreg, "OpenKey", return_value=fake_ctx), patch.object(
            winreg,
            "QueryValueEx",
            side_effect=[
                (1, winreg.REG_DWORD),
                (2, winreg.REG_DWORD),
            ],
        ):
            d, m = wcm.cascade_parent_registry_state_for_tests(0, r"Software\X")
        self.assertIsNone(d)
        self.assertIsNone(m)

    def test_install_dry_run_returns_plan_on_any_os(self):
        from tagmanager import win_context_menu as wcm

        code, msg = wcm.install_context_menu(dry_run=True)
        self.assertEqual(code, 0, msg)
        self.assertIn("Launcher directory:", msg)
        self.assertIn("HKEY_CURRENT_USER", msg)
        self.assertIn("TagManager", msg)
        self.assertIn("shell\\TagManager\\ExtendedSubCommandsKey\\Shell\\", msg.replace("/", "\\"))
        self.assertIn("MUIVerb", msg)
        self.assertIn("(Default)=empty", msg)

    def test_shell_root_invalid(self):
        from tagmanager.win_context_menu import shell_root_for_tests

        with self.assertRaises(ValueError):
            shell_root_for_tests("invalid")

    def test_menu_leaves_cover_file_and_dir(self):
        from tagmanager.win_context_menu import menu_leaves_for_tests

        leaves = menu_leaves_for_tests()
        ids = {x.id for x in leaves}
        self.assertIn("AddTags", ids)
        self.assertIn("AddHereOneLevel", ids)
        self.assertTrue(any("file" in x.scopes for x in leaves))
        self.assertTrue(any("dir" in x.scopes for x in leaves))

    def test_leaf_shell_paths(self):
        from tagmanager.win_context_menu import leaf_shell_path_for_tests

        p = leaf_shell_path_for_tests("file", "AddTags")
        self.assertIn(
            r"Classes\*\shell\TagManager\ExtendedSubCommandsKey\Shell\AddTags",
            p.replace("/", "\\"),
        )
        p2 = leaf_shell_path_for_tests("dir", "OpenTerminalHere")
        self.assertIn(
            r"Classes\Directory\shell\TagManager\ExtendedSubCommandsKey\Shell\OpenTerminalHere",
            p2.replace("/", "\\"),
        )

    def test_command_line_uses_percent_star_except_storage(self):
        from tagmanager.win_context_menu import command_line_for_leaf_for_tests, menu_leaves_for_tests

        bat = Path(r"C:\x\y.cmd")
        for leaf in menu_leaves_for_tests():
            cmd = command_line_for_leaf_for_tests(leaf, bat)
            if leaf.id == "Storage":
                self.assertIn("%1", cmd)
            else:
                self.assertIn("%*", cmd)

    def test_write_batch_uses_tilde1(self):
        import tagmanager.win_context_menu as wcm

        with self._patch_launcher():
            p = wcm._write_batch("test_stem", 'path "{path}"')
            text = p.read_text(encoding="utf-8")
            self.assertIn("path", text)
            self.assertIn("%~1", text)
            self.assertTrue(text.upper().startswith("@ECHO OFF"))

    def test_write_add_tags_interactive_contains_loop_and_choice(self):
        import tagmanager.win_context_menu as wcm

        with self._patch_launcher():
            p = wcm._write_add_tags_interactive("stem_add")
            t = p.read_text(encoding="utf-8")
            self.assertIn("--max-depth 1", t)
            self.assertIn("-r --tags", t)
            self.assertIn(":loop", t)
            self.assertIn("choice", t.lower())

    def test_write_remove_multi_accepts_star(self):
        import tagmanager.win_context_menu as wcm

        with self._patch_launcher():
            p = wcm._write_remove_multi("stem_rm")
            t = p.read_text(encoding="utf-8")
            self.assertIn("--all-tags", t)
            self.assertIn("--tag", t)

    def test_write_add_dir_fixed_loops_shift(self):
        import tagmanager.win_context_menu as wcm

        with self._patch_launcher():
            p = wcm._write_add_dir_fixed("stem_d1", "onelevel")
            t = p.read_text(encoding="utf-8")
            self.assertIn("--max-depth 1", t)
            self.assertIn(":loop", t)
            self.assertIn("shift", t)

    def test_write_add_dir_fixed_full_and_dry(self):
        import tagmanager.win_context_menu as wcm

        with self._patch_launcher():
            p_full = wcm._write_add_dir_fixed("stem_full", "full")
            self.assertIn("-r", p_full.read_text(encoding="utf-8"))
            self.assertNotIn("--dry-run", p_full.read_text(encoding="utf-8"))
            p_dry = wcm._write_add_dir_fixed("stem_dry", "fulldry")
            self.assertIn("--dry-run", p_dry.read_text(encoding="utf-8"))

    def test_write_add_dir_fixed_invalid_mode(self):
        import tagmanager.win_context_menu as wcm

        with self._patch_launcher():
            with self.assertRaises(ValueError):
                wcm._write_add_dir_fixed("stem_x", "not-a-mode")

    def test_reg_delete_subtree_missing_opens_key_gracefully(self):
        import tagmanager.win_context_menu as wcm

        with patch("winreg.OpenKey", side_effect=OSError()):
            wcm._reg_delete_subtree(0, r"Software\Missing\TagManager")

    def test_tm_cli_prefix_uses_tm_when_on_path(self):
        import tagmanager.win_context_menu as wcm

        with patch.object(wcm.shutil, "which", return_value=r"C:\bin\tm.exe"):
            self.assertEqual(wcm._tm_cli_prefix(), r'"C:\bin\tm.exe"')

    def test_tm_cli_prefix_falls_back_to_python_module(self):
        import tagmanager.win_context_menu as wcm

        with patch.object(wcm.shutil, "which", return_value=None):
            p = wcm._tm_cli_prefix()
            self.assertIn("-m tagmanager.cli", p)
            self.assertIn(wcm.sys.executable.replace("\\", "/"), p.replace("\\", "/"))

    def test_reg_set_named_and_default_value(self):
        import tagmanager.win_context_menu as wcm
        import winreg

        mock_key = MagicMock()
        with patch.object(winreg, "CreateKeyEx") as ck, patch.object(winreg, "SetValueEx") as sv:
            ck.return_value.__enter__.return_value = mock_key
            wcm._reg_set(0, r"Software\Test", None, "MUIVerb")
            sv.assert_called()
            args0 = sv.call_args[0]
            self.assertEqual(args0[1], "")
            wcm._reg_set(0, r"Software\Test\command", "Icon", "x.ico")
            self.assertEqual(sv.call_args[0][1], "Icon")

    def test_reg_delete_subtree_deletes_children_then_parent(self):
        import tagmanager.win_context_menu as wcm
        import winreg

        key_handles = {}

        def open_key(hkey, subkey, *a, **kw):
            if subkey not in key_handles:
                raise AssertionError(f"unexpected OpenKey {subkey!r}")
            ctx = MagicMock()
            ctx.__enter__.return_value = key_handles[subkey]
            ctx.__exit__.return_value = None
            return ctx

        root = MagicMock()
        child = MagicMock()
        key_handles[r"K\parent"] = root
        key_handles[r"K\parent\child"] = child

        enum_state = {"child": 0}

        def enum_key(k, index):
            self.assertEqual(index, 0)
            if k is root and enum_state["child"] == 0:
                enum_state["child"] = 1
                return "child"
            raise OSError()

        deleted = []

        def delete_key(hkey, subkey):
            deleted.append(subkey)

        with patch.object(winreg, "OpenKey", side_effect=open_key), patch.object(
            winreg, "EnumKey", side_effect=enum_key
        ), patch.object(winreg, "DeleteKey", side_effect=delete_key):
            wcm._reg_delete_subtree(0, r"K\parent")

        self.assertIn(r"K\parent\child", deleted)
        self.assertIn(r"K\parent", deleted)

    def test_reg_delete_subtree_delete_key_failure_swallowed(self):
        import tagmanager.win_context_menu as wcm
        import winreg

        k = MagicMock()
        ctx = MagicMock()
        ctx.__enter__.return_value = k
        ctx.__exit__.return_value = None

        with patch.object(winreg, "OpenKey", return_value=ctx), patch.object(
            winreg, "EnumKey", side_effect=OSError()
        ), patch.object(winreg, "DeleteKey", side_effect=OSError()):
            wcm._reg_delete_subtree(0, r"K\leaf")

    def test_write_leaf_launcher_unknown_add_multi_leaf(self):
        import tagmanager.win_context_menu as wcm

        bad = wcm._Leaf("UnknownAdd", "x", "add_multi", ("dir",))
        with self.assertRaises(ValueError):
            wcm._write_leaf_launcher(bad)

    def test_launcher_dir_for_docs_and_leaf_to_stem(self):
        import tagmanager.win_context_menu as wcm
        from tagmanager.win_context_menu import leaf_to_stem_for_tests, menu_leaves_for_tests

        self.assertEqual(wcm.launcher_dir_for_docs(), str(wcm._launcher_dir()))
        leaf = menu_leaves_for_tests()[0]
        self.assertTrue(leaf_to_stem_for_tests(leaf).startswith("tm_ctx_"))

    @unittest.skipUnless(sys.platform == "win32", "HKCU install")
    def test_install_calls_reg_set(self):
        import tagmanager.win_context_menu as wcm

        with self._patch_launcher(), patch("tagmanager.win_context_menu._reg_set") as m:
            code, msg = wcm.install_context_menu(dry_run=False)
        self.assertEqual(code, 0)
        self.assertGreaterEqual(m.call_count, 8, msg)

    @unittest.skipUnless(sys.platform == "win32", "HKCU install")
    def test_install_parent_uses_empty_default_and_muiverb(self):
        import tagmanager.win_context_menu as wcm

        calls = []

        def capture(hkey, subkey, name, value):
            calls.append((subkey, name, value))

        with self._patch_launcher(), patch.object(wcm, "_reg_set", side_effect=capture):
            code, msg = wcm.install_context_menu(dry_run=False)
        self.assertEqual(code, 0)
        parent_file = r"Software\Classes\*\shell\TagManager"
        parent_dir = r"Software\Classes\Directory\shell\TagManager"
        self.assertIn((parent_file, None, ""), calls)
        self.assertIn((parent_file, "MUIVerb", "TagManager"), calls)
        self.assertIn((parent_dir, None, ""), calls)
        self.assertIn((parent_dir, "MUIVerb", "TagManager"), calls)
        idx_empty_file = calls.index((parent_file, None, ""))
        idx_mui_file = calls.index((parent_file, "MUIVerb", "TagManager"))
        self.assertLess(idx_empty_file, idx_mui_file)

    @unittest.skipUnless(sys.platform == "win32", "HKCU uninstall")
    def test_uninstall_calls_delete_subtree_twice(self):
        import tagmanager.win_context_menu as wcm

        with patch("tagmanager.win_context_menu._reg_delete_subtree") as m:
            code, msg = wcm.uninstall_context_menu()
        self.assertEqual(code, 0)
        self.assertEqual(m.call_count, 2)

    @unittest.skipIf(sys.platform == "win32", "non-Windows branch")
    def test_uninstall_non_windows(self):
        from tagmanager import win_context_menu as wcm

        code, msg = wcm.uninstall_context_menu()
        self.assertEqual(code, 1)
        self.assertIn("windows", msg.lower())

    @unittest.skipUnless(sys.platform == "win32", "patch platform to exercise non-win install branches")
    def test_install_non_windows_message_when_platform_patched(self):
        from tagmanager import win_context_menu as wcm

        with patch.object(wcm.sys, "platform", "linux"):
            code, msg = wcm.install_context_menu(dry_run=False)
        self.assertEqual(code, 1)
        self.assertIn("only supported on windows", msg.lower())

    @unittest.skipUnless(sys.platform == "win32", "patch platform for dry-run note")
    def test_install_dry_run_non_windows_note_when_platform_patched(self):
        from tagmanager import win_context_menu as wcm

        with patch.object(wcm.sys, "platform", "linux"):
            code, msg = wcm.install_context_menu(dry_run=True)
        self.assertEqual(code, 0)
        self.assertIn("Run on Windows to install", msg)

    @unittest.skipUnless(sys.platform == "win32", "patch platform for uninstall guard")
    def test_uninstall_non_windows_when_platform_patched(self):
        from tagmanager import win_context_menu as wcm

        with patch.object(wcm.sys, "platform", "linux"):
            code, msg = wcm.uninstall_context_menu()
        self.assertEqual(code, 1)
        self.assertIn("windows", msg.lower())


if __name__ == "__main__":
    unittest.main()
