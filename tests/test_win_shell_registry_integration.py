#!/usr/bin/env python3
"""
Windows shell registry integration tests (real winreg — no mocks needed).

Three test classes:

* **TestWinShellRegistryProbe** — always runs on Windows.
  Writes only under ``HKCU\\Software\\TagManager\\TestProbes\\<uuid>`` so
  Explorer never sees the keys.  Verifies the cascade-parent pattern and leaf
  command round-trips using real winreg.

* **TestWinShellExplorerKeysE2E** — runs when ``TAGMANAGER_WIN_SHELL_E2E=1``
  or in CI.  Does a full install → deep registry read-back → uninstall using
  real ``HKCU\\Software\\Classes\\...`` so the CI Windows job proves the
  exact keys Explorer reads are correct.

* **TestWinShellLauncherBatch** — always runs on Windows.
  Writes launchers to a temp dir and verifies their batch content (shift loop,
  choice prompt, etc.) without touching Explorer or the real launcher folder.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

WIN32 = sys.platform == "win32"
RUN_SHELL_E2E = (
    os.environ.get("CI", "").lower() in ("1", "true", "yes")
    or os.environ.get("TAGMANAGER_WIN_SHELL_E2E", "").lower() in ("1", "true", "yes")
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_reg(hkey, subkey: str, name: str = "") -> str:
    import winreg
    with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ) as k:
        val, _ = winreg.QueryValueEx(k, name)
    return val


def _key_exists(hkey, subkey: str) -> bool:
    import winreg
    try:
        with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ):
            return True
    except OSError:
        return False


def _list_subkeys(hkey, subkey: str) -> list:
    import winreg
    keys = []
    with winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ) as k:
        i = 0
        while True:
            try:
                keys.append(winreg.EnumKey(k, i))
                i += 1
            except OSError:
                break
    return keys


# ---------------------------------------------------------------------------
# Class 1: safe probe tests — always run on Windows
# ---------------------------------------------------------------------------

@unittest.skipUnless(WIN32, "Windows winreg only")
class TestWinShellRegistryProbe(unittest.TestCase):
    """Writes only under HKCU\\Software\\TagManager\\TestProbes — Explorer ignores this tree."""

    def setUp(self):
        self._probe = rf"Software\TagManager\TestProbes\{uuid.uuid4()}"

    def tearDown(self):
        import winreg
        from tagmanager.win_context_menu import _reg_delete_subtree
        _reg_delete_subtree(winreg.HKEY_CURRENT_USER, self._probe)

    def test_cascade_parent_empty_default_and_muiverb_roundtrip(self):
        """Parent key must have empty (Default) and MUIVerb — this is the Explorer cascade rule."""
        import winreg
        import tagmanager.win_context_menu as wcm

        parent = rf"{self._probe}\shell\CascadeParent"
        wcm._reg_set(winreg.HKEY_CURRENT_USER, parent, None, "")
        wcm._reg_set(winreg.HKEY_CURRENT_USER, parent, "MUIVerb", "TagManager")

        default = _read_reg(winreg.HKEY_CURRENT_USER, parent, "")
        muiverb = _read_reg(winreg.HKEY_CURRENT_USER, parent, "MUIVerb")

        self.assertEqual(default, "", "parent (Default) must be empty string — not the label")
        self.assertEqual(muiverb, "TagManager", "MUIVerb carries the visible menu label")

    def test_cascade_parent_using_helper(self):
        """Same check via the exported cascade_parent_registry_state_for_tests helper."""
        import winreg
        import tagmanager.win_context_menu as wcm

        parent = rf"{self._probe}\shell\CascadeParent2"
        wcm._reg_set(winreg.HKEY_CURRENT_USER, parent, None, "")
        wcm._reg_set(winreg.HKEY_CURRENT_USER, parent, "MUIVerb", "TagManager")

        d, m = wcm.cascade_parent_registry_state_for_tests(winreg.HKEY_CURRENT_USER, parent)
        self.assertEqual(d, "")
        self.assertEqual(m, "TagManager")

    def test_leaf_default_and_command_roundtrip(self):
        """Leaf (Default) = label text + child \\command key present."""
        import winreg
        import tagmanager.win_context_menu as wcm

        leaf = rf"{self._probe}\shell\Parent\shell\FakeLeaf"
        cmd_val = '"C:\\fake\\tm.cmd" %*'
        wcm._reg_set(winreg.HKEY_CURRENT_USER, leaf, None, "My label")
        wcm._reg_set(winreg.HKEY_CURRENT_USER, leaf + r"\command", None, cmd_val)

        label = _read_reg(winreg.HKEY_CURRENT_USER, leaf, "")
        cmd = _read_reg(winreg.HKEY_CURRENT_USER, leaf + r"\command", "")

        self.assertEqual(label, "My label")
        self.assertEqual(cmd, cmd_val)

    def test_unicode_label_roundtrip(self):
        """Ellipsis (U+2026) and other non-ASCII must survive the REG_SZ write."""
        import winreg
        import tagmanager.win_context_menu as wcm

        leaf = rf"{self._probe}\shell\Parent\shell\UnicodeLeaf"
        label = "Add tags\u2026"   # "Add tags…"
        wcm._reg_set(winreg.HKEY_CURRENT_USER, leaf, None, label)

        stored = _read_reg(winreg.HKEY_CURRENT_USER, leaf, "")
        self.assertEqual(stored, label, "Unicode ellipsis must round-trip via REG_SZ without corruption")
        self.assertEqual(stored[-1], "\u2026")

    def test_delete_subtree_cleans_all_children(self):
        """_reg_delete_subtree must remove parent and all nested keys."""
        import winreg
        from tagmanager.win_context_menu import _reg_delete_subtree, _reg_set

        root = rf"{self._probe}\ToDelete"
        _reg_set(winreg.HKEY_CURRENT_USER, root, None, "root")
        _reg_set(winreg.HKEY_CURRENT_USER, root + r"\child1", None, "c1")
        _reg_set(winreg.HKEY_CURRENT_USER, root + r"\child1\grandchild", None, "gc")
        _reg_set(winreg.HKEY_CURRENT_USER, root + r"\child2", None, "c2")

        _reg_delete_subtree(winreg.HKEY_CURRENT_USER, root)

        self.assertFalse(_key_exists(winreg.HKEY_CURRENT_USER, root))


# ---------------------------------------------------------------------------
# Class 2: launcher batch content tests — always run on Windows
# ---------------------------------------------------------------------------

@unittest.skipUnless(WIN32, "Windows only")
class TestWinShellLauncherBatch(unittest.TestCase):
    """Verify .cmd launcher content without touching real LOCALAPPDATA."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _launcher_dir(self):
        return Path(self.tmp)

    def _patch(self):
        import tagmanager.win_context_menu as wcm
        return patch.object(wcm, "_launcher_dir", self._launcher_dir)

    def test_add_tags_interactive_contains_correct_keys(self):
        import tagmanager.win_context_menu as wcm
        with self._patch():
            p = wcm._write_add_tags_interactive("stem")
        t = p.read_text(encoding="utf-8")
        self.assertIn("set /p TM_TAGS=", t)
        self.assertIn(":loop", t)
        self.assertIn("shift", t)
        self.assertIn("choice /c 12", t)
        self.assertIn("-r --max-depth 1 --tags", t)
        self.assertIn("-r --tags", t)

    def test_remove_multi_star_triggers_all_tags(self):
        import tagmanager.win_context_menu as wcm
        with self._patch():
            p = wcm._write_remove_multi("stem")
        t = p.read_text(encoding="utf-8")
        self.assertIn('if "!TM_TAG!"=="*"', t)
        self.assertIn("--all-tags", t)
        self.assertIn("--tag", t)

    def test_show_multi_loops_all_args(self):
        import tagmanager.win_context_menu as wcm
        with self._patch():
            p = wcm._write_show_multi("stem")
        t = p.read_text(encoding="utf-8")
        self.assertIn(":loop", t)
        self.assertIn("shift", t)
        self.assertIn("pause", t)

    def test_add_dir_fixed_onelevel(self):
        import tagmanager.win_context_menu as wcm
        with self._patch():
            p = wcm._write_add_dir_fixed("stem", "onelevel")
        t = p.read_text(encoding="utf-8")
        self.assertIn("--max-depth 1", t)
        self.assertNotIn("--dry-run", t)

    def test_add_dir_fixed_fulldry(self):
        import tagmanager.win_context_menu as wcm
        with self._patch():
            p = wcm._write_add_dir_fixed("stem", "fulldry")
        t = p.read_text(encoding="utf-8")
        self.assertIn("--dry-run", t)

    def test_all_launchers_written_and_exist(self):
        """Every leaf gets a .cmd file on disk."""
        import tagmanager.win_context_menu as wcm
        with self._patch():
            written = {}
            for leaf in wcm.menu_leaves_for_tests():
                stem = wcm.leaf_to_stem_for_tests(leaf)
                if stem not in written:
                    written[stem] = wcm._write_leaf_launcher(leaf)
        for stem, path in written.items():
            self.assertTrue(path.exists(), f"{stem}.cmd was not created")
            self.assertGreater(path.stat().st_size, 0)

    def test_command_line_quotes_path_and_uses_percent_star(self):
        """Leaf command lines must be quoted and pass all args (%*) except Storage."""
        import tagmanager.win_context_menu as wcm
        fake = Path(r"C:\fake\launcher.cmd")
        for leaf in wcm.menu_leaves_for_tests():
            cmd = wcm.command_line_for_leaf_for_tests(leaf, fake)
            self.assertTrue(cmd.startswith('"'), f"{leaf.id}: cmd must start with quote")
            if leaf.id == "Storage":
                self.assertIn('"%1"', cmd)
            else:
                self.assertIn("%*", cmd)


# ---------------------------------------------------------------------------
# Class 3: full E2E against real HKCU\Software\Classes — gated on env var / CI
# ---------------------------------------------------------------------------

@unittest.skipUnless(WIN32 and RUN_SHELL_E2E, "set TAGMANAGER_WIN_SHELL_E2E=1 or run in CI")
class TestWinShellExplorerKeysE2E(unittest.TestCase):
    """
    Full install → registry read-back → uninstall.

    When this class is green the exact keys Explorer reads are verified:
      • Parent keys: (Default)="" + MUIVerb="TagManager"
      • All expected leaf IDs present under \\shell
      • Each leaf has (Default)=<label> and \\command subkey with quoted .cmd path
      • Unicode labels (ellipsis U+2026) survive the round-trip
      • Uninstall removes the whole tree
    """

    def setUp(self):
        import tagmanager.win_context_menu as wcm
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, True)
        self.addCleanup(wcm.uninstall_context_menu)

        wcm.uninstall_context_menu()

        tmp = self._tmp
        def launcher_dir():
            return Path(tmp)

        with patch.object(wcm, "_launcher_dir", launcher_dir):
            code, msg = wcm.install_context_menu(dry_run=False)
        if code != 0:
            self.fail(f"install_context_menu failed: {msg}")

    def test_parent_file_scope_has_empty_default_and_muiverb(self):
        import winreg
        import tagmanager.win_context_menu as wcm
        parent = wcm.shell_root_for_tests("file")
        d, m = wcm.cascade_parent_registry_state_for_tests(winreg.HKEY_CURRENT_USER, parent)
        self.assertEqual((d or ""), "", f"*\\shell\\TagManager (Default) must be empty; got {d!r}")
        self.assertEqual(m, "TagManager", f"*\\shell\\TagManager MUIVerb; got {m!r}")

    def test_parent_dir_scope_has_empty_default_and_muiverb(self):
        import winreg
        import tagmanager.win_context_menu as wcm
        parent = wcm.shell_root_for_tests("dir")
        d, m = wcm.cascade_parent_registry_state_for_tests(winreg.HKEY_CURRENT_USER, parent)
        self.assertEqual((d or ""), "", f"Directory\\shell\\TagManager (Default) must be empty; got {d!r}")
        self.assertEqual(m, "TagManager", f"Directory\\shell\\TagManager MUIVerb; got {m!r}")

    def test_all_file_scope_leaves_present(self):
        import winreg
        import tagmanager.win_context_menu as wcm
        parent = wcm.shell_root_for_tests("file")
        subkeys = _list_subkeys(
            winreg.HKEY_CURRENT_USER, parent + r"\ExtendedSubCommandsKey\Shell"
        )
        expected = {l.id for l in wcm.menu_leaves_for_tests() if "file" in l.scopes}
        self.assertEqual(set(subkeys), expected,
            f"Unexpected verbs under *\\shell\\TagManager\\ExtendedSubCommandsKey\\Shell")

    def test_all_dir_scope_leaves_present(self):
        import winreg
        import tagmanager.win_context_menu as wcm
        parent = wcm.shell_root_for_tests("dir")
        subkeys = _list_subkeys(
            winreg.HKEY_CURRENT_USER, parent + r"\ExtendedSubCommandsKey\Shell"
        )
        expected = {l.id for l in wcm.menu_leaves_for_tests() if "dir" in l.scopes}
        self.assertEqual(set(subkeys), expected,
            f"Unexpected verbs under Directory\\shell\\TagManager\\ExtendedSubCommandsKey\\Shell")

    def test_extended_subcommands_key_exists_under_each_parent(self):
        """ExtendedSubCommandsKey makes Explorer treat the parent as a popup, not a verb."""
        import winreg
        import tagmanager.win_context_menu as wcm
        for kind in ("file", "dir"):
            parent = wcm.shell_root_for_tests(kind)
            self.assertTrue(
                _key_exists(winreg.HKEY_CURRENT_USER, parent + r"\ExtendedSubCommandsKey"),
                f"{kind}: missing ExtendedSubCommandsKey under {parent}",
            )
            self.assertTrue(
                _key_exists(winreg.HKEY_CURRENT_USER, parent + r"\ExtendedSubCommandsKey\Shell"),
                f"{kind}: missing Shell subkey under ExtendedSubCommandsKey",
            )

    def test_parent_has_no_command_subkey(self):
        """Cascade parent must NOT have a \\command subkey or Explorer will try to invoke it."""
        import winreg
        import tagmanager.win_context_menu as wcm
        for kind in ("file", "dir"):
            parent = wcm.shell_root_for_tests(kind)
            self.assertFalse(
                _key_exists(winreg.HKEY_CURRENT_USER, parent + r"\command"),
                f"{kind}: parent must not have \\command (would override the popup)",
            )

    def test_each_leaf_has_label_and_command_key(self):
        import winreg
        import tagmanager.win_context_menu as wcm
        HKCU = winreg.HKEY_CURRENT_USER
        for leaf in wcm.menu_leaves_for_tests():
            for kind in leaf.scopes:
                sk = wcm.leaf_shell_path_for_tests(kind, leaf.id)
                label = _read_reg(HKCU, sk, "")
                self.assertEqual(label, leaf.menu_text,
                    f"{kind}/{leaf.id}: label mismatch — got {label!r}, want {leaf.menu_text!r}")
                cmd = _read_reg(HKCU, sk + r"\command", "")
                self.assertTrue(cmd.strip().startswith('"'),
                    f"{kind}/{leaf.id}: command must start with quoted path; got {cmd!r}")
                if leaf.id == "Storage":
                    self.assertIn('"%1"', cmd,
                        f"Storage command must use %1; got {cmd!r}")
                else:
                    self.assertIn("%*", cmd,
                        f"{kind}/{leaf.id}: command must use %* for multi-select; got {cmd!r}")

    def test_unicode_ellipsis_label_not_corrupted(self):
        """Confirm Add tags… (U+2026) survived the REG_SZ write on this machine."""
        import winreg
        import tagmanager.win_context_menu as wcm
        HKCU = winreg.HKEY_CURRENT_USER
        sk = wcm.leaf_shell_path_for_tests("file", "AddTags")
        label = _read_reg(HKCU, sk, "")
        self.assertIn("\u2026", label, f"Ellipsis corrupted in AddTags label: {label!r}")

    def test_launcher_cmd_files_on_disk(self):
        """Every leaf's .cmd file must exist in the launcher dir."""
        import tagmanager.win_context_menu as wcm
        seen = set()
        for leaf in wcm.menu_leaves_for_tests():
            stem = wcm.leaf_to_stem_for_tests(leaf)
            if stem in seen:
                continue
            seen.add(stem)
            bat = Path(self._tmp) / f"{stem}.cmd"
            self.assertTrue(bat.exists(), f"Launcher file missing: {bat}")
            self.assertGreater(bat.stat().st_size, 0, f"Launcher file empty: {bat}")

    def test_uninstall_removes_both_parent_keys(self):
        import winreg
        import tagmanager.win_context_menu as wcm
        code, msg = wcm.uninstall_context_menu()
        self.assertEqual(code, 0, msg)
        for kind in ("file", "dir"):
            parent = wcm.shell_root_for_tests(kind)
            self.assertFalse(
                _key_exists(winreg.HKEY_CURRENT_USER, parent),
                f"{kind} parent key still exists after uninstall: {parent}"
            )


if __name__ == "__main__":
    unittest.main()
