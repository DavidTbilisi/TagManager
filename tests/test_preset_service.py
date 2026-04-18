import unittest
from unittest.mock import patch, MagicMock


class TestPresetService(unittest.TestCase):

    def setUp(self):
        self.patcher = patch("tagmanager.app.preset.service.get_config_manager")
        self.mock_mgr_fn = self.patcher.start()
        self.mock_mgr = MagicMock()
        self.mock_mgr_fn.return_value = self.mock_mgr
        self._presets = {}
        self.mock_mgr.get.side_effect = lambda key, default=None: (
            self._presets if key == "presets" else default
        )
        def set_raw(key, value):
            if key == "presets":
                self._presets = value
        self.mock_mgr.set_raw.side_effect = set_raw

    def tearDown(self):
        self.patcher.stop()

    # --- get_presets / list_presets ---

    def test_get_presets_empty(self):
        from tagmanager.app.preset.service import get_presets
        self.assertEqual(get_presets(), {})

    def test_get_presets_returns_dict(self):
        from tagmanager.app.preset.service import get_presets
        self._presets = {"work": ["python", "backend"]}
        self.assertEqual(get_presets(), {"work": ["python", "backend"]})

    def test_get_presets_none_returns_empty(self):
        from tagmanager.app.preset.service import get_presets
        self.mock_mgr.get.side_effect = lambda k, d=None: None
        self.assertEqual(get_presets(), {})

    def test_list_presets_alias(self):
        from tagmanager.app.preset.service import list_presets
        self._presets = {"a": ["x"]}
        self.assertEqual(list_presets(), {"a": ["x"]})

    # --- save_preset ---

    def test_save_preset_basic(self):
        from tagmanager.app.preset.service import save_preset
        result = save_preset("work", ["python", "backend", "api"])
        self.assertTrue(result)
        self.assertIn("work", self._presets)
        self.assertEqual(self._presets["work"], ["python", "backend", "api"])

    def test_save_preset_lowercases_name(self):
        from tagmanager.app.preset.service import save_preset
        save_preset("WORK", ["python"])
        self.assertIn("work", self._presets)

    def test_save_preset_strips_name(self):
        from tagmanager.app.preset.service import save_preset
        save_preset("  work  ", ["python"])
        self.assertIn("work", self._presets)

    def test_save_preset_filters_empty_tags(self):
        from tagmanager.app.preset.service import save_preset
        save_preset("work", ["python", "", "  ", "backend"])
        self.assertEqual(self._presets["work"], ["python", "backend"])

    def test_save_preset_empty_name_returns_false(self):
        from tagmanager.app.preset.service import save_preset
        self.assertFalse(save_preset("", ["python"]))

    def test_save_preset_empty_tags_returns_false(self):
        from tagmanager.app.preset.service import save_preset
        self.assertFalse(save_preset("work", []))

    def test_save_preset_all_empty_tags_returns_false(self):
        from tagmanager.app.preset.service import save_preset
        self.assertFalse(save_preset("work", ["", "  "]))

    def test_save_preset_overwrites_existing(self):
        from tagmanager.app.preset.service import save_preset
        self._presets = {"work": ["old"]}
        save_preset("work", ["new"])
        self.assertEqual(self._presets["work"], ["new"])

    def test_save_multiple_presets(self):
        from tagmanager.app.preset.service import save_preset
        save_preset("work", ["python", "backend"])
        save_preset("media", ["video", "audio"])
        self.assertEqual(len(self._presets), 2)

    # --- get_preset ---

    def test_get_preset_existing(self):
        from tagmanager.app.preset.service import get_preset
        self._presets = {"work": ["python", "backend"]}
        result = get_preset("work")
        self.assertEqual(result, ["python", "backend"])

    def test_get_preset_nonexistent_returns_none(self):
        from tagmanager.app.preset.service import get_preset
        result = get_preset("nonexistent")
        self.assertIsNone(result)

    def test_get_preset_case_insensitive(self):
        from tagmanager.app.preset.service import get_preset
        self._presets = {"work": ["python"]}
        result = get_preset("WORK")
        self.assertEqual(result, ["python"])

    def test_get_preset_strips_name(self):
        from tagmanager.app.preset.service import get_preset
        self._presets = {"work": ["python"]}
        result = get_preset("  work  ")
        self.assertEqual(result, ["python"])

    # --- delete_preset ---

    def test_delete_preset_existing(self):
        from tagmanager.app.preset.service import delete_preset
        self._presets = {"work": ["python"]}
        result = delete_preset("work")
        self.assertTrue(result)
        self.assertNotIn("work", self._presets)

    def test_delete_preset_nonexistent_returns_false(self):
        from tagmanager.app.preset.service import delete_preset
        result = delete_preset("nonexistent")
        self.assertFalse(result)

    def test_delete_preset_leaves_others(self):
        from tagmanager.app.preset.service import delete_preset
        self._presets = {"work": ["python"], "media": ["video"]}
        delete_preset("work")
        self.assertIn("media", self._presets)
        self.assertNotIn("work", self._presets)

    def test_delete_preset_case_insensitive(self):
        from tagmanager.app.preset.service import delete_preset
        self._presets = {"work": ["python"]}
        result = delete_preset("WORK")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
