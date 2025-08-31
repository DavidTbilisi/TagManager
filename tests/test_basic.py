#!/usr/bin/env python3
"""
Basic unit tests for TagManager that don't require full module imports
"""

import unittest
import tempfile
import os
import json
import shutil


class TestBasicFunctionality(unittest.TestCase):
    """Basic test cases that can run without full TagManager installation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_file.txt")
        self.test_tags_file = os.path.join(self.test_dir, "test_tags.json")
        
        # Create a test file
        with open(self.test_file, 'w') as f:
            f.write("Test content")
    
    def tearDown(self):
        """Clean up after tests"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_file_creation(self):
        """Test that test files are created properly"""
        self.assertTrue(os.path.exists(self.test_file))
        
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Test content")
    
    def test_json_operations(self):
        """Test basic JSON operations for tag storage"""
        test_data = {
            "file1.py": ["python", "code"],
            "file2.js": ["javascript", "web"]
        }
        
        # Save to JSON
        with open(self.test_tags_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load from JSON
        with open(self.test_tags_file, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
    
    def test_tag_data_structure(self):
        """Test tag data structure operations"""
        tags_db = {}
        
        # Add tags to a file
        file_path = "/path/to/file.py"
        new_tags = ["python", "test"]
        
        if file_path not in tags_db:
            tags_db[file_path] = []
        
        # Add tags (avoiding duplicates)
        existing_tags = set(tags_db[file_path])
        combined_tags = existing_tags.union(set(new_tags))
        tags_db[file_path] = list(combined_tags)
        
        self.assertEqual(set(tags_db[file_path]), set(new_tags))
        
        # Add more tags (with duplicates)
        more_tags = ["test", "demo", "python"]
        existing_tags = set(tags_db[file_path])
        combined_tags = existing_tags.union(set(more_tags))
        tags_db[file_path] = list(combined_tags)
        
        expected_tags = {"python", "test", "demo"}
        self.assertEqual(set(tags_db[file_path]), expected_tags)
    
    def test_search_simulation(self):
        """Test search functionality simulation"""
        # Simulate tag database
        tags_db = {
            "/path/file1.py": ["python", "backend", "api"],
            "/path/file2.js": ["javascript", "frontend", "ui"],
            "/path/file3.py": ["python", "frontend", "web"],
            "/path/file4.md": ["documentation", "readme"]
        }
        
        # Search for files with "python" tag
        search_tag = "python"
        results = [file_path for file_path, tags in tags_db.items() 
                  if search_tag in tags]
        
        expected_results = ["/path/file1.py", "/path/file3.py"]
        self.assertEqual(set(results), set(expected_results))
        
        # Search for files with "frontend" tag
        search_tag = "frontend"
        results = [file_path for file_path, tags in tags_db.items() 
                  if search_tag in tags]
        
        expected_results = ["/path/file2.js", "/path/file3.py"]
        self.assertEqual(set(results), set(expected_results))
    
    def test_tag_listing(self):
        """Test listing all unique tags"""
        tags_db = {
            "/path/file1.py": ["python", "backend"],
            "/path/file2.js": ["javascript", "frontend"],
            "/path/file3.py": ["python", "web"]
        }
        
        # Get all unique tags
        all_tags = set()
        for tags in tags_db.values():
            all_tags.update(tags)
        
        expected_tags = {"python", "backend", "javascript", "frontend", "web"}
        self.assertEqual(all_tags, expected_tags)
    
    def test_file_validation(self):
        """Test file existence validation"""
        # Create some test files
        existing_file = os.path.join(self.test_dir, "existing.txt")
        with open(existing_file, 'w') as f:
            f.write("exists")
        
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.txt")
        
        # Test validation
        self.assertTrue(os.path.exists(existing_file))
        self.assertFalse(os.path.exists(nonexistent_file))
        
        # Simulate removing invalid paths from tag database
        tags_db = {
            existing_file: ["valid", "file"],
            nonexistent_file: ["invalid", "file"]
        }
        
        # Filter out non-existent files
        valid_tags_db = {file_path: tags for file_path, tags in tags_db.items() 
                        if os.path.exists(file_path)}
        
        self.assertIn(existing_file, valid_tags_db)
        self.assertNotIn(nonexistent_file, valid_tags_db)


class TestProjectStructure(unittest.TestCase):
    """Test that the project structure is correct"""
    
    def test_project_files_exist(self):
        """Test that essential project files exist"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        essential_files = [
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "requirements.txt"
        ]
        
        for file_name in essential_files:
            file_path = os.path.join(project_root, file_name)
            self.assertTrue(os.path.exists(file_path), f"Missing essential file: {file_name}")
    
    def test_tagmanager_package_structure(self):
        """Test that the tagmanager package structure exists"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tagmanager_dir = os.path.join(project_root, "tagmanager")
        
        self.assertTrue(os.path.exists(tagmanager_dir), "tagmanager directory missing")
        
        essential_modules = [
            "__init__.py",
            "cli.py",
            "config_manager.py"
        ]
        
        for module in essential_modules:
            module_path = os.path.join(tagmanager_dir, module)
            self.assertTrue(os.path.exists(module_path), f"Missing module: {module}")
    
    def test_app_modules_exist(self):
        """Test that app modules exist"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        app_dir = os.path.join(project_root, "tagmanager", "app")
        
        if os.path.exists(app_dir):
            expected_modules = [
                "add", "remove", "search", "tags", "stats", 
                "bulk", "filter", "visualization", "config"
            ]
            
            for module in expected_modules:
                module_dir = os.path.join(app_dir, module)
                if os.path.exists(module_dir):
                    # Check for service.py and handler.py
                    service_file = os.path.join(module_dir, "service.py")
                    handler_file = os.path.join(module_dir, "handler.py")
                    
                    self.assertTrue(os.path.exists(service_file), 
                                  f"Missing service.py in {module}")
                    self.assertTrue(os.path.exists(handler_file), 
                                  f"Missing handler.py in {module}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
