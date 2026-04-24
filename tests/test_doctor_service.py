#!/usr/bin/env python3
"""Tests for tm doctor diagnostics."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestDoctorService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.tag_file = os.path.join(self.test_dir, "tags.json")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_doctor_ok_empty_tag_file(self):
        from tagmanager.app.doctor.service import run_doctor

        with open(self.tag_file, "w", encoding="utf-8") as f:
            f.write("{}")
        with patch("tagmanager.app.helpers.get_tag_file_path", return_value=self.tag_file):
            with patch("tagmanager.app.doctor.service._config_check", return_value={"ok": True}):
                r = run_doctor(max_path_checks=10)
        self.assertTrue(r["ok"])
        self.assertEqual(r["checks"]["tag_file"]["path_count"], 0)

    def test_doctor_invalid_json(self):
        from tagmanager.app.doctor.service import run_doctor

        with open(self.tag_file, "w", encoding="utf-8") as f:
            f.write("{not json")
        with patch("tagmanager.app.helpers.get_tag_file_path", return_value=self.tag_file):
            with patch("tagmanager.app.doctor.service._config_check", return_value={"ok": True}):
                r = run_doctor(max_path_checks=10)
        self.assertFalse(r["ok"])
        self.assertTrue(r["checks"]["tag_file"]["invalid_json"])

    def test_doctor_counts_missing_sample(self):
        from tagmanager.app.doctor.service import run_doctor

        existing = os.path.join(self.test_dir, "exists.txt")
        open(existing, "w").close()
        data = {existing: ["a"], "/nope/does-not-exist-xyz-123": ["b"]}
        with open(self.tag_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        with patch("tagmanager.app.helpers.get_tag_file_path", return_value=self.tag_file):
            with patch("tagmanager.app.doctor.service._config_check", return_value={"ok": True}):
                r = run_doctor(max_path_checks=10)
        self.assertTrue(r["ok"])
        sp = r["checks"]["sample_paths"]
        self.assertEqual(sp["missing_on_disk"], 1)
        self.assertTrue(any("does-not-exist" in x for x in sp["missing_examples"]))


if __name__ == "__main__":
    unittest.main()
