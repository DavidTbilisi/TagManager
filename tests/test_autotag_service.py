import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock


class TestAutotagService(unittest.TestCase):

    def _make_mgr(self, enabled=True, overrides=None, recursive_skip=None):
        mgr = MagicMock()

        def get_side(key, default=None):
            if key == "autotag.enabled":
                return enabled
            if key == "autotag.extension_tags":
                return overrides or {}
            if key == "autotag.recursive_skip_dirs":
                return recursive_skip if recursive_skip is not None else []
            if key == "files.follow_symlinks":
                return False
            if key == "files.include_hidden":
                return False
            return default

        mgr.get.side_effect = get_side
        return mgr

    # --- suggest_tags_for_file ---

    def test_python_file(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("script.py")
        self.assertIn("python", result)

    def test_javascript_file(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("app.js")
        self.assertIn("javascript", result)

    def test_typescript_file(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("app.ts")
        self.assertIn("typescript", result)

    def test_markdown_file(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("README.md")
        self.assertIn("markdown", result)
        self.assertIn("docs", result)

    def test_unknown_extension_returns_empty(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("file.xyz123")
        self.assertEqual(result, [])

    def test_disabled_returns_empty(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr(enabled=False)):
            result = suggest_tags_for_file("script.py")
        self.assertEqual(result, [])

    def test_case_insensitive_extension(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("SCRIPT.PY")
        self.assertIn("python", result)

    def test_config_override(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        overrides = {".py": ["python", "scripting", "backend"]}
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr(overrides=overrides)):
            result = suggest_tags_for_file("app.py")
        self.assertIn("scripting", result)
        self.assertIn("backend", result)

    def test_image_files(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        mgr = self._make_mgr()
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            for ext in [".jpg", ".jpeg", ".png", ".gif"]:
                result = suggest_tags_for_file(f"photo{ext}")
                self.assertIn("image", result, f"Expected 'image' for {ext}")

    def test_video_files(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        mgr = self._make_mgr()
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            for ext in [".mp4", ".mov"]:
                result = suggest_tags_for_file(f"clip{ext}")
                self.assertIn("video", result)

    def test_shell_script(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("deploy.sh")
        self.assertIn("shell", result)
        self.assertIn("script", result)

    def test_pdf_document(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("report.pdf")
        self.assertIn("pdf", result)
        self.assertIn("document", result)

    def test_no_extension(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            result = suggest_tags_for_file("Makefile")
        self.assertEqual(result, [])

    # --- get_extension_tags_map ---

    def test_map_contains_defaults(self):
        from tagmanager.app.autotag.service import get_extension_tags_map
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr()):
            mapping = get_extension_tags_map()
        self.assertIn(".py", mapping)
        self.assertIn(".js", mapping)
        self.assertIn(".md", mapping)

    def test_map_overrides_merged(self):
        from tagmanager.app.autotag.service import get_extension_tags_map
        overrides = {".xyz": ["custom"]}
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=self._make_mgr(overrides=overrides)):
            mapping = get_extension_tags_map()
        self.assertIn(".xyz", mapping)
        self.assertEqual(mapping[".xyz"], ["custom"])

    # --- set_extension_tags ---

    def test_set_extension_tags(self):
        from tagmanager.app.autotag.service import set_extension_tags
        mgr = self._make_mgr()
        captured = {}
        def set_raw(key, value):
            captured[key] = value
        mgr.set_raw.side_effect = set_raw
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            set_extension_tags(".custom", ["mytag"])
        self.assertIn("autotag", captured)
        self.assertEqual(captured["autotag"]["extension_tags"][".custom"], ["mytag"])

    def test_set_extension_adds_dot(self):
        from tagmanager.app.autotag.service import set_extension_tags
        mgr = self._make_mgr()
        captured = {}
        mgr.set_raw.side_effect = lambda k, v: captured.update({k: v})
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            set_extension_tags("py", ["python"])
        ext_tags = captured["autotag"]["extension_tags"]
        self.assertIn(".py", ext_tags)

    # --- recursive walk ---

    def test_get_recursive_skip_dir_names_extra(self):
        from tagmanager.app.autotag.service import get_recursive_skip_dir_names

        with patch(
            "tagmanager.app.autotag.service.get_config_manager",
            return_value=self._make_mgr(recursive_skip=["vendor"]),
        ):
            names = get_recursive_skip_dir_names()
        self.assertIn("node_modules", names)
        self.assertIn("vendor", names)

    def test_iter_files_recursive_skips_ignored_dirs(self):
        from tagmanager.app.autotag.service import iter_files_recursive

        root = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(root, "src"))
            os.makedirs(os.path.join(root, "node_modules", "pkg"))
            open(os.path.join(root, "src", "a.py"), "w", encoding="utf-8").close()
            open(os.path.join(root, "node_modules", "pkg", "b.js"), "w", encoding="utf-8").close()
            with patch(
                "tagmanager.app.autotag.service.get_config_manager",
                return_value=self._make_mgr(),
            ):
                paths = iter_files_recursive(root)
            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].endswith(f"src{os.sep}a.py"))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_iter_files_recursive_not_a_dir(self):
        from tagmanager.app.autotag.service import iter_files_recursive

        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            self.assertEqual(iter_files_recursive(path), [])
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
