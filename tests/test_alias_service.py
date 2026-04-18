import unittest
from unittest.mock import patch, MagicMock


class TestAliasService(unittest.TestCase):

    def setUp(self):
        self.patcher = patch("tagmanager.app.alias.service.get_config_manager")
        self.mock_mgr_fn = self.patcher.start()
        self.mock_mgr = MagicMock()
        self.mock_mgr_fn.return_value = self.mock_mgr
        self._aliases = {}
        self.mock_mgr.get.side_effect = lambda key, default=None: (
            self._aliases if key == "aliases" else default
        )
        def set_raw(key, value):
            if key == "aliases":
                self._aliases = value
        self.mock_mgr.set_raw.side_effect = set_raw

    def tearDown(self):
        self.patcher.stop()

    # --- get_aliases ---

    def test_get_aliases_empty(self):
        from tagmanager.app.alias.service import get_aliases
        self._aliases = {}
        self.assertEqual(get_aliases(), {})

    def test_get_aliases_returns_dict(self):
        from tagmanager.app.alias.service import get_aliases
        self._aliases = {"py": "python", "js": "javascript"}
        self.assertEqual(get_aliases(), {"py": "python", "js": "javascript"})

    def test_get_aliases_none_returns_empty(self):
        from tagmanager.app.alias.service import get_aliases
        self.mock_mgr.get.side_effect = lambda key, default=None: None
        self.assertEqual(get_aliases(), {})

    # --- add_alias ---

    def test_add_alias_basic(self):
        from tagmanager.app.alias.service import add_alias
        result = add_alias("py", "python")
        self.assertTrue(result)
        self.assertEqual(self._aliases, {"py": "python"})

    def test_add_alias_lowercases(self):
        from tagmanager.app.alias.service import add_alias
        add_alias("JS", "JavaScript")
        self.assertIn("js", self._aliases)
        self.assertEqual(self._aliases["js"], "javascript")

    def test_add_alias_strips_whitespace(self):
        from tagmanager.app.alias.service import add_alias
        result = add_alias("  py  ", "  python  ")
        self.assertTrue(result)
        self.assertIn("py", self._aliases)

    def test_add_alias_same_returns_false(self):
        from tagmanager.app.alias.service import add_alias
        result = add_alias("python", "python")
        self.assertFalse(result)

    def test_add_alias_empty_alias_returns_false(self):
        from tagmanager.app.alias.service import add_alias
        result = add_alias("", "python")
        self.assertFalse(result)

    def test_add_alias_empty_canonical_returns_false(self):
        from tagmanager.app.alias.service import add_alias
        result = add_alias("py", "")
        self.assertFalse(result)

    def test_add_alias_overwrites_existing(self):
        from tagmanager.app.alias.service import add_alias
        self._aliases = {"py": "python2"}
        add_alias("py", "python")
        self.assertEqual(self._aliases["py"], "python")

    def test_add_multiple_aliases(self):
        from tagmanager.app.alias.service import add_alias
        add_alias("py", "python")
        add_alias("js", "javascript")
        add_alias("ts", "typescript")
        self.assertEqual(len(self._aliases), 3)

    # --- remove_alias ---

    def test_remove_alias_existing(self):
        from tagmanager.app.alias.service import remove_alias
        self._aliases = {"py": "python"}
        result = remove_alias("py")
        self.assertTrue(result)
        self.assertNotIn("py", self._aliases)

    def test_remove_alias_nonexistent_returns_false(self):
        from tagmanager.app.alias.service import remove_alias
        result = remove_alias("nonexistent")
        self.assertFalse(result)

    def test_remove_alias_case_insensitive(self):
        from tagmanager.app.alias.service import remove_alias
        self._aliases = {"py": "python"}
        result = remove_alias("PY")
        self.assertTrue(result)

    # --- clear_aliases ---

    def test_clear_aliases_returns_count(self):
        from tagmanager.app.alias.service import clear_aliases
        self._aliases = {"py": "python", "js": "javascript"}
        count = clear_aliases()
        self.assertEqual(count, 2)
        self.assertEqual(self._aliases, {})

    def test_clear_aliases_empty(self):
        from tagmanager.app.alias.service import clear_aliases
        count = clear_aliases()
        self.assertEqual(count, 0)

    # --- apply_aliases ---

    def test_apply_aliases_resolves(self):
        from tagmanager.app.alias.service import apply_aliases
        self._aliases = {"py": "python", "js": "javascript"}
        result = apply_aliases(["py", "js", "docs"])
        self.assertIn("python", result)
        self.assertIn("javascript", result)
        self.assertIn("docs", result)
        self.assertNotIn("py", result)
        self.assertNotIn("js", result)

    def test_apply_aliases_no_aliases(self):
        from tagmanager.app.alias.service import apply_aliases
        self._aliases = {}
        result = apply_aliases(["python", "javascript"])
        self.assertEqual(result, ["python", "javascript"])

    def test_apply_aliases_deduplicates(self):
        from tagmanager.app.alias.service import apply_aliases
        self._aliases = {"py": "python"}
        result = apply_aliases(["python", "py"])
        self.assertEqual(result.count("python"), 1)

    def test_apply_aliases_preserves_order(self):
        from tagmanager.app.alias.service import apply_aliases
        self._aliases = {"py": "python"}
        result = apply_aliases(["docs", "py", "backend"])
        self.assertEqual(result[0], "docs")
        self.assertEqual(result[1], "python")
        self.assertEqual(result[2], "backend")

    def test_apply_aliases_empty_list(self):
        from tagmanager.app.alias.service import apply_aliases
        self.assertEqual(apply_aliases([]), [])

    def test_apply_aliases_case_insensitive_resolution(self):
        from tagmanager.app.alias.service import apply_aliases
        self._aliases = {"py": "python"}
        result = apply_aliases(["Py"])  # uppercase — still matched (case-insensitive)
        self.assertIn("python", result)
        self.assertNotIn("Py", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
