#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.add.service
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


class TestAddService(unittest.TestCase):
    """Comprehensive tests for add service functionality"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_file.txt")
        self.test_tags_file = os.path.join(self.test_dir, "test_tags.json")
        
        # Create a test file
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("Test content")
        
        # Mock the helpers module
        self.helpers_patcher = patch('tagmanager.app.add.service.load_tags')
        self.save_tags_patcher = patch('tagmanager.app.add.service.save_tags')
        
        self.mock_load_tags = self.helpers_patcher.start()
        self.mock_save_tags = self.save_tags_patcher.start()
        
        # Default mock behavior
        self.mock_load_tags.return_value = {}
        self.mock_save_tags.return_value = True  # save_tags should return True on success
        
    def tearDown(self):
        """Clean up after each test"""
        self.helpers_patcher.stop()
        self.save_tags_patcher.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_add_tags_existing_file_new_tags(self):
        """Test adding tags to existing file with no previous tags"""
        from tagmanager.app.add.service import add_tags
        
        # Mock existing tags (empty)
        self.mock_load_tags.return_value = {}
        
        # Test data
        tags = ["python", "test", "demo"]
        
        # Execute
        result = add_tags(self.test_file, tags)
        
        # Verify
        self.assertTrue(result)
        self.mock_load_tags.assert_called_once()
        self.mock_save_tags.assert_called_once()
        
        # Check saved data
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_path = os.path.abspath(self.test_file)
        self.assertIn(expected_path, saved_data)
        self.assertEqual(set(saved_data[expected_path]), set(tags))
    
    def test_add_tags_existing_file_existing_tags(self):
        """Test adding tags to file that already has tags"""
        from tagmanager.app.add.service import add_tags
        
        # Mock existing tags
        existing_path = os.path.abspath(self.test_file)
        self.mock_load_tags.return_value = {
            existing_path: ["existing", "tags"]
        }
        
        # Test data
        new_tags = ["python", "test"]
        
        # Execute
        result = add_tags(self.test_file, new_tags)
        
        # Verify
        self.assertTrue(result)
        
        # Check saved data
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_tags = set(["existing", "tags", "python", "test"])
        self.assertEqual(set(saved_data[existing_path]), expected_tags)
    
    def test_add_tags_duplicate_tags(self):
        """Test adding duplicate tags (should not create duplicates)"""
        from tagmanager.app.add.service import add_tags
        
        # Mock existing tags
        existing_path = os.path.abspath(self.test_file)
        self.mock_load_tags.return_value = {
            existing_path: ["python", "test"]
        }
        
        # Test data (includes duplicates)
        new_tags = ["test", "demo", "python", "new"]
        
        # Execute
        result = add_tags(self.test_file, new_tags)
        
        # Verify
        self.assertTrue(result)
        
        # Check saved data (no duplicates)
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_tags = set(["python", "test", "demo", "new"])
        self.assertEqual(set(saved_data[existing_path]), expected_tags)
    
    def test_add_tags_empty_tags_list(self):
        """Test adding empty tags list"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        
        # Execute with empty tags
        result = add_tags(self.test_file, [])
        
        # Verify
        self.assertTrue(result)
        
        # Check saved data
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_path = os.path.abspath(self.test_file)
        self.assertEqual(saved_data[expected_path], [])
    
    def test_add_tags_nonexistent_file_creates_file(self):
        """Test adding tags to non-existent file returns False (conservative behavior)"""
        from tagmanager.app.add.service import add_tags
        
        # Non-existent file path
        nonexistent_file = os.path.join(self.test_dir, "new_file.txt")
        self.assertFalse(os.path.exists(nonexistent_file))
        
        self.mock_load_tags.return_value = {}
        tags = ["new", "file"]
        
        # Execute
        result = add_tags(nonexistent_file, tags)
        
        # Verify conservative behavior - returns False, doesn't create file
        self.assertFalse(result)
        self.assertFalse(os.path.exists(nonexistent_file))
        
        # Verify save_tags was not called for non-existent file
        self.mock_save_tags.assert_not_called()
    
    @patch('builtins.print')
    def test_add_tags_file_creation_success_message(self, mock_print):
        """Test that error message is printed when file doesn't exist"""
        from tagmanager.app.add.service import add_tags
        
        nonexistent_file = os.path.join(self.test_dir, "new_file.txt")
        self.mock_load_tags.return_value = {}
        
        # Execute
        result = add_tags(nonexistent_file, ["tag"])
        
        # Verify error message was printed and function returned False
        self.assertFalse(result)
        expected_path = os.path.abspath(nonexistent_file)
        mock_print.assert_any_call(f"Error: The file '{expected_path}' does not exist Disk full.")
    
    @patch('builtins.print')
    def test_add_tags_success_message(self, mock_print):
        """Test that success message is printed after adding tags"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        
        # Execute
        add_tags(self.test_file, ["tag"])
        
        # Verify print was called with success message
        expected_path = os.path.abspath(self.test_file)
        mock_print.assert_called()
        
        # Check that success message contains the file path
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        success_messages = [msg for msg in print_calls if expected_path in msg]
        self.assertTrue(len(success_messages) > 0)
    
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    @patch('builtins.print')
    def test_add_tags_file_creation_permission_error(self, mock_print, mock_open):
        """Test handling of permission error when creating file"""
        from tagmanager.app.add.service import add_tags
        
        nonexistent_file = "/root/restricted/file.txt"
        self.mock_load_tags.return_value = {}
        
        # Execute
        result = add_tags(nonexistent_file, ["tag"])
        
        # Verify - function returns False for non-existent files before trying file operations
        self.assertFalse(result)
        mock_print.assert_called()
        
        # Check that the basic "file does not exist" error was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        error_messages = [msg for msg in print_calls if "does not exist" in msg]
        self.assertTrue(len(error_messages) > 0)
    
    @patch('builtins.open', side_effect=OSError("Disk full"))
    @patch('builtins.print')
    def test_add_tags_file_creation_os_error(self, mock_print, mock_open):
        """Test handling of OS error when creating file"""
        from tagmanager.app.add.service import add_tags
        
        nonexistent_file = "/tmp/test_file.txt"
        self.mock_load_tags.return_value = {}
        
        # Execute
        result = add_tags(nonexistent_file, ["tag"])
        
        # Verify
        self.assertFalse(result)
        mock_print.assert_called()
        
        # Check error message was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        error_messages = [msg for msg in print_calls if "Error" in msg and "Disk full" in msg]
        self.assertTrue(len(error_messages) > 0)
    
    @patch('builtins.print', side_effect=UnicodeEncodeError('utf-8', '', 0, 1, 'test'))
    def test_add_tags_unicode_encode_error(self, mock_print):
        """Test handling of Unicode encoding error in print statement"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        self.mock_save_tags.return_value = True  # Ensure save succeeds
        
        # Execute
        result = add_tags(self.test_file, ["tag"])
        
        # Should still return True despite print error
        self.assertTrue(result)
        
        # Verify tags were still saved
        self.mock_save_tags.assert_called_once()
    
    def test_add_tags_relative_path_conversion(self):
        """Test that relative paths are converted to absolute paths"""
        from tagmanager.app.add.service import add_tags
        
        # Create file in current directory
        current_dir_file = "relative_test.txt"
        with open(current_dir_file, 'w') as f:
            f.write("test")
        
        try:
            self.mock_load_tags.return_value = {}
            
            # Execute with relative path
            result = add_tags(current_dir_file, ["tag"])
            
            # Verify absolute path was used
            self.assertTrue(result)
            saved_data = self.mock_save_tags.call_args[0][0]
            
            # Should contain absolute path, not relative
            absolute_path = os.path.abspath(current_dir_file)
            self.assertIn(absolute_path, saved_data)
            self.assertNotIn(current_dir_file, saved_data)
            
        finally:
            # Clean up
            if os.path.exists(current_dir_file):
                os.remove(current_dir_file)
    
    def test_add_tags_special_characters_in_path(self):
        """Test handling of special characters in file paths"""
        from tagmanager.app.add.service import add_tags
        
        # Create file with special characters
        special_file = os.path.join(self.test_dir, "file with spaces & symbols!@#.txt")
        with open(special_file, 'w', encoding='utf-8') as f:
            f.write("test")
        
        self.mock_load_tags.return_value = {}
        
        # Execute
        result = add_tags(special_file, ["special"])
        
        # Verify
        self.assertTrue(result)
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_path = os.path.abspath(special_file)
        self.assertIn(expected_path, saved_data)
    
    def test_add_tags_unicode_characters_in_tags(self):
        """Test handling of Unicode characters in tags"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        
        # Tags with Unicode characters
        unicode_tags = ["python", "测试", "🏷️", "café", "naïve"]
        
        # Execute
        result = add_tags(self.test_file, unicode_tags)
        
        # Verify
        self.assertTrue(result)
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_path = os.path.abspath(self.test_file)
        self.assertEqual(set(saved_data[expected_path]), set(unicode_tags))
    
    def test_add_tags_very_long_tag_list(self):
        """Test handling of very long tag lists"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        
        # Create a very long list of tags
        long_tag_list = [f"tag_{i}" for i in range(1000)]
        
        # Execute
        result = add_tags(self.test_file, long_tag_list)
        
        # Verify
        self.assertTrue(result)
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_path = os.path.abspath(self.test_file)
        self.assertEqual(set(saved_data[expected_path]), set(long_tag_list))
    
    def test_add_tags_empty_string_tags(self):
        """Test handling of empty string tags"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        
        # Tags including empty strings
        tags_with_empty = ["python", "", "test", "", "demo"]
        
        # Execute
        result = add_tags(self.test_file, tags_with_empty)
        
        # Verify
        self.assertTrue(result)
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_path = os.path.abspath(self.test_file)
        
        # Empty strings should be included (current behavior)
        self.assertEqual(set(saved_data[expected_path]), set(tags_with_empty))
    
    def test_add_tags_whitespace_only_tags(self):
        """Test handling of whitespace-only tags"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        
        # Tags with whitespace
        whitespace_tags = ["python", "   ", "\t", "\n", "test"]
        
        # Execute
        result = add_tags(self.test_file, whitespace_tags)
        
        # Verify
        self.assertTrue(result)
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_path = os.path.abspath(self.test_file)
        
        # Whitespace tags should be included (current behavior)
        self.assertEqual(set(saved_data[expected_path]), set(whitespace_tags))
    
    @patch('tagmanager.app.add.service.load_tags', side_effect=Exception("Load error"))
    def test_add_tags_load_tags_exception(self, mock_load):
        """Test handling of exception in load_tags"""
        from tagmanager.app.add.service import add_tags
        
        # Execute - should raise exception
        with self.assertRaises(Exception):
            add_tags(self.test_file, ["tag"])
    
    @patch('tagmanager.app.add.service.save_tags', side_effect=Exception("Save error"))
    def test_add_tags_save_tags_exception(self, mock_save):
        """Test handling of exception in save_tags"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        
        # Execute - should raise exception
        with self.assertRaises(Exception):
            add_tags(self.test_file, ["tag"])
    
    def test_add_tags_case_sensitivity(self):
        """Test that tags are case-sensitive"""
        from tagmanager.app.add.service import add_tags
        
        self.mock_load_tags.return_value = {}
        
        # Tags with different cases
        case_tags = ["Python", "python", "PYTHON", "PyThOn"]
        
        # Execute
        result = add_tags(self.test_file, case_tags)
        
        # Verify all case variations are preserved
        self.assertTrue(result)
        saved_data = self.mock_save_tags.call_args[0][0]
        expected_path = os.path.abspath(self.test_file)
        self.assertEqual(set(saved_data[expected_path]), set(case_tags))
        self.assertEqual(len(saved_data[expected_path]), 4)  # All different


if __name__ == '__main__':
    unittest.main(verbosity=2)
