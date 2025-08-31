#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.remove.service
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


class TestRemoveService(unittest.TestCase):
    """Comprehensive tests for remove service functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        
        # Mock the helpers module
        self.helpers_patcher = patch('tagmanager.app.remove.service.load_tags')
        self.save_tags_patcher = patch('tagmanager.app.remove.service.save_tags')
        
        self.mock_load_tags = self.helpers_patcher.start()
        self.mock_save_tags = self.save_tags_patcher.start()
        
    def tearDown(self):
        """Clean up after each test"""
        self.helpers_patcher.stop()
        self.save_tags_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_remove_path_existing_path(self):
        """Test removing an existing path from tags"""
        from tagmanager.app.remove.service import remove_path
        
        # Mock existing tags with absolute paths (as remove_path uses os.path.abspath)
        test_path = os.path.abspath("/path/to/file.txt")
        other_path = os.path.abspath("/path/to/other.txt")
        self.mock_load_tags.return_value = {
            test_path: ["python", "test"],
            other_path: ["javascript", "web"]
        }
        
        # Execute with the same path (will be converted to absolute)
        remove_path("/path/to/file.txt")
        
        # Verify
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_called_once()
        
        # Check that only the target path was removed
        saved_data = self.mock_save_tags.call_args[0][0]
        self.assertNotIn(test_path, saved_data)
        self.assertIn(other_path, saved_data)
        self.assertEqual(saved_data[other_path], ["javascript", "web"])
    
    def test_remove_path_nonexistent_path(self):
        """Test removing a path that doesn't exist in tags"""
        from tagmanager.app.remove.service import remove_path
        
        # Mock existing tags (without target path)
        other_path = "/path/to/other.txt"
        self.mock_load_tags.return_value = {
            other_path: ["javascript", "web"]
        }
        
        nonexistent_path = "/path/to/nonexistent.txt"
        
        # Execute
        remove_path(nonexistent_path)
        
        # Verify - save_tags should NOT be called for nonexistent paths
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_not_called()
    
    def test_remove_path_empty_tags_database(self):
        """Test removing path from empty tags database"""
        from tagmanager.app.remove.service import remove_path
        
        # Mock empty tags
        self.mock_load_tags.return_value = {}
        
        # Execute
        remove_path("/any/path.txt")
        
        # Verify - save_tags should NOT be called for nonexistent paths
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_not_called()
    
    def test_remove_path_relative_path(self):
        """Test removing relative path (should be converted to absolute)"""
        from tagmanager.app.remove.service import remove_path
        
        # Create test file
        test_file = "test_file.txt"
        with open(test_file, 'w') as f:
            f.write("test")
        
        try:
            # Mock tags with absolute path
            absolute_path = os.path.abspath(test_file)
            self.mock_load_tags.return_value = {
                absolute_path: ["python", "test"]
            }
            
            # Execute with relative path
            remove_path(test_file)
            
            # Verify absolute path was removed
            saved_data = self.mock_save_tags.call_args[0][0]
            self.assertNotIn(absolute_path, saved_data)
            
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_remove_path_special_characters(self):
        """Test removing path with special characters"""
        from tagmanager.app.remove.service import remove_path
        
        # Path with special characters (use absolute paths)
        special_path_input = "/path/with spaces & symbols!@#/file.txt"
        normal_path_input = "/path/to/normal.txt"
        special_path = os.path.abspath(special_path_input)
        normal_path = os.path.abspath(normal_path_input)
        
        self.mock_load_tags.return_value = {
            special_path: ["special", "chars"],
            normal_path: ["normal", "file"]
        }
        
        # Execute
        remove_path(special_path_input)
        
        # Verify
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_called_once()
        saved_data = self.mock_save_tags.call_args[0][0]
        self.assertNotIn(special_path, saved_data)
        self.assertIn(normal_path, saved_data)
    
    def test_remove_path_unicode_characters(self):
        """Test removing path with Unicode characters"""
        from tagmanager.app.remove.service import remove_path
        
        # Path with Unicode characters (use absolute paths)
        unicode_path_input = "/路径/测试文件.txt"
        normal_path_input = "/path/to/normal.txt"
        unicode_path = os.path.abspath(unicode_path_input)
        normal_path = os.path.abspath(normal_path_input)
        
        self.mock_load_tags.return_value = {
            unicode_path: ["unicode", "测试"],
            normal_path: ["normal", "file"]
        }
        
        # Execute
        remove_path(unicode_path_input)
        
        # Verify
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_called_once()
        saved_data = self.mock_save_tags.call_args[0][0]
        self.assertNotIn(unicode_path, saved_data)
        self.assertIn(normal_path, saved_data)
    
    @patch('tagmanager.app.remove.service.load_tags', side_effect=Exception("Load error"))
    def test_remove_path_load_exception(self, mock_load):
        """Test handling of exception in load_tags"""
        from tagmanager.app.remove.service import remove_path
        
        # Execute - should raise exception
        with self.assertRaises(Exception):
            remove_path("/any/path.txt")
    
    @patch('tagmanager.app.remove.service.save_tags', side_effect=Exception("Save error"))
    def test_remove_path_save_exception(self, mock_save):
        """Test handling of exception in save_tags"""
        from tagmanager.app.remove.service import remove_path
        
        # Use absolute path that matches what remove_path will look for
        test_path = os.path.abspath("/path/file.txt")
        self.mock_load_tags.return_value = {test_path: ["tag"]}
        
        # Execute - should raise exception (propagated from save_tags)
        with self.assertRaises(Exception):
            remove_path("/path/file.txt")
        
        # Verify load was called
        self.mock_load_tags.assert_called_once()
    
    def test_remove_invalid_paths_mixed_validity(self):
        """Test removing invalid paths while keeping valid ones"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Create some test files
        valid_file1 = os.path.join(self.test_dir, "valid1.txt")
        valid_file2 = os.path.join(self.test_dir, "valid2.txt")
        
        with open(valid_file1, 'w') as f:
            f.write("valid1")
        with open(valid_file2, 'w') as f:
            f.write("valid2")
        
        # Mock tags with mix of valid and invalid paths
        invalid_path1 = "/nonexistent/path1.txt"
        invalid_path2 = "/nonexistent/path2.txt"
        
        self.mock_load_tags.return_value = {
            valid_file1: ["valid", "file1"],
            invalid_path1: ["invalid", "path1"],
            valid_file2: ["valid", "file2"],
            invalid_path2: ["invalid", "path2"]
        }
        
        # Execute
        remove_invalid_paths()
        
        # Verify
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_called_once()
        
        # Check that only valid paths remain
        saved_data = self.mock_save_tags.call_args[0][0]
        self.assertIn(valid_file1, saved_data)
        self.assertIn(valid_file2, saved_data)
        self.assertNotIn(invalid_path1, saved_data)
        self.assertNotIn(invalid_path2, saved_data)
    
    def test_remove_invalid_paths_all_valid(self):
        """Test remove_invalid_paths when all paths are valid"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Create test files
        valid_file1 = os.path.join(self.test_dir, "valid1.txt")
        valid_file2 = os.path.join(self.test_dir, "valid2.txt")
        
        with open(valid_file1, 'w') as f:
            f.write("valid1")
        with open(valid_file2, 'w') as f:
            f.write("valid2")
        
        # Mock tags with only valid paths
        self.mock_load_tags.return_value = {
            valid_file1: ["valid", "file1"],
            valid_file2: ["valid", "file2"]
        }
        
        # Execute
        remove_invalid_paths()
        
        # Verify - save_tags should NOT be called when no invalid paths exist
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_not_called()
    
    def test_remove_invalid_paths_all_invalid(self):
        """Test remove_invalid_paths when all paths are invalid"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Mock tags with only invalid paths
        self.mock_load_tags.return_value = {
            "/nonexistent/path1.txt": ["invalid", "path1"],
            "/nonexistent/path2.txt": ["invalid", "path2"],
            "/nonexistent/path3.txt": ["invalid", "path3"]
        }
        
        # Execute
        remove_invalid_paths()
        
        # Verify all paths are removed
        saved_data = self.mock_save_tags.call_args[0][0]
        self.assertEqual(saved_data, {})
    
    def test_remove_invalid_paths_empty_database(self):
        """Test remove_invalid_paths with empty tags database"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Mock empty tags
        self.mock_load_tags.return_value = {}
        
        # Execute
        remove_invalid_paths()
        
        # Verify - save_tags should NOT be called when database is empty
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_not_called()
    
    def test_remove_invalid_paths_symlinks(self):
        """Test remove_invalid_paths with symbolic links"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Create a real file and a symlink
        real_file = os.path.join(self.test_dir, "real_file.txt")
        with open(real_file, 'w') as f:
            f.write("real content")
        
        # Create symlink (if supported)
        symlink_file = os.path.join(self.test_dir, "symlink_file.txt")
        try:
            os.symlink(real_file, symlink_file)
            symlink_created = True
        except (OSError, NotImplementedError):
            # Symlinks not supported on this system
            symlink_created = False
        
        if symlink_created:
            # Mock tags with real file and symlink
            self.mock_load_tags.return_value = {
                real_file: ["real", "file"],
                symlink_file: ["symlink", "file"]
            }
            
            # Execute
            remove_invalid_paths()
            
            # Verify both are preserved (symlinks should be valid)
            saved_data = self.mock_save_tags.call_args[0][0]
            self.assertIn(real_file, saved_data)
            self.assertIn(symlink_file, saved_data)
    
    def test_remove_invalid_paths_broken_symlinks(self):
        """Test remove_invalid_paths with broken symbolic links"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Create a symlink to a non-existent file
        real_file = os.path.join(self.test_dir, "temp_file.txt")
        symlink_file = os.path.join(self.test_dir, "broken_symlink.txt")
        
        try:
            # Create real file, create symlink, then delete real file
            with open(real_file, 'w') as f:
                f.write("temp")
            os.symlink(real_file, symlink_file)
            os.remove(real_file)  # Now symlink is broken
            
            symlink_created = True
        except (OSError, NotImplementedError):
            symlink_created = False
        
        if symlink_created:
            # Mock tags with broken symlink
            self.mock_load_tags.return_value = {
                symlink_file: ["broken", "symlink"]
            }
            
            # Execute
            remove_invalid_paths()
            
            # Verify broken symlink is removed
            saved_data = self.mock_save_tags.call_args[0][0]
            self.assertNotIn(symlink_file, saved_data)
    
    @patch('os.path.exists', side_effect=OSError("Permission denied"))
    def test_remove_invalid_paths_permission_error(self, mock_exists):
        """Test remove_invalid_paths with permission errors"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Mock tags
        self.mock_load_tags.return_value = {
            "/restricted/file.txt": ["restricted", "file"]
        }
        
        # Execute - should raise the permission error (not handled gracefully)
        with self.assertRaises(OSError):
            remove_invalid_paths()
        
        # Verify load was called
        self.mock_load_tags.assert_called_once()
    
    @patch('tagmanager.app.remove.service.load_tags', side_effect=Exception("Load error"))
    def test_remove_invalid_paths_load_exception(self, mock_load):
        """Test handling of exception in load_tags for remove_invalid_paths"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Execute - should raise exception
        with self.assertRaises(Exception):
            remove_invalid_paths()
    
    @patch('tagmanager.app.remove.service.save_tags', side_effect=Exception("Save error"))
    def test_remove_invalid_paths_save_exception(self, mock_save):
        """Test handling of exception in save_tags for remove_invalid_paths"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        self.mock_load_tags.return_value = {"/path/file.txt": ["tag"]}
        
        # Execute - should raise exception
        with self.assertRaises(Exception):
            remove_invalid_paths()
    
    def test_remove_invalid_paths_large_database(self):
        """Test remove_invalid_paths with large number of paths"""
        from tagmanager.app.remove.service import remove_invalid_paths
        
        # Create a few valid files
        valid_files = []
        for i in range(5):
            valid_file = os.path.join(self.test_dir, f"valid_{i}.txt")
            with open(valid_file, 'w') as f:
                f.write(f"content {i}")
            valid_files.append(valid_file)
        
        # Create large database with mix of valid and invalid
        large_db = {}
        
        # Add valid files
        for i, valid_file in enumerate(valid_files):
            large_db[valid_file] = [f"valid_{i}"]
        
        # Add many invalid files
        for i in range(1000):
            invalid_path = f"/nonexistent/path_{i}.txt"
            large_db[invalid_path] = [f"invalid_{i}"]
        
        self.mock_load_tags.return_value = large_db
        
        # Execute
        remove_invalid_paths()
        
        # Verify only valid files remain
        saved_data = self.mock_save_tags.call_args[0][0]
        self.assertEqual(len(saved_data), 5)
        
        for valid_file in valid_files:
            self.assertIn(valid_file, saved_data)
    
    def test_remove_path_case_sensitivity(self):
        """Test that path removal is case-sensitive on case-sensitive filesystems"""
        from tagmanager.app.remove.service import remove_path
        
        # Paths with different cases (use absolute paths)
        lower_path_input = "/path/to/file.txt"
        upper_path_input = "/PATH/TO/FILE.TXT"
        mixed_path_input = "/Path/To/File.txt"
        lower_path = os.path.abspath(lower_path_input)
        upper_path = os.path.abspath(upper_path_input)
        mixed_path = os.path.abspath(mixed_path_input)
        
        self.mock_load_tags.return_value = {
            lower_path: ["lower"],
            upper_path: ["upper"],
            mixed_path: ["mixed"]
        }
        
        # Execute - remove only lower case
        remove_path(lower_path_input)
        
        # Verify only exact match is removed
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_called_once()
        saved_data = self.mock_save_tags.call_args[0][0]
        self.assertNotIn(lower_path, saved_data)
        self.assertIn(upper_path, saved_data)
        self.assertIn(mixed_path, saved_data)


if __name__ == '__main__':
    unittest.main(verbosity=2)
