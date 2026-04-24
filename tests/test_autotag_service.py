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

    def _make_mgr_content(
        self,
        rules,
        *,
        content_enabled=True,
        autotag_enabled=True,
        content_use_defaults=True,
    ):
        mgr = MagicMock()

        def get_side(key, default=None):
            if key == "autotag.enabled":
                return autotag_enabled
            if key == "autotag.extension_tags":
                return {}
            if key == "autotag.content_enabled":
                return content_enabled
            if key == "autotag.content_rules":
                return rules
            if key == "autotag.content_use_defaults":
                return content_use_defaults
            if key == "autotag.content_max_bytes":
                return 65536
            if key == "autotag.recursive_skip_dirs":
                return []
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

    def test_set_extension_tags_preserves_content_config(self):
        from tagmanager.app.autotag.service import set_extension_tags

        base = {
            "enabled": True,
            "content_enabled": True,
            "content_rules": [{"contains": "pytest", "tags": ["testing"]}],
            "extension_tags": {".js": ["javascript"]},
        }
        mgr = MagicMock()
        mgr.get.side_effect = lambda key, default=None: dict(base) if key == "autotag" else default
        captured: dict = {}
        mgr.set_raw.side_effect = lambda k, v: captured.update({k: v})
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            set_extension_tags(".ts", ["typescript"])
        out = captured["autotag"]
        self.assertTrue(out["content_enabled"])
        self.assertEqual(len(out["content_rules"]), 1)
        self.assertEqual(out["extension_tags"][".ts"], ["typescript"])
        self.assertEqual(out["extension_tags"][".js"], ["javascript"])

    # --- content rules ---

    def test_suggest_tags_merges_extension_and_content(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "app.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write("import django\n")
            mgr = self._make_mgr_content([{"contains": "django", "tags": ["django-app"]}])
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertIn("python", tags)
            self.assertIn("django-app", tags)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_content_regex_rule(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "x.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write("from fastapi import APIRouter\n")
            mgr = self._make_mgr_content(
                [{"pattern": r"\bfastapi\b", "tags": ["fastapi"], "case_sensitive": False}]
            )
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertIn("fastapi", tags)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_include_content_false_skips_content_scan(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        with patch(
            "tagmanager.app.autotag.service.get_config_manager",
            return_value=self._make_mgr_content([{"contains": "unique", "tags": ["hit"]}]),
        ):
            with patch("tagmanager.app.autotag.service.suggest_tags_from_content") as mock_c:
                tags = suggest_tags_for_file("anything.py", include_content=False)
            mock_c.assert_not_called()
        self.assertIn("python", tags)

    def test_content_disabled_no_extra_tags(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "app.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write("import django\n")
            mgr = self._make_mgr_content(
                [{"contains": "django", "tags": ["django-app"]}], content_enabled=False
            )
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertIn("python", tags)
            self.assertNotIn("django-app", tags)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_default_content_rules_without_user_rules(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "test_x.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write("import pytest\n")
            mgr = self._make_mgr_content([], content_enabled=True)
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertIn("python", tags)
            self.assertIn("pytest", tags)
            self.assertIn("testing", tags)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_get_merged_content_rules_defaults_plus_user(self):
        from tagmanager.app.autotag.service import (
            DEFAULT_CONTENT_RULES,
            get_merged_content_rules,
        )

        mgr = self._make_mgr_content(
            [{"contains": "unique_xyz_123", "tags": ["custom"]}],
            content_enabled=True,
        )
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            merged = get_merged_content_rules()
        self.assertGreaterEqual(len(merged), len(DEFAULT_CONTENT_RULES) + 1)
        self.assertIs(merged[0], DEFAULT_CONTENT_RULES[0])
        self.assertEqual(merged[-1]["contains"], "unique_xyz_123")

    def test_content_pattern_groups_empty_list_skips_builtin_defaults(self):
        from tagmanager.app.autotag.service import get_merged_content_rules

        mgr = MagicMock()

        def get_side(key, default=None):
            if key == "autotag.content_rules":
                return [{"contains": "x", "tags": ["custom"]}]
            if key == "autotag.content_use_defaults":
                return True
            if key == "autotag.content_pattern_groups":
                return []
            return default

        mgr.get.side_effect = get_side
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            merged = get_merged_content_rules()
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["contains"], "x")

    def test_content_pattern_groups_subset_python_web_only(self):
        from tagmanager.app.autotag.content_rule_groups import CONTENT_RULE_GROUPS
        from tagmanager.app.autotag.service import DEFAULT_CONTENT_RULES, get_merged_content_rules

        mgr = MagicMock()

        def get_side(key, default=None):
            if key == "autotag.content_rules":
                return []
            if key == "autotag.content_use_defaults":
                return True
            if key == "autotag.content_pattern_groups":
                return ["python_web"]
            return default

        mgr.get.side_effect = get_side
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            merged = get_merged_content_rules()
        expected = [r for g in CONTENT_RULE_GROUPS if g["id"] == "python_web" for r in g["rules"]]
        self.assertEqual(len(merged), len(expected))
        self.assertIs(merged[0], expected[0])
        self.assertLess(len(merged), len(DEFAULT_CONTENT_RULES))

    def test_content_pattern_groups_unknown_ids_no_builtin_rules(self):
        from tagmanager.app.autotag.service import get_merged_content_rules

        mgr = MagicMock()

        def get_side(key, default=None):
            if key == "autotag.content_rules":
                return []
            if key == "autotag.content_use_defaults":
                return True
            if key == "autotag.content_pattern_groups":
                return ["not_a_real_group_id"]
            return default

        mgr.get.side_effect = get_side
        with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
            merged = get_merged_content_rules()
        self.assertEqual(merged, [])

    def test_content_use_defaults_false_uses_only_user_rules(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "test_x.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write("import pytest\n")
            mgr = self._make_mgr_content(
                [],
                content_enabled=True,
                content_use_defaults=False,
            )
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertIn("python", tags)
            self.assertNotIn("pytest", tags)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_title_pattern_rule(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "RFC 7231 notes.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("plain notes\n")
            mgr = self._make_mgr_content(
                [{"title_pattern": r"(?i)\bRFC\s*\d+", "tags": ["rfc-hit"]}],
                content_use_defaults=False,
            )
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertIn("rfc-hit", tags)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_filename_rule_when_snippet_unreadable(self):
        from tagmanager.app.autotag.service import suggest_tags_from_content

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "README.bin")
            with open(path, "wb") as f:
                f.write(b"\x00\x01binary")
            mgr = self._make_mgr_content(
                [{"filename_pattern": r"(?i)readme", "tags": ["from-filename"]}],
                content_use_defaults=False,
            )
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_from_content(path)
            self.assertEqual(tags, ["from-filename"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_combined_title_and_content_requires_both(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "RFC 9999.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("no magic token here\n")
            rule = {
                "title_pattern": r"(?i)\bRFC\s*\d+",
                "contains": "MAGIC_TOKEN",
                "tags": ["combo"],
            }
            mgr = self._make_mgr_content([rule], content_use_defaults=False)
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertNotIn("combo", tags)
            with open(path, "w", encoding="utf-8") as f:
                f.write("MAGIC_TOKEN\n")
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertIn("combo", tags)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_default_readme_filename_tags(self):
        from tagmanager.app.autotag.service import suggest_tags_for_file

        root = tempfile.mkdtemp()
        try:
            path = os.path.join(root, "README.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Hi\n")
            mgr = self._make_mgr_content([], content_enabled=True)
            with patch("tagmanager.app.autotag.service.get_config_manager", return_value=mgr):
                tags = suggest_tags_for_file(path)
            self.assertIn("readme", tags)
            self.assertIn("docs", tags)
        finally:
            shutil.rmtree(root, ignore_errors=True)

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

    def test_iter_files_max_depth_one_only_immediate_files(self):
        from tagmanager.app.autotag.service import iter_files_recursive

        root = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(root, "sub"))
            open(os.path.join(root, "root.txt"), "w", encoding="utf-8").close()
            open(os.path.join(root, "sub", "inner.txt"), "w", encoding="utf-8").close()
            with patch(
                "tagmanager.app.autotag.service.get_config_manager",
                return_value=self._make_mgr(),
            ):
                paths = iter_files_recursive(root, max_depth=1)
            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].endswith("root.txt"))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_iter_files_max_depth_zero_returns_empty(self):
        from tagmanager.app.autotag.service import iter_files_recursive

        root = tempfile.mkdtemp()
        try:
            open(os.path.join(root, "a.txt"), "w", encoding="utf-8").close()
            with patch(
                "tagmanager.app.autotag.service.get_config_manager",
                return_value=self._make_mgr(),
            ):
                self.assertEqual(iter_files_recursive(root, max_depth=0), [])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_iter_files_max_depth_two_includes_one_subdir(self):
        from tagmanager.app.autotag.service import iter_files_recursive

        root = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(root, "a", "b"))
            open(os.path.join(root, "r.txt"), "w", encoding="utf-8").close()
            open(os.path.join(root, "a", "a1.txt"), "w", encoding="utf-8").close()
            open(os.path.join(root, "a", "b", "deep.txt"), "w", encoding="utf-8").close()
            with patch(
                "tagmanager.app.autotag.service.get_config_manager",
                return_value=self._make_mgr(),
            ):
                paths = iter_files_recursive(root, max_depth=2)
            basenames = {os.path.basename(p) for p in paths}
            self.assertEqual(basenames, {"r.txt", "a1.txt"})
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
