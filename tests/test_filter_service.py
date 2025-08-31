#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.filter.service
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


class TestFilterService(unittest.TestCase):
    """Comprehensive tests for filter service functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create isolated tag file for this test
        self.test_tag_file = os.path.join(self.test_dir, "test_tags.json")
        
        # Patch the TAG_FILE to use our test file
        self.tag_file_patcher = patch('tagmanager.app.helpers.TAG_FILE', self.test_tag_file)
        self.tag_file_patcher.start()
        
        # Clear any existing tag data before each test
        from tagmanager.app.helpers import save_tags
        save_tags({})  # Start with clean tag data

    def tearDown(self):
        """Clean up"""
        self.tag_file_patcher.stop()
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _setup_test_data(self):
        """Setup common test data"""
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/path/to/file1.py": ["python", "backend", "api"],
            "/path/to/file2.py": ["python", "backend", "api"],  # Duplicate of file1
            "/path/to/file3.js": ["javascript", "frontend", "react"],
            "/path/to/file4.py": ["python", "frontend", "web"],
            "/path/to/file5.txt": ["documentation", "readme"],
            "/path/to/file6.md": [],  # Orphan file
            "/path/to/file7.css": ["css", "styling"],
            "/path/to/file8.py": ["python", "backend"],  # Similar to file1
        }
        save_tags(test_data)
        return test_data

    # =================================================================
    # Tests for find_duplicate_tags
    # =================================================================

    def test_find_duplicate_tags_success(self):
        """Test finding duplicate tag sets"""
        from tagmanager.app.filter.service import find_duplicate_tags
        
        self._setup_test_data()
        
        result = find_duplicate_tags()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["duplicate_groups"], 1)  # Only file1 and file2 have identical tags
        self.assertEqual(result["total_files"], 8)
        self.assertGreater(result["duplicate_files_count"], 1)
        
        # Check that file1 and file2 are in the duplicates
        duplicates = result["duplicates"]
        python_backend_api = ("api", "backend", "python")  # Sorted tuple
        self.assertIn(python_backend_api, duplicates)
        duplicate_files = duplicates[python_backend_api]
        self.assertEqual(len(duplicate_files), 2)

    def test_find_duplicate_tags_empty_database(self):
        """Test duplicate finding with empty database"""
        from tagmanager.app.filter.service import find_duplicate_tags
        
        result = find_duplicate_tags()
        
        self.assertFalse(result["success"])
        self.assertIn("No tagged files found", result["message"])
        self.assertEqual(result["duplicate_groups"], 0)

    def test_find_duplicate_tags_no_duplicates(self):
        """Test when no duplicates exist"""
        from tagmanager.app.filter.service import find_duplicate_tags
        from tagmanager.app.helpers import save_tags
        
        # Setup data with all unique tag sets
        test_data = {
            "/file1.py": ["python"],
            "/file2.js": ["javascript"],
            "/file3.txt": ["text"],
        }
        save_tags(test_data)
        
        result = find_duplicate_tags()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["duplicate_groups"], 0)
        self.assertEqual(result["duplicate_files_count"], 0)

    def test_find_duplicate_tags_empty_tag_sets(self):
        """Test finding duplicates including empty tag sets"""
        from tagmanager.app.filter.service import find_duplicate_tags
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/file1.txt": [],
            "/file2.txt": [],
            "/file3.py": ["python"],
        }
        save_tags(test_data)
        
        result = find_duplicate_tags()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["duplicate_groups"], 1)  # Two files with empty tags
        
        # Check empty tag duplicates
        duplicates = result["duplicates"]
        empty_tuple = ()
        self.assertIn(empty_tuple, duplicates)
        self.assertEqual(len(duplicates[empty_tuple]), 2)

    # =================================================================
    # Tests for find_orphaned_files
    # =================================================================

    def test_find_orphaned_files_success(self):
        """Test finding orphaned files"""
        from tagmanager.app.filter.service import find_orphaned_files
        
        self._setup_test_data()
        
        result = find_orphaned_files()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["orphan_count"], 1)  # Only file6.md has no tags
        self.assertEqual(result["total_files"], 8)
        self.assertIn("/path/to/file6.md", result["orphans"])

    def test_find_orphaned_files_empty_database(self):
        """Test orphan finding with empty database"""
        from tagmanager.app.filter.service import find_orphaned_files
        
        result = find_orphaned_files()
        
        self.assertFalse(result["success"])
        self.assertIn("No files found", result["message"])
        self.assertEqual(result["orphan_count"], 0)

    def test_find_orphaned_files_no_orphans(self):
        """Test when no orphaned files exist"""
        from tagmanager.app.filter.service import find_orphaned_files
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/file1.py": ["python"],
            "/file2.js": ["javascript"],
        }
        save_tags(test_data)
        
        result = find_orphaned_files()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["orphan_count"], 0)
        self.assertEqual(len(result["orphans"]), 0)

    def test_find_orphaned_files_all_orphans(self):
        """Test when all files are orphans"""
        from tagmanager.app.filter.service import find_orphaned_files
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/file1.txt": [],
            "/file2.txt": [],
        }
        save_tags(test_data)
        
        result = find_orphaned_files()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["orphan_count"], 2)
        self.assertEqual(len(result["orphans"]), 2)

    # =================================================================
    # Tests for calculate_tag_similarity
    # =================================================================

    def test_calculate_tag_similarity_identical(self):
        """Test similarity calculation for identical tag sets"""
        from tagmanager.app.filter.service import calculate_tag_similarity
        
        tags1 = ["python", "backend", "api"]
        tags2 = ["python", "backend", "api"]
        
        similarity = calculate_tag_similarity(tags1, tags2)
        self.assertEqual(similarity, 1.0)

    def test_calculate_tag_similarity_no_overlap(self):
        """Test similarity calculation for completely different tag sets"""
        from tagmanager.app.filter.service import calculate_tag_similarity
        
        tags1 = ["python", "backend"]
        tags2 = ["javascript", "frontend"]
        
        similarity = calculate_tag_similarity(tags1, tags2)
        self.assertEqual(similarity, 0.0)

    def test_calculate_tag_similarity_partial_overlap(self):
        """Test similarity calculation for partial overlap"""
        from tagmanager.app.filter.service import calculate_tag_similarity
        
        tags1 = ["python", "backend", "api"]      # 3 tags
        tags2 = ["python", "frontend", "web"]     # 3 tags, 1 common = 1/5 = 0.2
        
        similarity = calculate_tag_similarity(tags1, tags2)
        self.assertAlmostEqual(similarity, 0.2, places=2)

    def test_calculate_tag_similarity_empty_tags(self):
        """Test similarity calculation with empty tag sets"""
        from tagmanager.app.filter.service import calculate_tag_similarity
        
        # Both empty
        self.assertEqual(calculate_tag_similarity([], []), 1.0)
        
        # One empty
        self.assertEqual(calculate_tag_similarity(["python"], []), 0.0)
        self.assertEqual(calculate_tag_similarity([], ["python"]), 0.0)

    def test_calculate_tag_similarity_case_insensitive(self):
        """Test that similarity calculation is case-insensitive"""
        from tagmanager.app.filter.service import calculate_tag_similarity
        
        tags1 = ["Python", "Backend"]
        tags2 = ["python", "backend", "api"]
        
        similarity = calculate_tag_similarity(tags1, tags2)
        # 2 common out of 3 total = 2/3 ≈ 0.67
        self.assertAlmostEqual(similarity, 2/3, places=2)

    # =================================================================
    # Tests for find_similar_files
    # =================================================================

    def test_find_similar_files_success(self):
        """Test finding similar files"""
        from tagmanager.app.filter.service import find_similar_files
        
        self._setup_test_data()
        
        # Find files similar to file1.py
        result = find_similar_files("/path/to/file1.py", similarity_threshold=0.3)
        
        self.assertTrue(result["success"])
        self.assertGreater(len(result["similar_files"]), 0)
        self.assertEqual(result["target_tags"], ["python", "backend", "api"])
        
        # Check that similar files are sorted by similarity
        similarities = [f["similarity"] for f in result["similar_files"]]
        self.assertEqual(similarities, sorted(similarities, reverse=True))

    def test_find_similar_files_target_not_found(self):
        """Test similar files when target file not found"""
        from tagmanager.app.filter.service import find_similar_files
        
        self._setup_test_data()
        
        result = find_similar_files("/nonexistent/file.py")
        
        self.assertFalse(result["success"])
        self.assertIn("Target file not found", result["message"])
        self.assertEqual(len(result["similar_files"]), 0)

    def test_find_similar_files_target_no_tags(self):
        """Test similar files when target file has no tags"""
        from tagmanager.app.filter.service import find_similar_files
        
        self._setup_test_data()
        
        result = find_similar_files("/path/to/file6.md")  # The orphan file
        
        self.assertFalse(result["success"])
        self.assertIn("Target file has no tags", result["message"])

    def test_find_similar_files_empty_database(self):
        """Test similar files with empty database"""
        from tagmanager.app.filter.service import find_similar_files
        
        result = find_similar_files("/any/file.py")
        
        self.assertFalse(result["success"])
        self.assertIn("No tagged files found", result["message"])

    def test_find_similar_files_high_threshold(self):
        """Test similar files with high threshold (no matches)"""
        from tagmanager.app.filter.service import find_similar_files
        
        self._setup_test_data()
        
        result = find_similar_files("/path/to/file1.py", similarity_threshold=0.99)
        
        self.assertTrue(result["success"])
        # Should only find file2.py (exact duplicate)
        self.assertEqual(len(result["similar_files"]), 1)

    def test_find_similar_files_case_insensitive_path(self):
        """Test that file path matching is case-insensitive"""
        from tagmanager.app.filter.service import find_similar_files
        
        self._setup_test_data()
        
        # Try with different case
        result = find_similar_files("/PATH/TO/FILE1.PY", similarity_threshold=0.3)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["target_tags"], ["python", "backend", "api"])

    # =================================================================
    # Tests for find_tag_clusters
    # =================================================================

    def test_find_tag_clusters_success(self):
        """Test finding tag clusters"""
        from tagmanager.app.filter.service import find_tag_clusters
        
        self._setup_test_data()
        
        result = find_tag_clusters(min_cluster_size=2)
        
        self.assertTrue(result["success"])
        self.assertGreater(len(result["clusters"]), 0)
        self.assertEqual(result["total_files"], 8)
        
        # Check that python is a cluster (appears in multiple files)
        clusters = result["clusters"]
        self.assertIn("python", clusters)
        self.assertGreaterEqual(clusters["python"]["file_count"], 2)

    def test_find_tag_clusters_empty_database(self):
        """Test cluster finding with empty database"""
        from tagmanager.app.filter.service import find_tag_clusters
        
        result = find_tag_clusters()
        
        self.assertFalse(result["success"])
        self.assertIn("No tagged files found", result["message"])

    def test_find_tag_clusters_high_min_size(self):
        """Test cluster finding with high minimum cluster size"""
        from tagmanager.app.filter.service import find_tag_clusters
        
        self._setup_test_data()
        
        result = find_tag_clusters(min_cluster_size=10)  # Higher than any possible cluster
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["clusters"]), 0)

    def test_find_tag_clusters_sorted_by_size(self):
        """Test that clusters are sorted by file count"""
        from tagmanager.app.filter.service import find_tag_clusters
        
        self._setup_test_data()
        
        result = find_tag_clusters(min_cluster_size=2)
        
        if result["clusters"]:
            file_counts = [cluster["file_count"] for cluster in result["clusters"].values()]
            self.assertEqual(file_counts, sorted(file_counts, reverse=True))

    def test_find_tag_clusters_percentage_calculation(self):
        """Test that cluster percentages are calculated correctly"""
        from tagmanager.app.filter.service import find_tag_clusters
        
        self._setup_test_data()
        
        result = find_tag_clusters(min_cluster_size=2)
        
        if "python" in result["clusters"]:
            python_cluster = result["clusters"]["python"]
            expected_percentage = (python_cluster["file_count"] / result["total_files"]) * 100
            self.assertAlmostEqual(python_cluster["percentage"], expected_percentage, places=1)

    # =================================================================
    # Tests for find_isolated_files
    # =================================================================

    def test_find_isolated_files_success(self):
        """Test finding isolated files"""
        from tagmanager.app.filter.service import find_isolated_files
        from tagmanager.app.helpers import save_tags
        
        # Setup data with some isolated files
        test_data = {
            "/file1.py": ["python", "common"],
            "/file2.py": ["python", "common"],      # Not isolated - shares 2 tags
            "/file3.js": ["javascript", "unique"],  # Isolated - shares at most 0 tags
            "/file4.css": ["css", "styling"],       # Isolated - shares at most 0 tags
        }
        save_tags(test_data)
        
        result = find_isolated_files(max_shared_tags=1)
        
        self.assertTrue(result["success"])
        self.assertGreater(len(result["isolated_files"]), 0)
        
        # Check that isolated files have low shared tag counts
        for isolated in result["isolated_files"]:
            self.assertLessEqual(isolated["max_shared_tags"], 1)

    def test_find_isolated_files_empty_database(self):
        """Test isolated files finding with empty database"""
        from tagmanager.app.filter.service import find_isolated_files
        
        result = find_isolated_files()
        
        self.assertFalse(result["success"])
        self.assertIn("No tagged files found", result["message"])

    def test_find_isolated_files_no_isolated(self):
        """Test when no files are isolated"""
        from tagmanager.app.filter.service import find_isolated_files
        from tagmanager.app.helpers import save_tags
        
        # All files share multiple tags
        test_data = {
            "/file1.py": ["common", "tag1"],
            "/file2.py": ["common", "tag2"],
            "/file3.py": ["common", "tag3"],
        }
        save_tags(test_data)
        
        result = find_isolated_files(max_shared_tags=0)  # Very strict
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["isolated_files"]), 0)

    def test_find_isolated_files_case_insensitive(self):
        """Test that isolation check is case-insensitive"""
        from tagmanager.app.filter.service import find_isolated_files
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/file1.py": ["Python", "Backend"],
            "/file2.js": ["python", "frontend"],  # Shares "python" despite different case
        }
        save_tags(test_data)
        
        result = find_isolated_files(max_shared_tags=0)
        
        self.assertTrue(result["success"])
        # Should not find isolated files because they share "python"/"Python"
        self.assertEqual(len(result["isolated_files"]), 0)

    def test_find_isolated_files_skip_empty_tags(self):
        """Test that files with empty tags are skipped"""
        from tagmanager.app.filter.service import find_isolated_files
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/file1.py": [],                    # Empty tags - should be skipped
            "/file2.py": ["python"],
            "/file3.js": ["javascript"],
        }
        save_tags(test_data)
        
        result = find_isolated_files(max_shared_tags=0)
        
        self.assertTrue(result["success"])
        # Should not include file1.py because it has no tags
        isolated_files = [f["file_path"] for f in result["isolated_files"]]
        self.assertNotIn("/file1.py", isolated_files)

    # =================================================================
    # Tests for formatting functions
    # =================================================================

    def test_format_duplicates_result_success(self):
        """Test formatting duplicate results"""
        from tagmanager.app.filter.service import format_duplicates_result
        
        result = {
            "success": True,
            "total_files": 5,
            "duplicate_groups": 1,
            "duplicate_files_count": 2,
            "duplicates": {
                ("python", "test"): ["/file1.py", "/file2.py"]
            }
        }
        
        output = format_duplicates_result(result)
        
        self.assertIn("Duplicate Tags Analysis", output)
        self.assertIn("Total files: 5", output)
        self.assertIn("python, test", output)
        self.assertIn("file1.py", output)

    def test_format_duplicates_result_no_duplicates(self):
        """Test formatting when no duplicates found"""
        from tagmanager.app.filter.service import format_duplicates_result
        
        result = {
            "success": True,
            "total_files": 5,
            "duplicate_groups": 0,
            "duplicate_files_count": 0,
            "duplicates": {}
        }
        
        output = format_duplicates_result(result)
        
        self.assertIn("No duplicate tag sets found", output)
        self.assertIn("Analyzed 5 files", output)

    def test_format_orphans_result_success(self):
        """Test formatting orphaned files results"""
        from tagmanager.app.filter.service import format_orphans_result
        
        result = {
            "success": True,
            "total_files": 5,
            "orphan_count": 2,
            "orphans": ["/file1.txt", "/file2.md"]
        }
        
        output = format_orphans_result(result)
        
        self.assertIn("Orphaned Files Analysis", output)
        self.assertIn("Total files: 5", output)
        self.assertIn("Orphaned files: 2", output)
        self.assertIn("file1.txt", output)

    def test_format_similar_result_success(self):
        """Test formatting similar files results"""
        from tagmanager.app.filter.service import format_similar_result
        
        result = {
            "success": True,
            "target_file": "/path/to/target.py",
            "target_tags": ["python", "test"],
            "similarity_threshold": 0.5,
            "similar_files": [
                {
                    "file_path": "/path/to/similar.py",
                    "similarity": 0.8,
                    "common_tags": ["python"],
                    "unique_tags": ["web"]
                }
            ]
        }
        
        output = format_similar_result(result)
        
        self.assertIn("Similar Files to 'target.py'", output)
        self.assertIn("python, test", output)
        self.assertIn("80.0% similar", output)
        self.assertIn("Common: python", output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
