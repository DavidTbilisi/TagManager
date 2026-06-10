"""Unit tests for tagmanager/app/gui_handlers.py.

Every handler function is tested in isolation.  All filesystem and service
calls are mocked so the suite runs without a real tag DB or OS shell.
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Make the project root importable regardless of working directory.
# ---------------------------------------------------------------------------
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT not in sys.path:
    sys.path.insert(0, _PROJECT)

import tagmanager.app.gui_handlers as _gh  # noqa: E402  (after sys.path edit)


# ---------------------------------------------------------------------------
# Helpers — use tempdir paths so tests are platform-agnostic.
# normalize_gui_path() resolves paths relative to cwd; using already-absolute
# tempdir paths guarantees mock-store keys always match.
# ---------------------------------------------------------------------------
import tempfile as _tempfile

_TMPDIR = os.path.normpath(_tempfile.gettempdir())
_ALPHA = os.path.join(_TMPDIR, "alpha.txt")
_BETA = os.path.join(_TMPDIR, "beta.py")
_GAMMA = os.path.join(_TMPDIR, "gamma.md")

_STORE = {
    _ALPHA: ["python", "docs"],
    _BETA:  ["python", "tests"],
    _GAMMA: ["docs", "markdown"],
}


# ===========================================================================
# normalize_gui_path / path_allowed / gui_allowed_root
# ===========================================================================


class TestNormalizeGuiPath(unittest.TestCase):
    def test_returns_absolute_path(self):
        p = _gh.normalize_gui_path("/tmp/foo.txt")
        self.assertTrue(os.path.isabs(p))

    def test_relative_path_resolved_against_cwd(self):
        p = _gh.normalize_gui_path("relative/file.txt")
        self.assertTrue(os.path.isabs(p))

    def test_strips_whitespace(self):
        p1 = _gh.normalize_gui_path("  /tmp/foo.txt  ")
        p2 = _gh.normalize_gui_path("/tmp/foo.txt")
        self.assertEqual(p1, p2)

    def test_normalises_dots(self):
        p = _gh.normalize_gui_path("/tmp/../tmp/foo.txt")
        self.assertNotIn("..", p)


class TestPathAllowed(unittest.TestCase):
    # All paths must be absolute and already normalised so that they round-trip
    # through os.path.normpath(os.path.abspath(...)) unchanged.  We derive
    # them from the system temp dir to stay platform-agnostic.

    def test_no_root_allows_anything(self):
        ok, msg = _gh.path_allowed(os.path.join(_TMPDIR, "file.txt"), None)
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_path_inside_root_is_allowed(self):
        path = os.path.join(_TMPDIR, "sub", "file.txt")
        ok, msg = _gh.path_allowed(path, _TMPDIR)
        self.assertTrue(ok)

    def test_exact_root_match_is_allowed(self):
        ok, msg = _gh.path_allowed(_TMPDIR, _TMPDIR)
        self.assertTrue(ok)

    def test_path_outside_root_is_denied(self):
        # A sibling of _TMPDIR that definitely isn't inside it.
        other = os.path.join(os.path.dirname(_TMPDIR), "other_dir")
        ok, msg = _gh.path_allowed(other, _TMPDIR)
        self.assertFalse(ok)
        self.assertIn("outside", msg)

    def test_sibling_with_shared_prefix_is_denied(self):
        # e.g. /tmp-extra should not be allowed when root is /tmp
        sibling = _TMPDIR + "-extra"
        ok, _msg = _gh.path_allowed(sibling, _TMPDIR)
        self.assertFalse(ok)


class TestGuiAllowedRoot(unittest.TestCase):
    def test_empty_env_returns_none(self):
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": ""}, clear=False):
            self.assertIsNone(_gh.gui_allowed_root())

    def test_set_env_returns_abs_path(self):
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": "/some/root"}, clear=False):
            result = _gh.gui_allowed_root()
            self.assertIsNotNone(result)
            self.assertTrue(os.path.isabs(result))


# ===========================================================================
# get_path_tags
# ===========================================================================


class TestGetPathTags(unittest.TestCase):
    @patch("tagmanager.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_known_path_returns_tags(self, _mock):
        result = _gh.get_path_tags(_ALPHA)
        self.assertTrue(result["ok"])
        self.assertIn("python", result["tags"])
        self.assertIn("docs", result["tags"])

    @patch("tagmanager.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_unknown_path_returns_empty_tags(self, _mock):
        result = _gh.get_path_tags(os.path.join(_TMPDIR, "nobody.txt"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["tags"], [])

    @patch("tagmanager.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_path_denied_by_root_returns_error(self, _mock):
        # Restrict to a different directory so _ALPHA is outside the allowed root.
        other_root = os.path.join(_TMPDIR, "restricted")
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": other_root}, clear=False):
            result = _gh.get_path_tags(_ALPHA)
        self.assertFalse(result["ok"])
        self.assertIn("outside", result["error"])

    @patch("tagmanager.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_returns_list_not_other_type(self, _mock):
        result = _gh.get_path_tags(_ALPHA)
        self.assertIsInstance(result["tags"], list)


# ===========================================================================
# post_add_tags
# ===========================================================================


class TestPostAddTags(unittest.TestCase):
    # ------------------------------------------------------------------
    # dry_run
    # ------------------------------------------------------------------

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={"/tmp/f.txt": ["existing"]})
    @patch("os.path.isfile", return_value=True)
    def test_dry_run_returns_preview_without_saving(self, _isfile, _load):
        result = _gh.post_add_tags("/tmp/f.txt", ["newtag"], dry_run=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])
        self.assertIn("tags_before", result)
        self.assertIn("tags_after_preview", result)
        self.assertIn("newtag", result["tags_after_preview"])

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={})
    @patch("tagmanager.app.gui_handlers.add_tags")
    @patch("os.path.isfile", return_value=True)
    def test_dry_run_does_not_call_add_tags(self, _isfile, mock_add, _load):
        _gh.post_add_tags("/tmp/f.txt", ["x"], dry_run=True)
        mock_add.assert_not_called()

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={})
    @patch("os.path.isfile", return_value=True)
    def test_dry_run_no_tags_with_no_auto_returns_error(self, _isfile, _load):
        result = _gh.post_add_tags("/tmp/f.txt", [], dry_run=True, no_auto=True)
        self.assertFalse(result["ok"])

    # ------------------------------------------------------------------
    # real add
    # ------------------------------------------------------------------

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={"/tmp/f.txt": ["prev"]})
    @patch("tagmanager.app.gui_handlers.add_tags", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_real_add_calls_add_tags(self, _isfile, mock_add, _load):
        result = _gh.post_add_tags("/tmp/f.txt", ["python"])
        self.assertTrue(result["ok"])
        mock_add.assert_called_once()

    @patch("tagmanager.app.gui_handlers.add_tags", return_value=False)
    @patch("os.path.isfile", return_value=True)
    def test_add_tags_failure_returns_error(self, _isfile, _mock_add):
        result = _gh.post_add_tags("/tmp/f.txt", ["x"])
        self.assertFalse(result["ok"])
        self.assertIn("error", result)

    @patch("os.path.isfile", return_value=False)
    def test_file_not_on_disk_returns_error(self, _isfile):
        result = _gh.post_add_tags("/nonexistent/file.txt", ["tag"])
        self.assertFalse(result["ok"])
        self.assertIn("error", result)

    def test_empty_path_returns_error(self):
        with patch("os.path.isfile", return_value=False):
            result = _gh.post_add_tags("", ["tag"])
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={})
    def test_no_tags_no_auto_returns_error(self, _load):
        with patch("os.path.isfile", return_value=True):
            result = _gh.post_add_tags("/tmp/f.txt", [], no_auto=True)
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={})
    @patch("tagmanager.app.gui_handlers.add_tags", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_no_content_param_silently_discarded(self, _isfile, _add, _load):
        # The handler accepts no_content but ignores it; should not raise.
        result = _gh.post_add_tags("/tmp/f.txt", ["x"], no_content=True)
        self.assertIn("ok", result)

    def test_root_restriction_blocks_outside_path(self):
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": "/allowed"}, clear=False):
            result = _gh.post_add_tags("/elsewhere/f.txt", ["tag"])
        self.assertFalse(result["ok"])
        self.assertIn("outside", result["error"])


# ===========================================================================
# post_remove
# ===========================================================================


class TestPostRemove(unittest.TestCase):
    # ------------------------------------------------------------------
    # mode = path
    # ------------------------------------------------------------------

    @patch("tagmanager.app.gui_handlers.load_tags",
           return_value={_ALPHA: ["python"]})
    @patch("tagmanager.app.gui_handlers._remove_path", return_value=None)
    def test_mode_path_removes_entry(self, mock_rm, _load):
        result = _gh.post_remove(_ALPHA, "path")
        self.assertTrue(result["ok"])
        mock_rm.assert_called_once()

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={})
    def test_mode_path_not_in_db_returns_error(self, _load):
        result = _gh.post_remove(os.path.join(_TMPDIR, "ghost.txt"), "path")
        self.assertFalse(result["ok"])
        self.assertIn("not in tag database", result["error"])

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={})
    def test_mode_path_dry_run_returns_preview(self, _load):
        result = _gh.post_remove("/data/any.txt", "path", dry_run=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])

    # ------------------------------------------------------------------
    # mode = clear_tags
    # ------------------------------------------------------------------

    @patch("tagmanager.app.gui_handlers.remove_all_tags",
           return_value={"success": True, "message": "cleared"})
    def test_mode_clear_tags_calls_remove_all_tags(self, mock_clear):
        result = _gh.post_remove("/data/alpha.txt", "clear_tags")
        self.assertTrue(result["ok"])
        mock_clear.assert_called_once()

    @patch("tagmanager.app.gui_handlers.remove_all_tags",
           return_value={"success": False, "message": "fail"})
    def test_mode_clear_tags_service_failure(self, _mock):
        result = _gh.post_remove("/data/alpha.txt", "clear_tags")
        self.assertFalse(result["ok"])

    def test_mode_clear_tags_dry_run_returns_preview(self):
        result = _gh.post_remove("/data/alpha.txt", "clear_tags", dry_run=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])

    # ------------------------------------------------------------------
    # mode = one_tag
    # ------------------------------------------------------------------

    @patch("tagmanager.app.gui_handlers.load_tags",
           return_value={_ALPHA: ["python", "docs"]})
    @patch("tagmanager.app.gui_handlers.save_tags", return_value=True)
    def test_mode_one_tag_removes_specific_tag(self, _save, _load):
        result = _gh.post_remove(_ALPHA, "one_tag", tag="docs")
        self.assertTrue(result["ok"])
        self.assertNotIn("docs", result["tags"])
        self.assertIn("python", result["tags"])

    @patch("tagmanager.app.gui_handlers.load_tags",
           return_value={_ALPHA: ["python"]})
    def test_mode_one_tag_tag_not_present_returns_error(self, _load):
        result = _gh.post_remove(_ALPHA, "one_tag", tag="nonexistent")
        self.assertFalse(result["ok"])
        self.assertIn("not present", result["error"])

    def test_mode_one_tag_missing_tag_param_returns_error(self):
        result = _gh.post_remove(_ALPHA, "one_tag", tag=None)
        self.assertFalse(result["ok"])
        self.assertIn("tag required", result["error"])

    @patch("tagmanager.app.gui_handlers.load_tags",
           return_value={_ALPHA: ["python"]})
    def test_mode_one_tag_path_not_in_db_returns_error(self, _load):
        nobody = os.path.join(_TMPDIR, "nobody.txt")
        result = _gh.post_remove(nobody, "one_tag", tag="python")
        self.assertFalse(result["ok"])

    def test_mode_one_tag_dry_run_returns_preview(self):
        result = _gh.post_remove(_ALPHA, "one_tag", tag="docs", dry_run=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])

    @patch("tagmanager.app.gui_handlers.load_tags",
           return_value={_ALPHA: ["python", "docs"]})
    @patch("tagmanager.app.gui_handlers.save_tags", return_value=False)
    def test_mode_one_tag_save_failure_returns_error(self, _save, _load):
        result = _gh.post_remove(_ALPHA, "one_tag", tag="docs")
        self.assertFalse(result["ok"])
        self.assertIn("save failed", result["error"])

    # ------------------------------------------------------------------
    # unknown mode / empty path
    # ------------------------------------------------------------------

    def test_unknown_mode_returns_error(self):
        result = _gh.post_remove("/data/alpha.txt", "invalid_mode")
        self.assertFalse(result["ok"])
        self.assertIn("unknown mode", result["error"])

    def test_root_restriction_blocks_outside_path(self):
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": "/allowed"}, clear=False):
            result = _gh.post_remove("/elsewhere/f.txt", "path")
        self.assertFalse(result["ok"])


# ===========================================================================
# get_all_tags_with_counts
# ===========================================================================


class TestGetAllTagsWithCounts(unittest.TestCase):
    @patch("tagmanager.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_returns_ok_true(self, _mock):
        result = _gh.get_all_tags_with_counts()
        self.assertTrue(result["ok"])

    @patch("tagmanager.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_python_has_count_2(self, _mock):
        result = _gh.get_all_tags_with_counts()
        by_name = {t["tag"]: t["count"] for t in result["tags"]}
        self.assertEqual(by_name["python"], 2)
        self.assertEqual(by_name["docs"], 2)

    @patch("tagmanager.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_sorted_descending_by_count(self, _mock):
        result = _gh.get_all_tags_with_counts()
        counts = [t["count"] for t in result["tags"]]
        self.assertEqual(counts, sorted(counts, reverse=True))

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={})
    def test_empty_store_returns_empty_list(self, _mock):
        result = _gh.get_all_tags_with_counts()
        self.assertTrue(result["ok"])
        self.assertEqual(result["tags"], [])
        self.assertEqual(result["unique"], 0)

    @patch("tagmanager.app.gui_handlers.load_tags", return_value={"/f.txt": "not-a-list"})
    def test_non_list_values_skipped(self, _mock):
        result = _gh.get_all_tags_with_counts()
        self.assertTrue(result["ok"])
        self.assertEqual(result["tags"], [])

    @patch("tagmanager.app.gui_handlers.load_tags", side_effect=RuntimeError("db down"))
    def test_load_error_returns_empty_ok(self, _mock):
        result = _gh.get_all_tags_with_counts()
        self.assertTrue(result["ok"])
        self.assertEqual(result["tags"], [])


# ===========================================================================
# get_stats
# ===========================================================================


class TestGetStats(unittest.TestCase):
    @patch("tagmanager.app.stats.service.get_overall_statistics",
           return_value={"total_files": 5, "unique_tags": 3})
    def test_returns_ok_and_stats(self, _mock):
        result = _gh.get_stats()
        self.assertTrue(result["ok"])
        self.assertEqual(result["total_files"], 5)
        self.assertEqual(result["unique_tags"], 3)

    @patch("tagmanager.app.stats.service.get_overall_statistics",
           side_effect=RuntimeError("db error"))
    def test_service_error_returns_ok_false(self, _mock):
        result = _gh.get_stats()
        self.assertFalse(result["ok"])
        self.assertIn("error", result)


# ===========================================================================
# Alias handlers
# ===========================================================================


class TestGetAliasesHandler(unittest.TestCase):
    @patch("tagmanager.app.alias.service.get_aliases", return_value={"py": "python"})
    def test_returns_ok_and_aliases(self, _mock):
        result = _gh.get_aliases_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(result["aliases"]["py"], "python")

    @patch("tagmanager.app.alias.service.get_aliases", side_effect=RuntimeError("fail"))
    def test_service_error_returns_ok_false(self, _mock):
        result = _gh.get_aliases_handler()
        self.assertFalse(result["ok"])


class TestSetAliasHandler(unittest.TestCase):
    @patch("tagmanager.app.alias.service.add_alias", return_value=True)
    def test_success_returns_ok(self, mock_add):
        result = _gh.set_alias_handler("py", "python")
        self.assertTrue(result["ok"])
        mock_add.assert_called_once_with("py", "python")

    @patch("tagmanager.app.alias.service.add_alias", return_value=False)
    def test_add_alias_false_returns_error(self, _mock):
        result = _gh.set_alias_handler("py", "py")  # alias == canonical
        self.assertFalse(result["ok"])

    def test_empty_alias_returns_error(self):
        result = _gh.set_alias_handler("", "python")
        self.assertFalse(result["ok"])

    def test_empty_canonical_returns_error(self):
        result = _gh.set_alias_handler("py", "")
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.alias.service.add_alias", side_effect=RuntimeError("bad"))
    def test_service_exception_returns_error(self, _mock):
        result = _gh.set_alias_handler("py", "python")
        self.assertFalse(result["ok"])


class TestDeleteAliasHandler(unittest.TestCase):
    @patch("tagmanager.app.alias.service.remove_alias", return_value=True)
    def test_success_returns_ok(self, mock_rm):
        result = _gh.delete_alias_handler("py")
        self.assertTrue(result["ok"])
        mock_rm.assert_called_once_with("py")

    @patch("tagmanager.app.alias.service.remove_alias", return_value=False)
    def test_not_found_returns_error(self, _mock):
        result = _gh.delete_alias_handler("nonexistent")
        self.assertFalse(result["ok"])

    def test_empty_alias_returns_error(self):
        result = _gh.delete_alias_handler("")
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.alias.service.remove_alias", side_effect=RuntimeError("err"))
    def test_service_exception_returns_error(self, _mock):
        result = _gh.delete_alias_handler("py")
        self.assertFalse(result["ok"])


# ===========================================================================
# Preset handlers
# ===========================================================================


class TestGetPresetsHandler(unittest.TestCase):
    @patch("tagmanager.app.preset.service.get_presets",
           return_value={"default": ["python", "docs"]})
    def test_returns_ok_and_presets(self, _mock):
        result = _gh.get_presets_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(result["presets"]["default"], ["python", "docs"])

    @patch("tagmanager.app.preset.service.get_presets", side_effect=RuntimeError("fail"))
    def test_service_error_returns_ok_false(self, _mock):
        result = _gh.get_presets_handler()
        self.assertFalse(result["ok"])


class TestSetPresetHandler(unittest.TestCase):
    @patch("tagmanager.app.preset.service.save_preset", return_value=True)
    def test_success_returns_ok(self, mock_save):
        result = _gh.set_preset_handler("mypre", ["python", "docs"])
        self.assertTrue(result["ok"])
        mock_save.assert_called_once_with("mypre", ["python", "docs"])

    @patch("tagmanager.app.preset.service.save_preset", return_value=False)
    def test_save_rejected_returns_error(self, _mock):
        result = _gh.set_preset_handler("mypre", ["x"])
        self.assertFalse(result["ok"])

    def test_empty_name_returns_error(self):
        result = _gh.set_preset_handler("", ["python"])
        self.assertFalse(result["ok"])

    def test_empty_tags_returns_error(self):
        result = _gh.set_preset_handler("mypre", [])
        self.assertFalse(result["ok"])

    def test_whitespace_only_tags_filtered_returns_error(self):
        result = _gh.set_preset_handler("mypre", ["  ", "  "])
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.preset.service.save_preset", side_effect=RuntimeError("e"))
    def test_service_exception_returns_error(self, _mock):
        result = _gh.set_preset_handler("x", ["t"])
        self.assertFalse(result["ok"])


class TestDeletePresetHandler(unittest.TestCase):
    @patch("tagmanager.app.preset.service.delete_preset", return_value=True)
    def test_success_returns_ok(self, mock_del):
        result = _gh.delete_preset_handler("mypre")
        self.assertTrue(result["ok"])
        mock_del.assert_called_once_with("mypre")

    @patch("tagmanager.app.preset.service.delete_preset", return_value=False)
    def test_not_found_returns_error(self, _mock):
        result = _gh.delete_preset_handler("ghost")
        self.assertFalse(result["ok"])

    def test_empty_name_returns_error(self):
        result = _gh.delete_preset_handler("")
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.preset.service.delete_preset", side_effect=RuntimeError("err"))
    def test_service_exception_returns_error(self, _mock):
        result = _gh.delete_preset_handler("x")
        self.assertFalse(result["ok"])


# ===========================================================================
# Bulk handlers
# ===========================================================================


class TestBulkPreviewHandler(unittest.TestCase):
    @patch("tagmanager.app.bulk.service.find_files_by_pattern",
           return_value=["/tmp/a.py", "/tmp/b.py"])
    def test_returns_ok_and_files(self, mock_find):
        result = _gh.bulk_preview_handler("*.py", ["python"], "/tmp")
        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])
        self.assertEqual(len(result["files"]), 2)
        mock_find.assert_called_once_with("*.py", "/tmp")

    def test_no_tags_returns_error(self):
        result = _gh.bulk_preview_handler("*.py", [])
        self.assertFalse(result["ok"])
        self.assertIn("tag required", result["error"])

    def test_whitespace_only_tags_treated_as_empty(self):
        result = _gh.bulk_preview_handler("*.py", ["   "])
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.bulk.service.find_files_by_pattern", return_value=[])
    def test_empty_pattern_defaults_to_glob_all(self, mock_find):
        _gh.bulk_preview_handler("", ["python"])
        # The handler normalises "" to "**/*"
        mock_find.assert_called_once_with("**/*", ".")

    @patch("tagmanager.app.bulk.service.find_files_by_pattern",
           side_effect=RuntimeError("err"))
    def test_service_exception_returns_error(self, _mock):
        result = _gh.bulk_preview_handler("*.py", ["tag"])
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.bulk.service.find_files_by_pattern",
           return_value=["/allowed/a.py", "/forbidden/b.py"])
    def test_root_restriction_filters_files(self, _mock):
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": "/allowed"}, clear=False):
            result = _gh.bulk_preview_handler("*.py", ["tag"])
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["files"][0], "/allowed/a.py")


class TestBulkApplyHandler(unittest.TestCase):
    @patch("tagmanager.app.bulk.service.bulk_add_tags",
           return_value={"success": True, "tagged_files": ["/tmp/a.py"], "ok": True})
    def test_calls_bulk_add_tags(self, mock_bulk):
        result = _gh.bulk_apply_handler("*.py", ["python"], "/tmp")
        self.assertTrue(result["ok"])
        mock_bulk.assert_called_once_with("*.py", ["python"], "/tmp", dry_run=False)

    def test_no_tags_returns_error(self):
        result = _gh.bulk_apply_handler("*.py", [])
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.bulk.service.bulk_add_tags",
           side_effect=RuntimeError("err"))
    def test_service_exception_returns_error(self, _mock):
        result = _gh.bulk_apply_handler("*.py", ["tag"])
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.bulk.service.find_files_by_pattern",
           return_value=["/allowed/a.py"])
    @patch("tagmanager.app.gui_handlers.add_tags", return_value=True)
    def test_root_restriction_uses_per_file_add(self, mock_add, _mock_find):
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": "/allowed"}, clear=False):
            result = _gh.bulk_apply_handler("*.py", ["python"])
        self.assertTrue(result["ok"])
        mock_add.assert_called_once()

    @patch("tagmanager.app.bulk.service.find_files_by_pattern", return_value=[])
    def test_root_restriction_no_files_returns_error(self, _mock):
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": "/allowed"}, clear=False):
            result = _gh.bulk_apply_handler("*.py", ["python"])
        self.assertFalse(result["ok"])


# ===========================================================================
# open_path_handler
# ===========================================================================


class TestOpenPathHandler(unittest.TestCase):
    def test_empty_path_returns_error(self):
        result = _gh.open_path_handler("")
        self.assertFalse(result["ok"])
        self.assertIn("path required", result["error"])

    @patch("os.path.exists", return_value=False)
    def test_nonexistent_path_returns_error(self, _mock):
        result = _gh.open_path_handler("/nonexistent/file.txt")
        self.assertFalse(result["ok"])
        self.assertTrue(result["error"])  # any non-empty error message accepted

    @patch("os.path.exists", return_value=True)
    def test_unknown_mode_returns_error(self, _mock):
        result = _gh.open_path_handler("/tmp/f.txt", mode="invalid")
        self.assertFalse(result["ok"])
        self.assertIn("unknown mode", result["error"])

    @patch("os.path.exists", return_value=True)
    def test_root_restriction_blocks_outside_path(self, _mock):
        with patch.dict(os.environ, {"TAGMANAGER_GUI_ROOT": "/allowed"}, clear=False):
            result = _gh.open_path_handler("/elsewhere/f.txt", "file")
        self.assertFalse(result["ok"])
        self.assertIn("outside", result["error"])

    @patch("os.path.exists", return_value=True)
    @patch("os.startfile")
    def test_windows_file_mode_calls_startfile(self, mock_startfile, _exists):
        with patch("sys.platform", "win32"):
            result = _gh.open_path_handler(_ALPHA, "file")
        self.assertTrue(result["ok"])
        mock_startfile.assert_called_once()

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.Popen")
    def test_windows_folder_mode_calls_explorer(self, mock_popen, _exists):
        with patch("sys.platform", "win32"):
            result = _gh.open_path_handler(_ALPHA, "folder")
        self.assertTrue(result["ok"])
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "explorer")

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.Popen")
    def test_macos_file_mode_calls_open(self, mock_popen, _exists):
        with patch("sys.platform", "darwin"):
            result = _gh.open_path_handler(_ALPHA, "file")
        self.assertTrue(result["ok"])
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "open")

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.Popen")
    def test_macos_folder_mode_calls_open_r(self, mock_popen, _exists):
        with patch("sys.platform", "darwin"):
            result = _gh.open_path_handler(_ALPHA, "folder")
        self.assertTrue(result["ok"])
        args = mock_popen.call_args[0][0]
        self.assertIn("-R", args)

    @patch("os.path.exists", return_value=True)
    @patch("subprocess.Popen")
    def test_linux_calls_xdg_open(self, mock_popen, _exists):
        with patch("sys.platform", "linux"):
            result = _gh.open_path_handler(_ALPHA, "file")
        self.assertTrue(result["ok"])
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "xdg-open")

    @patch("os.path.exists", return_value=True)
    @patch("os.startfile", side_effect=OSError("permission denied"))
    def test_launch_failure_returns_error(self, _startfile, _exists):
        with patch("sys.platform", "win32"):
            result = _gh.open_path_handler(_ALPHA, "file")
        self.assertFalse(result["ok"])
        self.assertIn("launch failed", result["error"])


# ===========================================================================
# get_tag_stats_handler
# ===========================================================================


class TestGetTagStatsHandler(unittest.TestCase):
    _SAMPLE = {
        "tag": "python",
        "files_with_tag": 2,
        "percentage_of_files": 66.67,
        "files": ["/data/alpha.txt", "/data/beta.py"],
        "co_occurring_tags": [("docs", 1)],
        "file_types": {".txt": 1, ".py": 1},
    }

    @patch("tagmanager.app.stats.service.get_tag_statistics", return_value=_SAMPLE)
    def test_returns_ok_and_tag_info(self, mock_svc):
        result = _gh.get_tag_stats_handler("python")
        self.assertTrue(result["ok"])
        self.assertEqual(result["files_with_tag"], 2)
        mock_svc.assert_called_once_with("python")

    def test_empty_tag_returns_error(self):
        result = _gh.get_tag_stats_handler("")
        self.assertFalse(result["ok"])
        self.assertIn("tag required", result["error"])

    @patch("tagmanager.app.stats.service.get_tag_statistics",
           side_effect=KeyError("unknown"))
    def test_service_error_returns_ok_false(self, _mock):
        result = _gh.get_tag_stats_handler("nonexistent")
        self.assertFalse(result["ok"])


# ===========================================================================
# filter_duplicates_handler
# ===========================================================================


class TestFilterDuplicatesHandler(unittest.TestCase):
    _DUP_RESULT = {
        "duplicates": {
            ("python", "docs"): ["/data/alpha.txt", "/data/clone.txt"],
        },
        "duplicate_groups": 1,
        "duplicate_files_count": 2,
        "total_files": 3,
        "message": "1 group found",
    }

    @patch("tagmanager.app.filter.service.find_duplicate_tags",
           return_value=_DUP_RESULT)
    def test_returns_ok_and_groups(self, _mock):
        result = _gh.filter_duplicates_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["groups"]), 1)

    @patch("tagmanager.app.filter.service.find_duplicate_tags",
           return_value=_DUP_RESULT)
    def test_tuple_keys_converted_to_lists(self, _mock):
        result = _gh.filter_duplicates_handler()
        for grp in result["groups"]:
            self.assertIsInstance(grp["tags"], list)

    @patch("tagmanager.app.filter.service.find_duplicate_tags",
           return_value={"duplicates": {}, "total_files": 0, "message": ""})
    def test_no_duplicates_returns_empty_groups(self, _mock):
        result = _gh.filter_duplicates_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(result["groups"], [])

    @patch("tagmanager.app.filter.service.find_duplicate_tags",
           side_effect=RuntimeError("err"))
    def test_service_exception_returns_ok_false(self, _mock):
        result = _gh.filter_duplicates_handler()
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.filter.service.find_duplicate_tags",
           return_value=_DUP_RESULT)
    def test_group_count_and_file_count_fields_present(self, _mock):
        result = _gh.filter_duplicates_handler()
        self.assertIn("group_count", result)
        self.assertIn("file_count", result)


# ===========================================================================
# filter_orphans_handler
# ===========================================================================


class TestFilterOrphansHandler(unittest.TestCase):
    @patch("tagmanager.app.filter.service.find_orphaned_files",
           return_value={"orphans": ["/missing/a.txt"], "orphan_count": 1, "total_files": 5})
    def test_returns_ok_and_orphans(self, _mock):
        result = _gh.filter_orphans_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertIn("/missing/a.txt", result["orphans"])

    @patch("tagmanager.app.filter.service.find_orphaned_files",
           return_value={"orphans": [], "orphan_count": 0, "total_files": 3})
    def test_no_orphans_returns_empty_list(self, _mock):
        result = _gh.filter_orphans_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(result["orphans"], [])

    @patch("tagmanager.app.filter.service.find_orphaned_files",
           side_effect=RuntimeError("err"))
    def test_service_exception_returns_ok_false(self, _mock):
        result = _gh.filter_orphans_handler()
        self.assertFalse(result["ok"])


# ===========================================================================
# filter_clusters_handler
# ===========================================================================


class TestFilterClustersHandler(unittest.TestCase):
    _CLUSTER_RESULT = {
        "clusters": {
            "python": {"file_count": 10, "percentage": 33.3, "files": ["/a.txt"]},
        },
        "total_files": 30,
    }

    @patch("tagmanager.app.filter.service.find_tag_clusters",
           return_value=_CLUSTER_RESULT)
    def test_returns_ok_and_clusters(self, _mock):
        result = _gh.filter_clusters_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["clusters"]), 1)

    @patch("tagmanager.app.filter.service.find_tag_clusters",
           return_value=_CLUSTER_RESULT)
    def test_custom_min_size_passed_through(self, mock_svc):
        _gh.filter_clusters_handler(min_size=5)
        mock_svc.assert_called_once_with(min_cluster_size=5)

    @patch("tagmanager.app.filter.service.find_tag_clusters",
           return_value=_CLUSTER_RESULT)
    def test_min_size_below_2_clamped_to_2(self, mock_svc):
        _gh.filter_clusters_handler(min_size=0)
        mock_svc.assert_called_once_with(min_cluster_size=2)

    @patch("tagmanager.app.filter.service.find_tag_clusters",
           return_value=_CLUSTER_RESULT)
    def test_invalid_min_size_string_defaults_to_2(self, mock_svc):
        _gh.filter_clusters_handler(min_size="bad")
        mock_svc.assert_called_once_with(min_cluster_size=2)

    @patch("tagmanager.app.filter.service.find_tag_clusters",
           side_effect=RuntimeError("err"))
    def test_service_exception_returns_ok_false(self, _mock):
        result = _gh.filter_clusters_handler()
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.filter.service.find_tag_clusters",
           return_value=_CLUSTER_RESULT)
    def test_cluster_items_have_required_fields(self, _mock):
        result = _gh.filter_clusters_handler()
        for c in result["clusters"]:
            self.assertIn("tag", c)
            self.assertIn("file_count", c)
            self.assertIn("percentage", c)
            self.assertIn("files", c)


# ===========================================================================
# filter_isolated_handler
# ===========================================================================


class TestFilterIsolatedHandler(unittest.TestCase):
    @patch("tagmanager.app.filter.service.find_isolated_files",
           return_value={"isolated_files": ["/lone/wolf.txt"], "total_files": 10})
    def test_returns_ok_and_isolated(self, _mock):
        result = _gh.filter_isolated_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertIn("/lone/wolf.txt", result["isolated"])

    @patch("tagmanager.app.filter.service.find_isolated_files",
           return_value={"isolated_files": [], "total_files": 5})
    def test_no_isolated_returns_empty(self, _mock):
        result = _gh.filter_isolated_handler()
        self.assertTrue(result["ok"])
        self.assertEqual(result["isolated"], [])

    @patch("tagmanager.app.filter.service.find_isolated_files",
           return_value={"isolated_files": [], "total_files": 0})
    def test_custom_max_shared_passed_through(self, mock_svc):
        _gh.filter_isolated_handler(max_shared=3)
        mock_svc.assert_called_once_with(max_shared_tags=3)

    @patch("tagmanager.app.filter.service.find_isolated_files",
           return_value={"isolated_files": [], "total_files": 0})
    def test_negative_max_shared_clamped_to_0(self, mock_svc):
        _gh.filter_isolated_handler(max_shared=-5)
        mock_svc.assert_called_once_with(max_shared_tags=0)

    @patch("tagmanager.app.filter.service.find_isolated_files",
           return_value={"isolated_files": [], "total_files": 0})
    def test_invalid_max_shared_string_defaults_to_1(self, mock_svc):
        _gh.filter_isolated_handler(max_shared="oops")
        mock_svc.assert_called_once_with(max_shared_tags=1)

    @patch("tagmanager.app.filter.service.find_isolated_files",
           side_effect=RuntimeError("err"))
    def test_service_exception_returns_ok_false(self, _mock):
        result = _gh.filter_isolated_handler()
        self.assertFalse(result["ok"])


# ===========================================================================
# clean_handler
# ===========================================================================


class TestCleanHandler(unittest.TestCase):
    @patch("tagmanager.app.move.service.clean_missing",
           return_value={"success": True, "dry_run": True,
                         "missing": ["/gone/a.txt"], "count": 1, "message": "1 found"})
    def test_dry_run_true_passed_to_service(self, mock_svc):
        result = _gh.clean_handler(dry_run=True)
        self.assertTrue(result["ok"])
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["count"], 1)
        mock_svc.assert_called_once_with(dry_run=True)

    @patch("tagmanager.app.move.service.clean_missing",
           return_value={"success": True, "dry_run": False,
                         "missing": [], "count": 0, "message": "done"})
    def test_dry_run_false_passed_to_service(self, mock_svc):
        result = _gh.clean_handler(dry_run=False)
        self.assertTrue(result["ok"])
        self.assertFalse(result["dry_run"])
        mock_svc.assert_called_once_with(dry_run=False)

    @patch("tagmanager.app.move.service.clean_missing",
           return_value={"success": True, "dry_run": True,
                         "missing": ["/x.txt", "/y.txt"], "count": 2, "message": ""})
    def test_missing_list_returned_correctly(self, _mock):
        result = _gh.clean_handler(dry_run=True)
        self.assertEqual(len(result["missing"]), 2)

    @patch("tagmanager.app.move.service.clean_missing",
           return_value={"success": False, "dry_run": False,
                         "missing": [], "count": 0, "message": ""})
    def test_service_success_false_maps_to_ok_false(self, _mock):
        result = _gh.clean_handler(dry_run=False)
        self.assertFalse(result["ok"])

    @patch("tagmanager.app.move.service.clean_missing",
           side_effect=RuntimeError("db locked"))
    def test_service_exception_returns_ok_false(self, _mock):
        result = _gh.clean_handler()
        self.assertFalse(result["ok"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
