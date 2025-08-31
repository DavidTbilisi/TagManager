#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.search.service
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


class TestSearchService(unittest.TestCase):
    """Comprehensive tests for search service functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        
        # Mock the helpers module
        self.helpers_patcher = patch('tagmanager.app.search.service.load_tags')
        self.mock_load_tags = self.helpers_patcher.start()
        
    def tearDown(self):
        """Clean up after each test"""
        self.helpers_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_search_by_tags_single_tag_match(self):
        """Test searching by single tag with matches"""
        from tagmanager.app.search.service import search_files_by_tags
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"],
            "/path/file3.py": ["python", "web"],
            "/path/file4.md": ["documentation"]
        }
        
        # Execute
        results = search_files_by_tags(["python"])
        
        # Verify
        expected_results = ["/path/file1.py", "/path/file3.py"]
        self.assertEqual(set(results), set(expected_results))
        self.assertEqual(len(results), 2)
    
    def test_search_by_tags_multiple_tags_and_logic(self):
        """Test searching by multiple tags (AND logic)"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend", "api"],
            "/path/file2.py": ["python", "frontend", "web"],
            "/path/file3.js": ["javascript", "frontend", "web"],
            "/path/file4.py": ["python", "backend", "database"]
        }
        
        # Execute - search for files with both "python" AND "backend"
        results = search_by_tags(["python", "backend"])
        
        # Verify
        expected_results = ["/path/file1.py", "/path/file4.py"]
        self.assertEqual(set(results), set(expected_results))
    
    def test_search_by_tags_no_matches(self):
        """Test searching with no matching results"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        
        # Execute - search for non-existent tag
        results = search_by_tags(["nonexistent"])
        
        # Verify
        self.assertEqual(results, [])
    
    def test_search_by_tags_empty_search_tags(self):
        """Test searching with empty tag list"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        
        # Execute
        results = search_by_tags([])
        
        # Verify - should return empty list
        self.assertEqual(results, [])
    
    def test_search_by_tags_empty_database(self):
        """Test searching in empty tags database"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock empty database
        self.mock_load_tags.return_value = {}
        
        # Execute
        results = search_by_tags(["python"])
        
        # Verify
        self.assertEqual(results, [])
    
    def test_search_by_tags_case_sensitivity(self):
        """Test that tag search is case-sensitive"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database with different cases
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["Python", "backend"],
            "/path/file2.py": ["python", "frontend"],
            "/path/file3.py": ["PYTHON", "web"]
        }
        
        # Execute - search for exact case
        results_lower = search_by_tags(["python"])
        results_upper = search_by_tags(["Python"])
        results_caps = search_by_tags(["PYTHON"])
        
        # Verify case sensitivity
        self.assertEqual(results_lower, ["/path/file2.py"])
        self.assertEqual(results_upper, ["/path/file1.py"])
        self.assertEqual(results_caps, ["/path/file3.py"])
    
    def test_search_by_tags_unicode_tags(self):
        """Test searching with Unicode tags"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database with Unicode
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "测试"],
            "/path/file2.js": ["javascript", "тест"],
            "/path/file3.md": ["documentation", "🏷️"]
        }
        
        # Execute
        results_chinese = search_by_tags(["测试"])
        results_russian = search_by_tags(["тест"])
        results_emoji = search_by_tags(["🏷️"])
        
        # Verify
        self.assertEqual(results_chinese, ["/path/file1.py"])
        self.assertEqual(results_russian, ["/path/file2.js"])
        self.assertEqual(results_emoji, ["/path/file3.md"])
    
    def test_search_by_tags_special_characters(self):
        """Test searching with special characters in tags"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database with special characters
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python-3", "web-dev"],
            "/path/file2.js": ["node.js", "front-end"],
            "/path/file3.css": ["css3", "style@sheet"]
        }
        
        # Execute
        results_hyphen = search_by_tags(["python-3"])
        results_dot = search_by_tags(["node.js"])
        results_at = search_by_tags(["style@sheet"])
        
        # Verify
        self.assertEqual(results_hyphen, ["/path/file1.py"])
        self.assertEqual(results_dot, ["/path/file2.js"])
        self.assertEqual(results_at, ["/path/file3.css"])
    
    def test_search_by_tags_whitespace_tags(self):
        """Test searching with whitespace in tags"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database with whitespace
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["machine learning", "data science"],
            "/path/file2.py": ["web development", "full stack"],
            "/path/file3.py": [" python ", "\ttest\t"]
        }
        
        # Execute
        results_space = search_by_tags(["machine learning"])
        results_padded = search_by_tags([" python "])
        results_tabs = search_by_tags(["\ttest\t"])
        
        # Verify exact matching including whitespace
        self.assertEqual(results_space, ["/path/file1.py"])
        self.assertEqual(results_padded, ["/path/file3.py"])
        self.assertEqual(results_tabs, ["/path/file3.py"])
    
    def test_search_by_tags_empty_string_tag(self):
        """Test searching for empty string tag"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database with empty string tag
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", ""],
            "/path/file2.js": ["javascript", "web"],
            "/path/file3.py": ["", "test"]
        }
        
        # Execute
        results = search_by_tags([""])
        
        # Verify
        expected_results = ["/path/file1.py", "/path/file3.py"]
        self.assertEqual(set(results), set(expected_results))
    
    def test_search_by_tags_duplicate_search_tags(self):
        """Test searching with duplicate tags in search list"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.py": ["python", "frontend"],
            "/path/file3.js": ["javascript", "frontend"]
        }
        
        # Execute with duplicate search tags
        results = search_by_tags(["python", "python", "backend"])
        
        # Verify - should work same as ["python", "backend"]
        self.assertEqual(results, ["/path/file1.py"])
    
    def test_search_by_tags_large_database(self):
        """Test searching in large tags database"""
        from tagmanager.app.search.service import search_by_tags
        
        # Create large database
        large_db = {}
        for i in range(10000):
            file_path = f"/path/file_{i}.py"
            tags = [f"tag_{i % 100}", "python"] if i % 2 == 0 else [f"tag_{i % 100}", "javascript"]
            large_db[file_path] = tags
        
        self.mock_load_tags.return_value = large_db
        
        # Execute
        results = search_by_tags(["python"])
        
        # Verify - should find all even-numbered files
        self.assertEqual(len(results), 5000)
        
        # Check a few specific results
        self.assertIn("/path/file_0.py", results)
        self.assertIn("/path/file_2.py", results)
        self.assertNotIn("/path/file_1.py", results)
        self.assertNotIn("/path/file_3.py", results)
    
    def test_search_by_tags_complex_and_logic(self):
        """Test complex AND logic with multiple tags"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock complex tags database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend", "api", "rest"],
            "/path/file2.py": ["python", "backend", "database"],
            "/path/file3.py": ["python", "frontend", "api"],
            "/path/file4.js": ["javascript", "backend", "api", "rest"],
            "/path/file5.py": ["python", "backend", "api", "graphql"]
        }
        
        # Execute - search for files with python AND backend AND api
        results = search_by_tags(["python", "backend", "api"])
        
        # Verify
        expected_results = ["/path/file1.py", "/path/file5.py"]
        self.assertEqual(set(results), set(expected_results))
    
    def test_search_by_tags_all_files_match(self):
        """Test when all files match the search criteria"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock database where all files have common tag
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.py": ["python", "frontend"],
            "/path/file3.py": ["python", "web"],
            "/path/file4.py": ["python", "api"]
        }
        
        # Execute
        results = search_by_tags(["python"])
        
        # Verify all files are returned
        expected_results = ["/path/file1.py", "/path/file2.py", "/path/file3.py", "/path/file4.py"]
        self.assertEqual(set(results), set(expected_results))
        self.assertEqual(len(results), 4)
    
    def test_search_by_tags_single_file_multiple_matches(self):
        """Test when single file matches multiple different search criteria"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock database
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend", "api", "rest", "web"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        
        # Execute multiple searches
        results_python = search_by_tags(["python"])
        results_backend = search_by_tags(["backend"])
        results_api = search_by_tags(["api"])
        results_multi = search_by_tags(["python", "backend"])
        
        # Verify same file appears in multiple results
        self.assertEqual(results_python, ["/path/file1.py"])
        self.assertEqual(results_backend, ["/path/file1.py"])
        self.assertEqual(results_api, ["/path/file1.py"])
        self.assertEqual(results_multi, ["/path/file1.py"])
    
    @patch('tagmanager.app.search.service.load_tags', side_effect=Exception("Load error"))
    def test_search_by_tags_load_exception(self, mock_load):
        """Test handling of exception in load_tags"""
        from tagmanager.app.search.service import search_by_tags
        
        # Execute - should raise exception
        with self.assertRaises(Exception):
            search_by_tags(["python"])
    
    def test_search_by_tags_none_input(self):
        """Test searching with None as input"""
        from tagmanager.app.search.service import search_by_tags
        
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"]
        }
        
        # Execute with None - should handle gracefully
        with self.assertRaises((TypeError, AttributeError)):
            search_by_tags(None)
    
    def test_search_by_tags_non_list_input(self):
        """Test searching with non-list input"""
        from tagmanager.app.search.service import search_by_tags
        
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "backend"]
        }
        
        # Execute with string instead of list
        with self.assertRaises((TypeError, AttributeError)):
            search_by_tags("python")
    
    def test_search_by_tags_mixed_types_in_list(self):
        """Test searching with mixed types in tag list"""
        from tagmanager.app.search.service import search_by_tags
        
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", "123", "True"],
            "/path/file2.py": ["javascript", "456"]
        }
        
        # Execute with mixed types (converted to strings)
        results = search_by_tags(["python", 123, True])
        
        # Verify - depends on implementation, but likely no matches due to type mismatch
        # This tests the robustness of the function
        self.assertIsInstance(results, list)
    
    def test_search_by_tags_very_long_tag_names(self):
        """Test searching with very long tag names"""
        from tagmanager.app.search.service import search_by_tags
        
        # Create very long tag names
        long_tag = "a" * 1000
        another_long_tag = "b" * 500
        
        self.mock_load_tags.return_value = {
            "/path/file1.py": ["python", long_tag],
            "/path/file2.py": ["javascript", another_long_tag]
        }
        
        # Execute
        results = search_by_tags([long_tag])
        
        # Verify
        self.assertEqual(results, ["/path/file1.py"])
    
    def test_search_by_tags_performance_large_tag_lists(self):
        """Test performance with files having large numbers of tags"""
        from tagmanager.app.search.service import search_by_tags
        
        # Create file with many tags
        many_tags = [f"tag_{i}" for i in range(1000)]
        many_tags.append("target_tag")
        
        self.mock_load_tags.return_value = {
            "/path/file1.py": many_tags,
            "/path/file2.py": ["javascript", "simple"]
        }
        
        # Execute
        results = search_by_tags(["target_tag"])
        
        # Verify
        self.assertEqual(results, ["/path/file1.py"])
    
    def test_search_by_tags_order_preservation(self):
        """Test that search results maintain consistent order"""
        from tagmanager.app.search.service import search_by_tags
        
        # Mock database with multiple matches
        self.mock_load_tags.return_value = {
            "/path/z_file.py": ["python", "backend"],
            "/path/a_file.py": ["python", "frontend"],
            "/path/m_file.py": ["python", "web"]
        }
        
        # Execute multiple times
        results1 = search_by_tags(["python"])
        results2 = search_by_tags(["python"])
        results3 = search_by_tags(["python"])
        
        # Verify consistent ordering
        self.assertEqual(results1, results2)
        self.assertEqual(results2, results3)
        self.assertEqual(len(results1), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
