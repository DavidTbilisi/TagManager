import os
import unittest
import tempfile
import shutil
from unittest.mock import patch


class TestMoveService(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_file = os.path.join(self.test_dir, "old.py")
        self.new_file = os.path.join(self.test_dir, "new.py")
        self.old_abs = os.path.normpath(os.path.abspath(self.old_file))
        self.new_abs = os.path.normpath(os.path.abspath(self.new_file))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _patch(self, tags_data, save_return=True):
        load = patch("tagmanager.app.move.service.load_tags", return_value=dict(tags_data))
        save = patch("tagmanager.app.move.service.save_tags", return_value=save_return)
        return load, save

    # --- move_path ---

    def test_move_path_success(self):
        from tagmanager.app.move.service import move_path
        data = {self.old_abs: ["python", "backend"]}
        load_p, save_p = self._patch(data)
        with load_p, save_p as mock_save:
            success, msg = move_path(self.old_file, self.new_file)
        self.assertTrue(success)
        saved = mock_save.call_args[0][0]
        self.assertIn(self.new_abs, saved)
        self.assertNotIn(self.old_abs, saved)
        self.assertEqual(saved[self.new_abs], ["python", "backend"])

    def test_move_path_not_tracked(self):
        from tagmanager.app.move.service import move_path
        load_p, save_p = self._patch({})
        with load_p, save_p:
            success, msg = move_path(self.old_file, self.new_file)
        self.assertFalse(success)
        self.assertIn("not tracked", msg)

    def test_move_path_same_path(self):
        from tagmanager.app.move.service import move_path
        data = {self.old_abs: ["python"]}
        load_p, save_p = self._patch(data)
        with load_p, save_p:
            success, msg = move_path(self.old_file, self.old_file)
        self.assertFalse(success)
        self.assertIn("same", msg)

    def test_move_path_destination_already_tracked(self):
        from tagmanager.app.move.service import move_path
        data = {
            self.old_abs: ["python"],
            self.new_abs: ["existing"],
        }
        load_p, save_p = self._patch(data)
        with load_p, save_p:
            success, msg = move_path(self.old_file, self.new_file)
        self.assertFalse(success)
        self.assertIn("already tracked", msg)

    def test_move_path_save_failure(self):
        from tagmanager.app.move.service import move_path
        data = {self.old_abs: ["python"]}
        load_p, save_p = self._patch(data, save_return=False)
        with load_p, save_p:
            success, msg = move_path(self.old_file, self.new_file)
        self.assertFalse(success)
        self.assertIn("Failed", msg)

    def test_move_path_normalizes_paths(self):
        from tagmanager.app.move.service import move_path
        data = {self.old_abs: ["docs"]}
        load_p, save_p = self._patch(data)
        with load_p, save_p as mock_save:
            success, _ = move_path(self.old_file, self.new_file)
        self.assertTrue(success)
        saved = mock_save.call_args[0][0]
        for key in saved:
            self.assertEqual(key, os.path.normpath(key))

    def test_move_path_success_message(self):
        from tagmanager.app.move.service import move_path
        data = {self.old_abs: ["python"]}
        load_p, save_p = self._patch(data)
        with load_p, save_p:
            success, msg = move_path(self.old_file, self.new_file)
        self.assertTrue(success)
        self.assertIn("Moved", msg)

    # --- clean_missing ---

    def test_clean_missing_no_missing(self):
        from tagmanager.app.move.service import clean_missing
        existing = os.path.join(self.test_dir, "exists.py")
        with open(existing, "w") as f:
            f.write("")
        data = {os.path.normpath(os.path.abspath(existing)): ["python"]}
        with patch("tagmanager.app.move.service.load_tags", return_value=data), \
             patch("tagmanager.app.move.service.save_tags") as mock_save:
            result = clean_missing()
        self.assertEqual(result["count"], 0)
        mock_save.assert_not_called()

    def test_clean_missing_removes_ghost_paths(self):
        from tagmanager.app.move.service import clean_missing
        ghost = os.path.join(self.test_dir, "gone.py")
        data = {os.path.normpath(os.path.abspath(ghost)): ["python"]}
        with patch("tagmanager.app.move.service.load_tags", return_value=data), \
             patch("tagmanager.app.move.service.save_tags") as mock_save:
            result = clean_missing()
        self.assertEqual(result["count"], 1)
        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        self.assertEqual(saved, {})

    def test_clean_missing_dry_run_does_not_save(self):
        from tagmanager.app.move.service import clean_missing
        ghost = os.path.join(self.test_dir, "gone.py")
        data = {os.path.normpath(os.path.abspath(ghost)): ["python"]}
        with patch("tagmanager.app.move.service.load_tags", return_value=data), \
             patch("tagmanager.app.move.service.save_tags") as mock_save:
            result = clean_missing(dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["count"], 1)
        mock_save.assert_not_called()

    def test_clean_missing_mixed(self):
        from tagmanager.app.move.service import clean_missing
        existing = os.path.join(self.test_dir, "exists.py")
        with open(existing, "w") as f:
            f.write("")
        ghost = os.path.join(self.test_dir, "gone.py")
        data = {
            os.path.normpath(os.path.abspath(existing)): ["python"],
            os.path.normpath(os.path.abspath(ghost)): ["docs"],
        }
        with patch("tagmanager.app.move.service.load_tags", return_value=data), \
             patch("tagmanager.app.move.service.save_tags") as mock_save:
            result = clean_missing()
        self.assertEqual(result["count"], 1)
        saved = mock_save.call_args[0][0]
        self.assertEqual(len(saved), 1)

    def test_clean_missing_dry_run_message(self):
        from tagmanager.app.move.service import clean_missing
        ghost = os.path.join(self.test_dir, "gone.py")
        data = {os.path.normpath(os.path.abspath(ghost)): ["python"]}
        with patch("tagmanager.app.move.service.load_tags", return_value=data), \
             patch("tagmanager.app.move.service.save_tags"):
            result = clean_missing(dry_run=True)
        self.assertIn("Would", result["message"])

    def test_clean_missing_success_message(self):
        from tagmanager.app.move.service import clean_missing
        ghost = os.path.join(self.test_dir, "gone.py")
        data = {os.path.normpath(os.path.abspath(ghost)): ["python"]}
        with patch("tagmanager.app.move.service.load_tags", return_value=data), \
             patch("tagmanager.app.move.service.save_tags"):
            result = clean_missing()
        self.assertIn("Removed", result["message"])

    def test_clean_empty_database(self):
        from tagmanager.app.move.service import clean_missing
        with patch("tagmanager.app.move.service.load_tags", return_value={}), \
             patch("tagmanager.app.move.service.save_tags") as mock_save:
            result = clean_missing()
        self.assertEqual(result["count"], 0)
        mock_save.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
