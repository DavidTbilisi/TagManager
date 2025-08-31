#!/usr/bin/env python3
"""
Tests for handler functions - these are thin wrappers around services
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestAddHandler(unittest.TestCase):
    """Test add handler functions"""

    @patch('tagmanager.app.add.service.add_tags')
    def test_handle_add_command(self, mock_add_tags):
        """Test handle_add_command calls add_tags with correct arguments"""
        from tagmanager.app.add.handler import handle_add_command
        
        # Mock args object
        mock_args = MagicMock()
        mock_args.file = "/path/to/file.txt"
        mock_args.tags = ["python", "test"]
        
        # Execute
        handle_add_command(mock_args)
        
        # Verify
        mock_add_tags.assert_called_once_with("/path/to/file.txt", ["python", "test"])


class TestRemoveHandler(unittest.TestCase):
    """Test remove handler functions"""

    @patch('tagmanager.app.remove.service.remove_path')
    @patch('tagmanager.app.remove.service.remove_invalid_paths')
    def test_handle_remove_command_path(self, mock_remove_invalid, mock_remove_path):
        """Test handle_remove_command with path argument"""
        from tagmanager.app.remove.handler import handle_remove_command
        
        # Mock args object with path
        mock_args = MagicMock()
        mock_args.path = "/path/to/file.txt"
        mock_args.invalid = False
        
        # Execute
        result = handle_remove_command(mock_args)
        
        # Verify
        mock_remove_path.assert_called_once_with("/path/to/file.txt")
        mock_remove_invalid.assert_not_called()
        self.assertIsNone(result)

    @patch('tagmanager.app.remove.service.remove_path')
    @patch('tagmanager.app.remove.service.remove_invalid_paths')
    def test_handle_remove_command_invalid(self, mock_remove_invalid, mock_remove_path):
        """Test handle_remove_command with invalid flag"""
        from tagmanager.app.remove.handler import handle_remove_command
        
        # Mock args object with invalid flag
        mock_args = MagicMock()
        mock_args.path = None
        mock_args.invalid = True
        
        # Execute
        result = handle_remove_command(mock_args)
        
        # Verify
        mock_remove_invalid.assert_called_once()
        mock_remove_path.assert_not_called()
        self.assertIsNone(result)

    @patch('builtins.print')
    @patch('tagmanager.app.remove.service.remove_path')
    @patch('tagmanager.app.remove.service.remove_invalid_paths')
    def test_handle_remove_command_no_args(self, mock_remove_invalid, mock_remove_path, mock_print):
        """Test handle_remove_command with no arguments"""
        from tagmanager.app.remove.handler import handle_remove_command
        
        # Mock args object with no arguments
        mock_args = MagicMock()
        mock_args.path = None
        mock_args.invalid = False
        
        # Execute
        result = handle_remove_command(mock_args)
        
        # Verify
        mock_remove_path.assert_not_called()
        mock_remove_invalid.assert_not_called()
        mock_print.assert_called_once_with("No arguments provided")
        self.assertIsNone(result)


class TestSearchHandler(unittest.TestCase):
    """Test search handler functions"""

    @patch('builtins.print')
    @patch('tagmanager.app.search.service.search_files_by_tags')
    def test_handle_search_command_tags_only(self, mock_search, mock_print):
        """Test search by tags only"""
        from tagmanager.app.search.handler import handle_search_command
        
        # Mock return value
        mock_search.return_value = ["/path/file1.py", "/path/file2.py"]
        
        # Mock args object
        mock_args = MagicMock()
        mock_args.tags = ["python"]
        mock_args.path = None
        mock_args.match_all = False
        mock_args.exact = False
        
        # Execute
        handle_search_command(mock_args)
        
        # Verify
        mock_search.assert_called_once_with(["python"], False, False)
        # Check that results were printed
        self.assertTrue(mock_print.called)

    @patch('builtins.print')
    def test_handle_search_command_no_args(self, mock_print):
        """Test search with no arguments"""
        from tagmanager.app.search.handler import handle_search_command
        
        # Mock args object with no search criteria
        mock_args = MagicMock()
        mock_args.tags = None
        mock_args.path = None
        
        # Execute
        result = handle_search_command(mock_args)
        
        # Verify help message was printed
        self.assertTrue(mock_print.called)
        self.assertIsNone(result)


class TestTagsHandler(unittest.TestCase):
    """Test tags handler functions"""

    @patch('builtins.print')
    @patch('tagmanager.app.tags.service.list_all_tags')
    def test_handle_tags_command_list_all(self, mock_list_tags, mock_print):
        """Test listing all tags"""
        from tagmanager.app.tags.handler import handle_tags_command
        
        # Mock return value
        mock_list_tags.return_value = ["python", "javascript", "test"]
        
        # Mock args object for listing all tags
        mock_args = MagicMock()
        mock_args.search = None
        mock_args.open = False
        
        # Execute
        handle_tags_command(mock_args)
        
        # Verify
        mock_list_tags.assert_called_once()
        self.assertTrue(mock_print.called)

    @patch('builtins.print')
    @patch('tagmanager.app.tags.service.search_files_by_tag')
    def test_handle_tags_command_search(self, mock_search_by_tag, mock_print):
        """Test searching files by specific tag"""
        from tagmanager.app.tags.handler import handle_tags_command
        
        # Mock return value
        mock_search_by_tag.return_value = ["/path/file1.py"]
        
        # Mock args object for searching by tag
        mock_args = MagicMock()
        mock_args.search = "python"
        mock_args.open = False
        mock_args.exact = True
        
        # Execute
        handle_tags_command(mock_args)
        
        # Verify
        mock_search_by_tag.assert_called_once_with("python", True)
        self.assertTrue(mock_print.called)

    @patch('builtins.input', return_value='q')  # Mock user choosing to quit
    @patch('tagmanager.app.tags.handler.search_files_by_tag')
    def test_handle_tags_command_search_and_open(self, mock_search_by_tag, mock_input):
        """Test searching and opening files by tag"""
        from tagmanager.app.tags.handler import handle_tags_command
        
        # Mock return value
        mock_search_by_tag.return_value = ["/path/file1.py"]
        
        # Mock args object for searching and opening
        mock_args = MagicMock()
        mock_args.search = "python"
        mock_args.open = True
        mock_args.exact = False
        
        # Execute
        handle_tags_command(mock_args)
        
        # Verify
        mock_search_by_tag.assert_called_once_with("python", False)
        # Verify that input was called (user interaction)
        mock_input.assert_called_once()


if __name__ == '__main__':
    unittest.main()
