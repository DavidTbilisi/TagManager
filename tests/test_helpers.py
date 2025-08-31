#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.helpers
Testing every function, edge case, and error condition
"""

import unittest
import tempfile
import os
import json
import shutil
import sys
from unittest.mock import patch, mock_open, MagicMock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestHelpers(unittest.TestCase):
    """Comprehensive tests for helpers functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_tags_file = os.path.join(self.test_dir, "test_tags.json")
        
    def tearDown(self):
        """Clean up after each test"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_load_tags_existing_file(self, mock_tag_file):
        """Test loading tags from existing file"""
        from tagmanager.app.helpers import load_tags
        
        # Set up mock file path
        mock_tag_file.__str__ = lambda: self.test_tags_file
        mock_tag_file.__fspath__ = lambda: self.test_tags_file
        
        # Create test data
        test_data = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        
        # Write test data to file
        with open(self.test_tags_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Mock TAG_FILE to point to our test file
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            result = load_tags()
        
        # Verify
        self.assertEqual(result, test_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_load_tags_nonexistent_file(self, mock_tag_file):
        """Test loading tags from non-existent file"""
        from tagmanager.app.helpers import load_tags
        
        # Point to non-existent file
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.json")
        
        with patch('tagmanager.app.helpers.TAG_FILE', nonexistent_file):
            # Execute
            result = load_tags()
        
        # Verify returns empty dict
        self.assertEqual(result, {})
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_load_tags_empty_file(self, mock_tag_file):
        """Test loading tags from empty file"""
        from tagmanager.app.helpers import load_tags
        
        # Create empty file
        with open(self.test_tags_file, 'w') as f:
            pass  # Empty file
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            result = load_tags()
        
        # Verify returns empty dict (JSON decode should fail gracefully)
        self.assertEqual(result, {})
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_load_tags_invalid_json(self, mock_tag_file):
        """Test loading tags from file with invalid JSON"""
        from tagmanager.app.helpers import load_tags
        
        # Create file with invalid JSON
        with open(self.test_tags_file, 'w') as f:
            f.write("invalid json content {")
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute - should handle JSON decode error gracefully
            result = load_tags()
        
        # Verify returns empty dict
        self.assertEqual(result, {})
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_load_tags_unicode_content(self, mock_tag_file):
        """Test loading tags with Unicode content"""
        from tagmanager.app.helpers import load_tags
        
        # Test data with Unicode
        test_data = {
            "/路径/文件.py": ["python", "测试", "🏷️"],
            "/path/café.js": ["javascript", "naïve", "résumé"]
        }
        
        # Write test data to file
        with open(self.test_tags_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            result = load_tags()
        
        # Verify Unicode is preserved
        self.assertEqual(result, test_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_load_tags_large_file(self, mock_tag_file):
        """Test loading tags from large file"""
        from tagmanager.app.helpers import load_tags
        
        # Create large test data
        large_data = {}
        for i in range(10000):
            file_path = f"/path/file_{i}.py"
            tags = [f"tag_{j}" for j in range(10)]  # 10 tags per file
            large_data[file_path] = tags
        
        # Write large data to file
        with open(self.test_tags_file, 'w', encoding='utf-8') as f:
            json.dump(large_data, f)
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            result = load_tags()
        
        # Verify large data is loaded correctly
        self.assertEqual(len(result), 10000)
        self.assertEqual(result["/path/file_0.py"], ["tag_0", "tag_1", "tag_2", "tag_3", "tag_4", "tag_5", "tag_6", "tag_7", "tag_8", "tag_9"])
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_load_tags_permission_error(self, mock_tag_file, mock_open):
        """Test loading tags with permission error"""
        from tagmanager.app.helpers import load_tags
        
        with patch('tagmanager.app.helpers.TAG_FILE', "/restricted/file.json"):
            # Execute - should handle permission error gracefully
            result = load_tags()
        
        # Verify returns empty dict
        self.assertEqual(result, {})
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_new_file(self, mock_tag_file):
        """Test saving tags to new file"""
        from tagmanager.app.helpers import save_tags
        
        # Test data
        test_data = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            save_tags(test_data)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(self.test_tags_file))
        
        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_overwrite_existing(self, mock_tag_file):
        """Test saving tags overwrites existing file"""
        from tagmanager.app.helpers import save_tags
        
        # Create existing file with old data
        old_data = {"/old/file.py": ["old", "tags"]}
        with open(self.test_tags_file, 'w', encoding='utf-8') as f:
            json.dump(old_data, f)
        
        # New data to save
        new_data = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"]
        }
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            save_tags(new_data)
        
        # Verify old data is overwritten
        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, new_data)
        self.assertNotEqual(saved_data, old_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_empty_data(self, mock_tag_file):
        """Test saving empty tags data"""
        from tagmanager.app.helpers import save_tags
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            save_tags({})
        
        # Verify empty dict is saved
        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, {})
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_unicode_data(self, mock_tag_file):
        """Test saving tags with Unicode data"""
        from tagmanager.app.helpers import save_tags
        
        # Test data with Unicode
        unicode_data = {
            "/路径/文件.py": ["python", "测试", "🏷️"],
            "/path/café.js": ["javascript", "naïve", "résumé"]
        }
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            save_tags(unicode_data)
        
        # Verify Unicode is preserved
        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, unicode_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_special_characters(self, mock_tag_file):
        """Test saving tags with special characters"""
        from tagmanager.app.helpers import save_tags
        
        # Test data with special characters
        special_data = {
            "/path/file with spaces.py": ["python-3", "web@dev"],
            "/path/file&symbols!.js": ["node.js", "front-end"],
            "/path/file[brackets].css": ["css3", "style/sheet"]
        }
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            save_tags(special_data)
        
        # Verify special characters are preserved
        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, special_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_large_data(self, mock_tag_file):
        """Test saving large amount of tags data"""
        from tagmanager.app.helpers import save_tags
        
        # Create large test data
        large_data = {}
        for i in range(10000):
            file_path = f"/path/file_{i}.py"
            tags = [f"tag_{j}" for j in range(10)]
            large_data[file_path] = tags
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute
            save_tags(large_data)
        
        # Verify large data is saved correctly
        with open(self.test_tags_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(len(saved_data), 10000)
        self.assertEqual(saved_data, large_data)
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_permission_error(self, mock_tag_file, mock_open):
        """Test saving tags with permission error"""
        from tagmanager.app.helpers import save_tags
        
        test_data = {"/path/file.py": ["python"]}
        
        with patch('tagmanager.app.helpers.TAG_FILE', "/restricted/file.json"):
            # Execute - should raise exception
            with self.assertRaises(PermissionError):
                save_tags(test_data)
    
    @patch('builtins.open', side_effect=OSError("Disk full"))
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_os_error(self, mock_tag_file, mock_open):
        """Test saving tags with OS error"""
        from tagmanager.app.helpers import save_tags
        
        test_data = {"/path/file.py": ["python"]}
        
        with patch('tagmanager.app.helpers.TAG_FILE', "/full/disk/file.json"):
            # Execute - should raise exception
            with self.assertRaises(OSError):
                save_tags(test_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_directory_creation(self, mock_tag_file):
        """Test saving tags creates directory if it doesn't exist"""
        from tagmanager.app.helpers import save_tags
        
        # Point to file in non-existent directory
        nested_dir = os.path.join(self.test_dir, "nested", "deep", "directory")
        nested_file = os.path.join(nested_dir, "tags.json")
        
        test_data = {"/path/file.py": ["python"]}
        
        with patch('tagmanager.app.helpers.TAG_FILE', nested_file):
            # Execute
            save_tags(test_data)
        
        # Verify directory was created and file exists
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(nested_file))
        
        # Verify data was saved correctly
        with open(nested_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_save_tags_json_serialization_error(self, mock_tag_file):
        """Test saving tags with non-serializable data"""
        from tagmanager.app.helpers import save_tags
        
        # Data that can't be JSON serialized
        non_serializable_data = {
            "/path/file.py": [lambda x: x]  # Function can't be serialized
        }
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Execute - should raise TypeError
            with self.assertRaises(TypeError):
                save_tags(non_serializable_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_load_save_roundtrip(self, mock_tag_file):
        """Test that load and save operations are consistent"""
        from tagmanager.app.helpers import load_tags, save_tags
        
        # Original test data
        original_data = {
            "/path/file1.py": ["python", "backend", "api"],
            "/path/file2.js": ["javascript", "frontend", "web"],
            "/path/file3.md": ["documentation", "readme"],
            "/path/unicode.py": ["测试", "🏷️", "café"]
        }
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Save data
            save_tags(original_data)
            
            # Load data back
            loaded_data = load_tags()
        
        # Verify roundtrip consistency
        self.assertEqual(loaded_data, original_data)
    
    @patch('tagmanager.app.helpers.TAG_FILE')
    def test_concurrent_access_simulation(self, mock_tag_file):
        """Test behavior with simulated concurrent access"""
        from tagmanager.app.helpers import load_tags, save_tags
        
        # Initial data
        initial_data = {"/path/file1.py": ["python"]}
        
        with patch('tagmanager.app.helpers.TAG_FILE', self.test_tags_file):
            # Save initial data
            save_tags(initial_data)
            
            # Load data (simulating one process)
            loaded_data1 = load_tags()
            
            # Modify and save (simulating another process)
            modified_data = {"/path/file2.py": ["javascript"]}
            save_tags(modified_data)
            
            # Load again (simulating first process)
            loaded_data2 = load_tags()
        
        # Verify behavior
        self.assertEqual(loaded_data1, initial_data)
        self.assertEqual(loaded_data2, modified_data)  # Should see the changes
    
    def test_tag_file_path_configuration(self):
        """Test that TAG_FILE path can be configured"""
        from tagmanager.app.helpers import get_tag_file_path
        
        # This tests the configuration system integration
        # The actual path depends on configuration
        tag_file_path = get_tag_file_path()
        
        # Verify it returns a valid path string
        self.assertIsInstance(tag_file_path, str)
        self.assertTrue(len(tag_file_path) > 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
