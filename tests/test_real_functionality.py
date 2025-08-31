#!/usr/bin/env python3
"""
Real functionality tests - no mocking, test actual services
"""

import unittest
import tempfile
import os
import json
import shutil
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestRealFunctionality(unittest.TestCase):
    """Test actual service functionality without mocking"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create isolated tag file for this test
        self.test_tag_file = os.path.join(self.test_dir, "test_tags.json")
        
        # Patch the TAG_FILE to use our test file
        from unittest.mock import patch
        self.tag_file_patcher = patch('tagmanager.app.helpers.TAG_FILE', self.test_tag_file)
        self.tag_file_patcher.start()
        
        # Create test files
        self.test_file1 = os.path.join(self.test_dir, "test1.py")
        self.test_file2 = os.path.join(self.test_dir, "test2.js")
        
        with open(self.test_file1, 'w') as f:
            f.write("# Python test file")
        with open(self.test_file2, 'w') as f:
            f.write("// JavaScript test file")
    
    def tearDown(self):
        """Clean up"""
        self.tag_file_patcher.stop()
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_helpers_load_save_cycle(self):
        """Test that helpers can save and load data"""
        from tagmanager.app.helpers import load_tags, save_tags
        
        # Test data
        test_data = {
            "/path/to/file1.py": ["python", "test"],
            "/path/to/file2.js": ["javascript", "web"]
        }
        
        # Save data
        result = save_tags(test_data)
        self.assertTrue(result, "save_tags should return True")
        
        # Load data back
        loaded_data = load_tags()
        self.assertEqual(loaded_data, test_data, "Loaded data should match saved data")
        
        print("✅ Helpers: Load/Save cycle works")
    
    def test_add_service_existing_file(self):
        """Test adding tags to existing file"""
        from tagmanager.app.add.service import add_tags
        
        # Add tags to existing file
        result = add_tags(self.test_file1, ["python", "test"])
        self.assertTrue(result, "add_tags should return True for existing file")
        
        # Verify tags were saved
        from tagmanager.app.helpers import load_tags
        saved_tags = load_tags()
        
        expected_path = os.path.abspath(self.test_file1)
        self.assertIn(expected_path, saved_tags, "File should be in saved tags")
        self.assertEqual(set(saved_tags[expected_path]), {"python", "test"}, "Tags should match")
        
        print("✅ Add service: Adding tags to existing file works")
    
    def test_search_service_basic(self):
        """Test basic search functionality"""
        from tagmanager.app.add.service import add_tags
        from tagmanager.app.search.service import search_by_tags
        
        # Add tags to files
        add_tags(self.test_file1, ["python", "backend"])
        add_tags(self.test_file2, ["javascript", "frontend"])
        
        # Search for python files
        results = search_by_tags(["python"])
        
        expected_path = os.path.abspath(self.test_file1)
        self.assertIn(expected_path, results, "Should find python file")
        self.assertEqual(len(results), 1, "Should find exactly one python file")
        
        print("✅ Search service: Basic search works")
    
    def test_tags_service_list_all(self):
        """Test listing all tags"""
        from tagmanager.app.add.service import add_tags
        from tagmanager.app.tags.service import list_all_tags
        
        # Add tags to files
        add_tags(self.test_file1, ["python", "backend", "api"])
        add_tags(self.test_file2, ["javascript", "frontend", "web"])
        
        # List all tags
        all_tags = list_all_tags()
        
        expected_tags = {"python", "backend", "api", "javascript", "frontend", "web"}
        self.assertEqual(set(all_tags), expected_tags, "Should list all unique tags")
        
        print("✅ Tags service: List all tags works")
    
    def test_tags_service_search_by_tag(self):
        """Test searching files by specific tag"""
        from tagmanager.app.add.service import add_tags
        from tagmanager.app.tags.service import search_files_by_tag
        
        # Add tags to files
        add_tags(self.test_file1, ["python", "backend"])
        add_tags(self.test_file2, ["python", "frontend"])
        
        # Search for files with python tag
        python_files = search_files_by_tag("python")
        
        expected_paths = {os.path.abspath(self.test_file1), os.path.abspath(self.test_file2)}
        result_paths = set(python_files)
        
        self.assertEqual(result_paths, expected_paths, "Should find both python files")
        
        print("✅ Tags service: Search by tag works")
    
    def test_remove_service_basic(self):
        """Test removing a file path"""
        from tagmanager.app.add.service import add_tags
        from tagmanager.app.remove.service import remove_path
        from tagmanager.app.helpers import load_tags
        
        # Add tags first
        add_tags(self.test_file1, ["python", "test"])
        add_tags(self.test_file2, ["javascript", "web"])
        
        # Remove one file
        expected_path = os.path.abspath(self.test_file1)
        remove_path(expected_path)
        
        # Verify it was removed
        saved_tags = load_tags()
        self.assertNotIn(expected_path, saved_tags, "File should be removed from tags")
        
        # Verify other file is still there
        other_path = os.path.abspath(self.test_file2)
        self.assertIn(other_path, saved_tags, "Other file should still be in tags")
        
        print("✅ Remove service: Remove path works")
    
    def test_integration_workflow(self):
        """Test complete workflow: add, search, list, remove"""
        from tagmanager.app.add.service import add_tags
        from tagmanager.app.search.service import search_by_tags
        from tagmanager.app.tags.service import list_all_tags, search_files_by_tag
        from tagmanager.app.remove.service import remove_path
        
        # Step 1: Add tags to files
        add_tags(self.test_file1, ["python", "backend", "api"])
        add_tags(self.test_file2, ["javascript", "frontend", "web"])
        
        # Step 2: Search by multiple tags
        backend_files = search_by_tags(["python", "backend"])
        self.assertEqual(len(backend_files), 1, "Should find one backend python file")
        
        # Step 3: List all tags
        all_tags = list_all_tags()
        self.assertEqual(len(all_tags), 6, "Should have 6 unique tags")
        
        # Step 4: Search by single tag
        python_files = search_files_by_tag("python")
        self.assertEqual(len(python_files), 1, "Should find one python file")
        
        # Step 5: Remove a file
        remove_path(os.path.abspath(self.test_file1))
        
        # Step 6: Verify removal
        remaining_tags = list_all_tags()
        self.assertNotIn("python", remaining_tags, "Python tag should be gone")
        self.assertIn("javascript", remaining_tags, "JavaScript tag should remain")
        
        print("✅ Integration: Complete workflow works")


if __name__ == '__main__':
    print("🧪 Real Functionality Tests")
    print("=" * 50)
    unittest.main(verbosity=2)
