import unittest
from unittest.mock import patch


class TestCompletionHelpers(unittest.TestCase):
    """Tests for the shell-completion callback functions in cli.py."""

    def _import_helpers(self):
        from tagmanager.cli import _complete_tags, _complete_preset_names, _complete_alias_names
        return _complete_tags, _complete_preset_names, _complete_alias_names

    # --- _complete_tags ---

    def test_complete_tags_empty_incomplete(self):
        _complete_tags, _, _ = self._import_helpers()
        with patch("tagmanager.cli.list_all_tags", return_value=["python", "javascript", "docs"]):
            result = _complete_tags("")
        self.assertEqual(sorted(result), ["docs", "javascript", "python"])

    def test_complete_tags_prefix_filter(self):
        _complete_tags, _, _ = self._import_helpers()
        with patch("tagmanager.cli.list_all_tags", return_value=["python", "javascript", "pytest"]):
            result = _complete_tags("py")
        self.assertIn("python", result)
        self.assertIn("pytest", result)
        self.assertNotIn("javascript", result)

    def test_complete_tags_case_insensitive(self):
        _complete_tags, _, _ = self._import_helpers()
        with patch("tagmanager.cli.list_all_tags", return_value=["Python", "javascript"]):
            result = _complete_tags("py")
        self.assertIn("Python", result)

    def test_complete_tags_exception_returns_empty(self):
        _complete_tags, _, _ = self._import_helpers()
        with patch("tagmanager.cli.list_all_tags", side_effect=Exception("boom")):
            result = _complete_tags("py")
        self.assertEqual(result, [])

    def test_complete_tags_no_match(self):
        _complete_tags, _, _ = self._import_helpers()
        with patch("tagmanager.cli.list_all_tags", return_value=["python", "javascript"]):
            result = _complete_tags("rust")
        self.assertEqual(result, [])

    # --- _complete_preset_names ---

    def test_complete_preset_names_prefix(self):
        _, _complete_preset_names, _ = self._import_helpers()
        with patch("tagmanager.cli.list_presets", return_value={"work": [], "media": [], "web": []}):
            result = _complete_preset_names("w")
        self.assertIn("work", result)
        self.assertIn("web", result)
        self.assertNotIn("media", result)

    def test_complete_preset_names_empty_returns_all(self):
        _, _complete_preset_names, _ = self._import_helpers()
        with patch("tagmanager.cli.list_presets", return_value={"work": [], "media": []}):
            result = _complete_preset_names("")
        self.assertEqual(sorted(result), ["media", "work"])

    def test_complete_preset_names_exception(self):
        _, _complete_preset_names, _ = self._import_helpers()
        with patch("tagmanager.cli.list_presets", side_effect=RuntimeError):
            result = _complete_preset_names("w")
        self.assertEqual(result, [])

    # --- _complete_alias_names ---

    def test_complete_alias_names_prefix(self):
        _, _, _complete_alias_names = self._import_helpers()
        with patch("tagmanager.cli.get_aliases", return_value={"py": "python", "js": "javascript"}):
            result = _complete_alias_names("p")
        self.assertIn("py", result)
        self.assertNotIn("js", result)

    def test_complete_alias_names_empty_returns_all(self):
        _, _, _complete_alias_names = self._import_helpers()
        with patch("tagmanager.cli.get_aliases", return_value={"py": "python", "js": "javascript"}):
            result = _complete_alias_names("")
        self.assertEqual(sorted(result), ["js", "py"])

    def test_complete_alias_names_exception(self):
        _, _, _complete_alias_names = self._import_helpers()
        with patch("tagmanager.cli.get_aliases", side_effect=Exception):
            result = _complete_alias_names("")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
