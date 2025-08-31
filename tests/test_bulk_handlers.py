#!/usr/bin/env python3
"""
Tests for bulk handler functions - comprehensive example
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestBulkHandlers(unittest.TestCase):
    """Test bulk handler functions with comprehensive coverage"""

    @patch('typer.echo')
    @patch('tagmanager.app.bulk.handler.format_bulk_result')
    @patch('tagmanager.app.bulk.handler.bulk_remove_by_tag')
    def test_handle_bulk_remove_with_tag(self, mock_bulk_remove_by_tag, mock_format_result, mock_echo):
        """Test handle_bulk_remove when removing files by tag"""
        from tagmanager.app.bulk.handler import handle_bulk_remove
        
        # Mock the service function return value
        mock_bulk_remove_by_tag.return_value = {
            'removed_files': ['/path/file1.py', '/path/file2.py'],
            'total_removed': 2
        }
        
        # Mock the formatter return value
        mock_format_result.return_value = "✅ Removed 2 files with tag 'deprecated'"
        
        # Execute - remove files with tag
        handle_bulk_remove(tag="deprecated", remove_tag=None, dry_run=False)
        
        # Verify service was called correctly
        mock_bulk_remove_by_tag.assert_called_once_with("deprecated", False)
        
        # Verify formatter was called with service result
        mock_format_result.assert_called_once_with({
            'removed_files': ['/path/file1.py', '/path/file2.py'],
            'total_removed': 2
        })
        
        # Verify output was displayed
        mock_echo.assert_called_once_with("✅ Removed 2 files with tag 'deprecated'")

    @patch('typer.echo')
    @patch('tagmanager.app.bulk.handler.format_bulk_result')
    @patch('tagmanager.app.bulk.handler.bulk_remove_tag_from_files')
    def test_handle_bulk_remove_with_remove_tag(self, mock_bulk_remove_tag, mock_format_result, mock_echo):
        """Test handle_bulk_remove when removing tag from all files"""
        from tagmanager.app.bulk.handler import handle_bulk_remove
        
        # Mock the service function return value
        mock_bulk_remove_tag.return_value = {
            'modified_files': ['/path/file1.py', '/path/file2.py', '/path/file3.js'],
            'total_modified': 3
        }
        
        # Mock the formatter return value
        mock_format_result.return_value = "✅ Removed tag 'old' from 3 files"
        
        # Execute - remove tag from files
        handle_bulk_remove(tag=None, remove_tag="old", dry_run=True)
        
        # Verify service was called correctly
        mock_bulk_remove_tag.assert_called_once_with("old", True)
        
        # Verify formatter was called with service result
        mock_format_result.assert_called_once_with({
            'modified_files': ['/path/file1.py', '/path/file2.py', '/path/file3.js'],
            'total_modified': 3
        })
        
        # Verify output was displayed
        mock_echo.assert_called_once_with("✅ Removed tag 'old' from 3 files")

    @patch('typer.echo')
    def test_handle_bulk_remove_no_arguments(self, mock_echo):
        """Test handle_bulk_remove when no arguments provided"""
        from tagmanager.app.bulk.handler import handle_bulk_remove
        
        # Execute - no arguments provided
        handle_bulk_remove(tag=None, remove_tag=None, dry_run=False)
        
        # Verify help messages were displayed
        expected_calls = [
            unittest.mock.call("❌ Specify either --tag (to remove files) or --remove-tag (to remove tag from files)."),
            unittest.mock.call("Examples:"),
            unittest.mock.call("  tm bulk remove --tag deprecated        # Remove all files with 'deprecated' tag"),
            unittest.mock.call("  tm bulk remove --remove-tag old        # Remove 'old' tag from all files")
        ]
        
        mock_echo.assert_has_calls(expected_calls)
        self.assertEqual(mock_echo.call_count, 4)

    @patch('typer.echo')
    @patch('tagmanager.app.bulk.handler.format_bulk_result')
    @patch('tagmanager.app.bulk.handler.bulk_remove_by_tag')
    def test_handle_bulk_remove_dry_run_mode(self, mock_bulk_remove_by_tag, mock_format_result, mock_echo):
        """Test handle_bulk_remove in dry-run mode"""
        from tagmanager.app.bulk.handler import handle_bulk_remove
        
        # Mock dry-run result
        mock_bulk_remove_by_tag.return_value = {
            'would_remove_files': ['/path/file1.py', '/path/file2.py'],
            'total_would_remove': 2,
            'dry_run': True
        }
        
        mock_format_result.return_value = "🔍 DRY RUN: Would remove 2 files with tag 'test'"
        
        # Execute - dry run mode
        handle_bulk_remove(tag="test", remove_tag=None, dry_run=True)
        
        # Verify dry_run=True was passed to service
        mock_bulk_remove_by_tag.assert_called_once_with("test", True)
        
        # Verify dry-run output was displayed
        mock_echo.assert_called_once_with("🔍 DRY RUN: Would remove 2 files with tag 'test'")

    @patch('typer.echo')
    @patch('tagmanager.app.bulk.handler.format_bulk_result')
    @patch('tagmanager.app.bulk.handler.bulk_remove_by_tag', side_effect=Exception("Service error"))
    def test_handle_bulk_remove_service_error(self, mock_bulk_remove_by_tag, mock_format_result, mock_echo):
        """Test handle_bulk_remove when service raises an exception"""
        from tagmanager.app.bulk.handler import handle_bulk_remove
        
        # Execute - should handle service exception gracefully
        with self.assertRaises(Exception) as context:
            handle_bulk_remove(tag="error", remove_tag=None, dry_run=False)
        
        # Verify the exception was raised
        self.assertEqual(str(context.exception), "Service error")
        
        # Verify service was called
        mock_bulk_remove_by_tag.assert_called_once_with("error", False)
        
        # Verify formatter and echo were not called due to exception
        mock_format_result.assert_not_called()
        mock_echo.assert_not_called()

    @patch('typer.echo')
    @patch('tagmanager.app.bulk.handler.format_bulk_result')
    @patch('tagmanager.app.bulk.handler.bulk_remove_by_tag')
    def test_handle_bulk_remove_empty_result(self, mock_bulk_remove_by_tag, mock_format_result, mock_echo):
        """Test handle_bulk_remove when no files are found/removed"""
        from tagmanager.app.bulk.handler import handle_bulk_remove
        
        # Mock empty result
        mock_bulk_remove_by_tag.return_value = {
            'removed_files': [],
            'total_removed': 0
        }
        
        mock_format_result.return_value = "ℹ️ No files found with tag 'nonexistent'"
        
        # Execute
        handle_bulk_remove(tag="nonexistent", remove_tag=None, dry_run=False)
        
        # Verify service was called
        mock_bulk_remove_by_tag.assert_called_once_with("nonexistent", False)
        
        # Verify appropriate message was displayed
        mock_echo.assert_called_once_with("ℹ️ No files found with tag 'nonexistent'")

    def test_handle_bulk_remove_parameter_validation(self):
        """Test that function accepts the expected parameter types"""
        from tagmanager.app.bulk.handler import handle_bulk_remove
        
        # Test that function exists and is callable
        self.assertTrue(callable(handle_bulk_remove))
        
        # Test function signature (this will fail if signature changes)
        import inspect
        sig = inspect.signature(handle_bulk_remove)
        params = list(sig.parameters.keys())
        
        # Verify expected parameters exist
        self.assertIn('tag', params)
        self.assertIn('remove_tag', params) 
        self.assertIn('dry_run', params)
        
        # Verify parameter defaults
        self.assertEqual(sig.parameters['tag'].default, None)
        self.assertEqual(sig.parameters['remove_tag'].default, None)
        self.assertEqual(sig.parameters['dry_run'].default, False)


if __name__ == '__main__':
    unittest.main()
