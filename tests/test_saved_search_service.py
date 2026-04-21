import unittest
from unittest.mock import MagicMock, patch


class TestSavedSearchService(unittest.TestCase):
    def test_save_list_run_delete(self):
        from tagmanager.app.saved_search import service as svc

        stored = {}
        mgr = MagicMock()

        def get_side(key, default=None):
            if key == "saved_searches":
                return dict(stored)
            return default

        mgr.get.side_effect = get_side

        def set_raw(key, val):
            stored.clear()
            stored.update(val)

        mgr.set_raw.side_effect = lambda k, v: set_raw(k, v)

        with patch("tagmanager.app.saved_search.service.get_config_manager", return_value=mgr):
            ok, err = svc.save_saved_search(
                "q1",
                tags=["work", "q1"],
                path=None,
                match_all=True,
                exact=False,
                exclude=["archived"],
            )
            self.assertTrue(ok)
            self.assertEqual(err, "")

            spec = svc.get_saved_search("q1")
            self.assertIsNotNone(spec)
            self.assertEqual(spec["tags"], ["work", "q1"])
            self.assertTrue(spec["match_all"])
            self.assertEqual(spec["exclude"], ["archived"])

            self.assertIn("q1", svc.list_saved_search_names())

            with patch("tagmanager.app.saved_search.service.search_files_by_tags", return_value=["/a.py"]):
                paths, err2 = svc.run_saved_search("q1")
            self.assertEqual(err2, "")
            self.assertEqual(paths, ["/a.py"])

            self.assertTrue(svc.delete_saved_search("q1"))
            self.assertIsNone(svc.get_saved_search("q1"))
