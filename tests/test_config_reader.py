#!/usr/bin/env python3
"""Tests for tagmanager.configReader (test_config.ini branch via reload)."""

import importlib
import os
import sys
import unittest
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestConfigReader(unittest.TestCase):
    def test_prefers_test_config_ini_when_marked_present(self):
        import tagmanager.configReader as cr

        orig_exists = cr.os.path.exists
        test_ini = os.path.normpath(os.path.join(cr.root_dir, "test_config.ini"))

        def exists(p):
            if os.path.normpath(p) == test_ini:
                return True
            return orig_exists(p)

        try:
            with patch.object(cr.os.path, "exists", side_effect=exists):
                importlib.reload(cr)
                self.assertTrue(
                    str(cr.config_file).replace("\\", "/").endswith("test_config.ini")
                )
        finally:
            importlib.reload(cr)


if __name__ == "__main__":
    unittest.main()
