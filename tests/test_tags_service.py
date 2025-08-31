#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.tags.service
Testing every function, edge case, and error condition
"""

import unittest
import tempfile
import os
import json
import shutil
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestTagsService(unittest.TestCase):
    """Comprehensive tests for tags service functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        
        # Mock the helpers module
        self.helpers_patcher = patch('tagmanager.app.tags.service.load_tags')
        self.mock_load_tags = self.helpers_patcher.start()
        
    def tearDown(self):
        """Clean up after each test"""
        self.helpers_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_list_all_tags_multiple_files(self):
        """Test listing all unique tags from multiple files"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend", "api"],
            "/path/file2.js": ["javascript", "frontend", "web"],
            "/path/file3.py": ["python", "web", "django"],
            "/path/file4.md": ["documentation", "readme"]
        }
        
        # Execute
        result = list_all_tags()
        
        # Verify all unique tags are returned
        expected_tags = {"python", "backend", "api", "javascript", "frontend", "web", "django", "documentation", "readme"}
        self.assertEqual(set(result), expected_tags)
    
    def test_list_all_tags_empty_database(self):
        """Test listing tags from empty database"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock empty database
        self.mock_load_tags.return_value = {}
        
        # Execute
        result = list_all_tags()
        
        # Verify empty list
        self.assertEqual(result, [])
    
    def test_list_all_tags_duplicate_tags(self):
        """Test that duplicate tags are not included multiple times"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock database with duplicate tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "web", "api"],
            "/path/file2.py": ["python", "backend", "api"],
            "/path/file3.py": ["python", "frontend", "web"]
        }
        
        # Execute
        result = list_all_tags()
        
        # Verify no duplicates
        expected_tags = {"python", "web", "api", "backend", "frontend"}
        self.assertEqual(set(result), expected_tags)
        self.assertEqual(len(result), len(set(result)))  # No duplicates
    
    def test_list_all_tags_empty_tag_lists(self):
        """Test listing tags when some files have empty tag lists"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock database with empty tag lists
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": [],
            "/path/file3.py": ["web"],
            "/path/file4.md": []
        }
        
        # Execute
        result = list_all_tags()
        
        # Verify only non-empty tags
        expected_tags = {"python", "backend", "web"}
        self.assertEqual(set(result), expected_tags)
    
    def test_list_all_tags_unicode_tags(self):
        """Test listing tags with Unicode characters"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock database with Unicode tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "测试", "🏷️"],
            "/path/file2.js": ["javascript", "тест", "café"],
            "/path/file3.md": ["documentation", "naïve"]
        }
        
        # Execute
        result = list_all_tags()
        
        # Verify Unicode tags are handled correctly
        expected_tags = {"python", "测试", "🏷️", "javascript", "тест", "café", "documentation", "naïve"}
        self.assertEqual(set(result), expected_tags)
    
    def test_list_all_tags_special_characters(self):
        """Test listing tags with special characters"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock database with special character tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python-3", "web-dev", "api@v1"],
            "/path/file2.js": ["node.js", "front-end", "css3"],
            "/path/file3.sh": ["bash", "shell-script", "unix/linux"]
        }
        
        # Execute
        result = list_all_tags()
        
        # Verify special characters are preserved
        expected_tags = {"python-3", "web-dev", "api@v1", "node.js", "front-end", "css3", "bash", "shell-script", "unix/linux"}
        self.assertEqual(set(result), expected_tags)
    
    def test_list_all_tags_whitespace_tags(self):
        """Test listing tags with whitespace"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock database with whitespace tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["machine learning", "data science", " python "],
            "/path/file2.js": ["web development", "\tjavascript\t", "full stack"]
        }
        
        # Execute
        result = list_all_tags()
        
        # Verify whitespace is preserved
        expected_tags = {"machine learning", "data science", " python ", "web development", "\tjavascript\t", "full stack"}
        self.assertEqual(set(result), expected_tags)
    
    def test_list_all_tags_empty_string_tags(self):
        """Test listing tags including empty strings"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock database with empty string tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "", "backend"],
            "/path/file2.js": ["", "javascript", "frontend"],
            "/path/file3.md": ["documentation"]
        }
        
        # Execute
        result = list_all_tags()
        
        # Verify empty strings are included
        expected_tags = {"python", "", "backend", "javascript", "frontend", "documentation"}
        self.assertEqual(set(result), expected_tags)
    
    def test_list_all_tags_case_sensitivity(self):
        """Test that tag listing preserves case sensitivity"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Mock database with different cases
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["Python", "python", "PYTHON"],
            "/path/file2.js": ["JavaScript", "javascript", "Javascript"]
        }
        
        # Execute
        result = list_all_tags()
        
        # Verify all case variations are preserved
        expected_tags = {"Python", "python", "PYTHON", "JavaScript", "javascript", "Javascript"}
        self.assertEqual(set(result), expected_tags)
        self.assertEqual(len(result), 6)  # All different
    
    def test_list_all_tags_large_database(self):
        """Test listing tags from large database"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Create large database
        large_db = {}
        for i in range(1000):
            file_path = f"/path/file_{i}.py"
            tags = [f"tag_{i % 100}", "common_tag", f"unique_{i}"]
            large_db[file_path] = tags
        
        self.mock_load_tags.return_value = large_db
        
        # Execute
        result = list_all_tags()
        
        # Verify correct number of unique tags
        # Should have: 100 tag_X tags + 1 common_tag + 1000 unique_X tags = 1101 total
        expected_count = 100 + 1 + 1000
        self.assertEqual(len(set(result)), expected_count)
        self.assertIn("common_tag", result)
        self.assertIn("tag_0", result)
        self.assertIn("unique_0", result)
    
    @patch('tagmanager.app.tags.service.load_tags', side_effect=Exception("Load error"))
    def test_list_all_tags_load_exception(self, mock_load):
        """Test handling of exception in load_tags"""
        from tagmanager.app.tags.service import list_all_tags
        
        # Execute - should raise exception
        with self.assertRaises(Exception):
            list_all_tags()
    
    def test_get_files_by_tag_single_match(self):
        """Test getting files by tag with single match"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"],
            "/path/file3.py": ["python", "web"]
        }
        
        # Execute
        result = get_files_by_tag("javascript")
        
        # Verify
        self.assertEqual(result, ["/path/file2.js"])
    
    def test_get_files_by_tag_multiple_matches(self):
        """Test getting files by tag with multiple matches"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.py": ["python", "frontend"],
            "/path/file3.js": ["javascript", "frontend"],
            "/path/file4.py": ["python", "web"]
        }
        
        # Execute
        result = get_files_by_tag("python")
        
        # Verify
        expected_files = ["/path/file1.py", "/path/file2.py", "/path/file4.py"]
        self.assertEqual(set(result), set(expected_files))
        self.assertEqual(len(result), 3)
    
    def test_get_files_by_tag_no_matches(self):
        """Test getting files by tag with no matches"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        
        # Execute
        result = get_files_by_tag("nonexistent")
        
        # Verify
        self.assertEqual(result, [])
    
    def test_get_files_by_tag_empty_database(self):
        """Test getting files by tag from empty database"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock empty database
        self.mock_load_tags.return_value = {}
        
        # Execute
        result = get_files_by_tag("python")
        
        # Verify
        self.assertEqual(result, [])
    
    def test_get_files_by_tag_case_sensitivity(self):
        """Test that get_files_by_tag is case-sensitive"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock database with different cases
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["Python", "backend"],
            "/path/file2.py": ["python", "frontend"],
            "/path/file3.py": ["PYTHON", "web"]
        }
        
        # Execute with different cases
        result_lower = get_files_by_tag("python")
        result_upper = get_files_by_tag("Python")
        result_caps = get_files_by_tag("PYTHON")
        
        # Verify case sensitivity
        self.assertEqual(result_lower, ["/path/file2.py"])
        self.assertEqual(result_upper, ["/path/file1.py"])
        self.assertEqual(result_caps, ["/path/file3.py"])
    
    def test_get_files_by_tag_unicode_tag(self):
        """Test getting files by Unicode tag"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock database with Unicode tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "测试"],
            "/path/file2.js": ["javascript", "тест"],
            "/path/file3.md": ["documentation", "🏷️"]
        }
        
        # Execute
        result_chinese = get_files_by_tag("测试")
        result_russian = get_files_by_tag("тест")
        result_emoji = get_files_by_tag("🏷️")
        
        # Verify
        self.assertEqual(result_chinese, ["/path/file1.py"])
        self.assertEqual(result_russian, ["/path/file2.js"])
        self.assertEqual(result_emoji, ["/path/file3.md"])
    
    def test_get_files_by_tag_special_characters(self):
        """Test getting files by tag with special characters"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock database with special character tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python-3", "web-dev"],
            "/path/file2.js": ["node.js", "front-end"],
            "/path/file3.css": ["css3", "style@sheet"]
        }
        
        # Execute
        result_hyphen = get_files_by_tag("python-3")
        result_dot = get_files_by_tag("node.js")
        result_at = get_files_by_tag("style@sheet")
        
        # Verify
        self.assertEqual(result_hyphen, ["/path/file1.py"])
        self.assertEqual(result_dot, ["/path/file2.js"])
        self.assertEqual(result_at, ["/path/file3.css"])
    
    def test_get_files_by_tag_whitespace_tag(self):
        """Test getting files by tag with whitespace"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock database with whitespace tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["machine learning", "data science"],
            "/path/file2.py": [" python ", "\ttest\t"],
            "/path/file3.js": ["web development"]
        }
        
        # Execute
        result_space = get_files_by_tag("machine learning")
        result_padded = get_files_by_tag(" python ")
        result_tabs = get_files_by_tag("\ttest\t")
        
        # Verify exact matching including whitespace
        self.assertEqual(result_space, ["/path/file1.py"])
        self.assertEqual(result_padded, ["/path/file2.py"])
        self.assertEqual(result_tabs, ["/path/file2.py"])
    
    def test_get_files_by_tag_empty_string(self):
        """Test getting files by empty string tag"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock database with empty string tags
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", ""],
            "/path/file2.js": ["javascript", "web"],
            "/path/file3.py": ["", "test"]
        }
        
        # Execute
        result = get_files_by_tag("")
        
        # Verify
        expected_files = ["/path/file1.py", "/path/file3.py"]
        self.assertEqual(set(result), set(expected_files))
    
    def test_get_files_by_tag_none_input(self):
        """Test getting files by None tag"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"]
        }
        
        # Execute with None - should handle gracefully or raise appropriate error
        try:
            result = get_files_by_tag(None)
            # If it doesn't raise an error, result should be empty or handle None appropriately
            self.assertIsInstance(result, list)
        except (TypeError, AttributeError):
            # This is also acceptable behavior
            pass
    
    def test_get_files_by_tag_large_database(self):
        """Test getting files by tag from large database"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Create large database
        large_db = {}
        for i in range(10000):
            file_path = f"/path/file_{i}.py"
            tags = ["common_tag"] if i % 2 == 0 else ["other_tag"]
            large_db[file_path] = tags
        
        self.mock_load_tags.return_value = large_db
        
        # Execute
        result = get_files_by_tag("common_tag")
        
        # Verify correct number of matches
        self.assertEqual(len(result), 5000)  # Half of the files
        
        # Check a few specific results
        self.assertIn("/path/file_0.py", result)
        self.assertIn("/path/file_2.py", result)
        self.assertNotIn("/path/file_1.py", result)
        self.assertNotIn("/path/file_3.py", result)
    
    @patch('tagmanager.app.tags.service.load_tags', side_effect=Exception("Load error"))
    def test_get_files_by_tag_load_exception(self, mock_load):
        """Test handling of exception in load_tags for get_files_by_tag"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Execute - should raise exception
        with self.assertRaises(Exception):
            get_files_by_tag("python")
    
    def test_get_files_by_tag_order_consistency(self):
        """Test that get_files_by_tag returns consistent order"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Mock database with multiple matches
        self.mock_load_tags.return_value = {
            "/path/z_file.py": ["python", "backend"],
            "/path/a_file.py": ["python", "frontend"],
            "/path/m_file.py": ["python", "web"]
        }
        
        # Execute multiple times
        result1 = get_files_by_tag("python")
        result2 = get_files_by_tag("python")
        result3 = get_files_by_tag("python")
        
        # Verify consistent ordering
        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)
        self.assertEqual(len(result1), 3)
    
    def test_get_files_by_tag_performance_many_tags_per_file(self):
        """Test performance when files have many tags"""
        from tagmanager.app.tags.service import get_files_by_tag
        
        # Create files with many tags
        many_tags = [f"tag_{i}" for i in range(1000)]
        many_tags.append("target_tag")
        
        self.mock_load_tags.return_value = {
            "/path/file1.py": many_tags,
            "/path/file2.py": ["javascript", "simple"],
            "/path/file3.py": many_tags  # Another file with many tags
        }
        
        # Execute
        result = get_files_by_tag("target_tag")
        
        # Verify
        expected_files = ["/path/file1.py", "/path/file3.py"]
        self.assertEqual(set(result), set(expected_files))


if __name__ == '__main__':
    unittest.main(verbosity=2)
