#!/usr/bin/env python3
"""
Unit tests for TagManager CLI application
"""

import unittest
import tempfile
import os
import json
import shutil
from pathlib import Path

# Import the service modules for testing
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    # Try to import directly from the modules
    from tagmanager.app.add.service import add_tags
    from tagmanager.app.remove.service import remove_path, remove_invalid_paths
    from tagmanager.app.search.service import search_by_tags
    from tagmanager.app.tags.service import list_all_tags, get_files_by_tag
    from tagmanager.app.helpers import load_tags, save_tags
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    print("Some tests may be skipped")
    # Create mock functions for basic testing
    def add_tags(file_path, tags):
        return True
    def remove_path(path):
        pass
    def remove_invalid_paths():
        pass
    def search_by_tags(tags):
        return []
    def list_all_tags():
        return []
    def get_files_by_tag(tag):
        return []
    def load_tags():
        return {}
    def save_tags(data):
        pass


class TestTagManager(unittest.TestCase):
    """Test cases for TagManager functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_file.txt")
        self.test_tags_file = os.path.join(self.test_dir, "test_tags.json")
        
        # Create a test file
        with open(self.test_file, 'w') as f:
            f.write("Test content")
        
        # Mock the TAG_FILE path for testing
        import tagmanager.app.helpers as helpers
        self.original_tag_file = helpers.TAG_FILE
        helpers.TAG_FILE = self.test_tags_file
        
    def tearDown(self):
        """Clean up after each test"""
        # Restore original TAG_FILE
        import tagmanager.app.helpers as helpers
        helpers.TAG_FILE = self.original_tag_file
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_add_tags(self):
        """Test adding tags to a file"""
        tags = ["python", "test", "demo"]
        result = add_tags(self.test_file, tags)
        
        self.assertTrue(result)
        
        # Verify tags were saved
        saved_tags = load_tags()
        self.assertIn(self.test_file, saved_tags)
        self.assertEqual(set(saved_tags[self.test_file]), set(tags))
    
    def test_add_duplicate_tags(self):
        """Test adding duplicate tags (should not create duplicates)"""
        tags1 = ["python", "test"]
        tags2 = ["test", "demo", "python"]
        
        add_tags(self.test_file, tags1)
        add_tags(self.test_file, tags2)
        
        saved_tags = load_tags()
        expected_tags = set(["python", "test", "demo"])
        self.assertEqual(set(saved_tags[self.test_file]), expected_tags)
    
    def test_add_tags_nonexistent_file(self):
        """Test adding tags to a non-existent file (should create it)"""
        nonexistent_file = os.path.join(self.test_dir, "new_file.txt")
        tags = ["new", "file"]
        
        result = add_tags(nonexistent_file, tags)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(nonexistent_file))
        
        saved_tags = load_tags()
        self.assertIn(nonexistent_file, saved_tags)
        self.assertEqual(set(saved_tags[nonexistent_file]), set(tags))
    
    def test_remove_path(self):
        """Test removing a file path from tags"""
        tags = ["python", "test"]
        add_tags(self.test_file, tags)
        
        # Verify file is in tags
        saved_tags = load_tags()
        self.assertIn(self.test_file, saved_tags)
        
        # Remove the path
        remove_path(self.test_file)
        
        # Verify file is removed from tags
        saved_tags = load_tags()
        self.assertNotIn(self.test_file, saved_tags)
    
    def test_search_by_tags(self):
        """Test searching files by tags"""
        # Add tags to multiple files
        file1 = os.path.join(self.test_dir, "file1.py")
        file2 = os.path.join(self.test_dir, "file2.js")
        
        with open(file1, 'w') as f:
            f.write("Python file")
        with open(file2, 'w') as f:
            f.write("JavaScript file")
        
        add_tags(file1, ["python", "code"])
        add_tags(file2, ["javascript", "code"])
        
        # Search for files with "code" tag
        results = search_by_tags(["code"])
        self.assertEqual(len(results), 2)
        self.assertIn(file1, results)
        self.assertIn(file2, results)
        
        # Search for files with "python" tag
        results = search_by_tags(["python"])
        self.assertEqual(len(results), 1)
        self.assertIn(file1, results)
    
    def test_list_all_tags(self):
        """Test listing all unique tags"""
        file1 = os.path.join(self.test_dir, "file1.txt")
        file2 = os.path.join(self.test_dir, "file2.txt")
        
        with open(file1, 'w') as f:
            f.write("File 1")
        with open(file2, 'w') as f:
            f.write("File 2")
        
        add_tags(file1, ["python", "code", "test"])
        add_tags(file2, ["javascript", "code", "web"])
        
        all_tags = list_all_tags()
        expected_tags = {"python", "code", "test", "javascript", "web"}
        self.assertEqual(set(all_tags), expected_tags)
    
    def test_get_files_by_tag(self):
        """Test getting files by specific tag"""
        file1 = os.path.join(self.test_dir, "file1.py")
        file2 = os.path.join(self.test_dir, "file2.py")
        file3 = os.path.join(self.test_dir, "file3.js")
        
        for f in [file1, file2, file3]:
            with open(f, 'w') as file:
                file.write("Test content")
        
        add_tags(file1, ["python", "backend"])
        add_tags(file2, ["python", "frontend"])
        add_tags(file3, ["javascript", "frontend"])
        
        # Get files with "python" tag
        python_files = get_files_by_tag("python")
        self.assertEqual(len(python_files), 2)
        self.assertIn(file1, python_files)
        self.assertIn(file2, python_files)
        
        # Get files with "frontend" tag
        frontend_files = get_files_by_tag("frontend")
        self.assertEqual(len(frontend_files), 2)
        self.assertIn(file2, frontend_files)
        self.assertIn(file3, frontend_files)
    
    def test_load_save_tags(self):
        """Test loading and saving tags to JSON file"""
        test_data = {
            "/path/to/file1.py": ["python", "code"],
            "/path/to/file2.js": ["javascript", "web"]
        }
        
        # Save tags
        save_tags(test_data)
        
        # Load tags
        loaded_data = load_tags()
        
        self.assertEqual(loaded_data, test_data)
    
    def test_load_tags_empty_file(self):
        """Test loading tags from non-existent file"""
        # Remove the tags file if it exists
        if os.path.exists(self.test_tags_file):
            os.remove(self.test_tags_file)
        
        loaded_data = load_tags()
        self.assertEqual(loaded_data, {})
    
    def test_remove_invalid_paths(self):
        """Test removing invalid (non-existent) file paths from tags"""
        # Add tags for existing and non-existent files
        existing_file = self.test_file
        nonexistent_file = "/path/to/nonexistent/file.txt"
        
        test_data = {
            existing_file: ["python", "test"],
            nonexistent_file: ["invalid", "path"]
        }
        save_tags(test_data)
        
        # Remove invalid paths
        remove_invalid_paths()
        
        # Verify only existing file remains
        saved_tags = load_tags()
        self.assertIn(existing_file, saved_tags)
        self.assertNotIn(nonexistent_file, saved_tags)


class TestConfigurationManagement(unittest.TestCase):
    """Test cases for configuration management"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after tests"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_config_manager_import(self):
        """Test that config manager can be imported"""
        try:
            from tagmanager.config_manager import ConfigManager
            self.assertTrue(True)
        except ImportError:
            self.fail("ConfigManager could not be imported")
    
    def test_config_service_import(self):
        """Test that config service can be imported"""
        try:
            from tagmanager.app.config.service import get_config_value, set_config_value
            self.assertTrue(True)
        except ImportError:
            self.fail("Config service could not be imported")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
