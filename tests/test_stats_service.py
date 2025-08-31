#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.stats.service
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


class TestStatsService(unittest.TestCase):
    """Comprehensive tests for stats service functionality"""

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
        """Setup comprehensive test data for statistics"""
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/project/main.py": ["python", "backend", "api", "main"],
            "/project/utils.py": ["python", "backend", "utilities"],
            "/project/test.py": ["python", "testing", "unit-tests"],
            "/frontend/app.js": ["javascript", "frontend", "react"],
            "/frontend/styles.css": ["css", "frontend", "styling"],
            "/docs/readme.md": ["documentation"],
            "/config/settings.json": ["config", "json"],
            "/empty/file.txt": [],  # File without tags
        }
        save_tags(test_data)
        return test_data

    # =================================================================
    # Tests for get_overall_statistics
    # =================================================================

    def test_get_overall_statistics_comprehensive(self):
        """Test overall statistics with comprehensive data"""
        from tagmanager.app.stats.service import get_overall_statistics
        
        self._setup_test_data()
        
        stats = get_overall_statistics()
        
        # Basic counts
        self.assertEqual(stats["total_files"], 8)
        self.assertEqual(stats["files_without_tags"], 1)  # empty/file.txt
        self.assertEqual(stats["unique_tags"], 15)  # Count unique tags (fixed)
        self.assertGreater(stats["total_tags"], stats["unique_tags"])  # Some tags repeat
        
        # Average calculation  
        expected_avg = stats["total_tags"] / 8  # Use actual total tags
        self.assertAlmostEqual(stats["avg_tags_per_file"], expected_avg, places=2)
        
        # Most common tags
        self.assertIsInstance(stats["most_common_tags"], list)
        self.assertGreater(len(stats["most_common_tags"]), 0)
        
        # Should include python, frontend, backend (appear multiple times)
        common_tag_names = [tag for tag, count in stats["most_common_tags"]]
        self.assertIn("python", common_tag_names)
        self.assertIn("frontend", common_tag_names)
        
        # Tag distribution
        self.assertIsInstance(stats["tag_distribution"], dict)
        self.assertIn(0, stats["tag_distribution"])  # Files with 0 tags
        self.assertEqual(stats["tag_distribution"][0], 1)  # One file with 0 tags

    def test_get_overall_statistics_empty_database(self):
        """Test overall statistics with empty database"""
        from tagmanager.app.stats.service import get_overall_statistics
        
        stats = get_overall_statistics()
        
        self.assertEqual(stats["total_files"], 0)
        self.assertEqual(stats["total_tags"], 0)
        self.assertEqual(stats["unique_tags"], 0)
        self.assertEqual(stats["avg_tags_per_file"], 0)
        self.assertEqual(stats["files_without_tags"], 0)
        self.assertEqual(stats["most_common_tags"], [])
        self.assertEqual(stats["least_common_tags"], [])
        self.assertEqual(stats["tag_distribution"], {})

    def test_get_overall_statistics_all_files_without_tags(self):
        """Test overall statistics when all files have no tags"""
        from tagmanager.app.stats.service import get_overall_statistics
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/file1.txt": [],
            "/file2.txt": [],
            "/file3.txt": [],
        }
        save_tags(test_data)
        
        stats = get_overall_statistics()
        
        self.assertEqual(stats["total_files"], 3)
        self.assertEqual(stats["files_without_tags"], 3)
        self.assertEqual(stats["total_tags"], 0)
        self.assertEqual(stats["unique_tags"], 0)
        self.assertEqual(stats["avg_tags_per_file"], 0)

    def test_get_overall_statistics_least_common_tags(self):
        """Test that least common tags are calculated correctly"""
        from tagmanager.app.stats.service import get_overall_statistics
        from tagmanager.app.helpers import save_tags
        
        # Create data with many unique tags (more than 10)
        test_data = {}
        for i in range(15):
            test_data[f"/file{i}.txt"] = [f"tag{i}", "common"]
        
        save_tags(test_data)
        
        stats = get_overall_statistics()
        
        # Should have least common tags since we have > 10 unique tags
        self.assertGreater(len(stats["least_common_tags"]), 0)
        # Each unique tag should appear only once except "common"
        least_common_counts = [count for tag, count in stats["least_common_tags"]]
        self.assertTrue(all(count == 1 for count in least_common_counts))

    # =================================================================
    # Tests for get_tag_statistics
    # =================================================================

    def test_get_tag_statistics_existing_tag(self):
        """Test statistics for an existing tag"""
        from tagmanager.app.stats.service import get_tag_statistics
        
        self._setup_test_data()
        
        stats = get_tag_statistics("python")
        
        self.assertEqual(stats["tag_name"], "python")
        self.assertEqual(stats["files_with_tag"], 3)  # main.py, utils.py, test.py
        self.assertEqual(stats["percentage_of_files"], 37.5)  # 3/8 * 100
        self.assertEqual(len(stats["files"]), 3)
        
        # Check co-occurring tags
        self.assertIsInstance(stats["co_occurring_tags"], list)
        co_occurring_names = [tag for tag, count in stats["co_occurring_tags"]]
        self.assertIn("backend", co_occurring_names)  # Appears with python in 2 files
        
        # Check file types
        self.assertIn("py", stats["file_types"])
        self.assertEqual(stats["file_types"]["py"], 3)

    def test_get_tag_statistics_case_insensitive(self):
        """Test that tag statistics are case-insensitive"""
        from tagmanager.app.stats.service import get_tag_statistics
        
        self._setup_test_data()
        
        stats_lower = get_tag_statistics("python")
        stats_upper = get_tag_statistics("PYTHON")
        stats_mixed = get_tag_statistics("PyThOn")
        
        # All should return the same results
        self.assertEqual(stats_lower["files_with_tag"], stats_upper["files_with_tag"])
        self.assertEqual(stats_lower["files_with_tag"], stats_mixed["files_with_tag"])

    def test_get_tag_statistics_nonexistent_tag(self):
        """Test statistics for a tag that doesn't exist"""
        from tagmanager.app.stats.service import get_tag_statistics
        
        self._setup_test_data()
        
        stats = get_tag_statistics("nonexistent")
        
        self.assertEqual(stats["tag_name"], "nonexistent")
        self.assertEqual(stats["files_with_tag"], 0)
        self.assertEqual(stats["percentage_of_files"], 0)
        self.assertEqual(stats["files"], [])
        self.assertEqual(stats["co_occurring_tags"], [])
        self.assertEqual(stats["file_types"], {})

    def test_get_tag_statistics_empty_database(self):
        """Test tag statistics with empty database"""
        from tagmanager.app.stats.service import get_tag_statistics
        
        stats = get_tag_statistics("any_tag")
        
        self.assertEqual(stats["tag_name"], "any_tag")
        self.assertEqual(stats["files_with_tag"], 0)
        self.assertEqual(stats["percentage_of_files"], 0)
        self.assertEqual(stats["files"], [])
        self.assertEqual(stats["co_occurring_tags"], [])
        self.assertEqual(stats["file_types"], {})

    def test_get_tag_statistics_files_without_extension(self):
        """Test tag statistics with files that have no extension"""
        from tagmanager.app.stats.service import get_tag_statistics
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/path/to/makefile": ["build", "config"],
            "/path/to/dockerfile": ["build", "docker"],
            "/path/to/readme": ["build", "docs"],
        }
        save_tags(test_data)
        
        stats = get_tag_statistics("build")
        
        self.assertEqual(stats["files_with_tag"], 3)
        self.assertIn("no_extension", stats["file_types"])
        self.assertEqual(stats["file_types"]["no_extension"], 3)

    def test_get_tag_statistics_co_occurring_analysis(self):
        """Test that co-occurring tags are analyzed correctly"""
        from tagmanager.app.stats.service import get_tag_statistics
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/file1.py": ["target", "common", "frequent"],
            "/file2.py": ["target", "common", "frequent"],
            "/file3.py": ["target", "common", "rare"],
            "/file4.py": ["target", "unique"],
        }
        save_tags(test_data)
        
        stats = get_tag_statistics("target")
        
        # Co-occurring tags should be sorted by frequency
        co_occurring = dict(stats["co_occurring_tags"])
        self.assertEqual(co_occurring["common"], 3)  # Appears with target 3 times
        self.assertEqual(co_occurring["frequent"], 2)  # Appears with target 2 times

    # =================================================================
    # Tests for get_file_count_distribution
    # =================================================================

    def test_get_file_count_distribution_success(self):
        """Test file count distribution with normal data"""
        from tagmanager.app.stats.service import get_file_count_distribution
        
        self._setup_test_data()
        
        stats = get_file_count_distribution()
        
        self.assertGreater(stats["total_tags"], 0)
        self.assertIsInstance(stats["tags_by_file_count"], list)
        self.assertIsInstance(stats["distribution_summary"], dict)
        
        # Check that tags are sorted by file count (descending)
        file_counts = [count for tag, count in stats["tags_by_file_count"]]
        self.assertEqual(file_counts, sorted(file_counts, reverse=True))
        
        # Check specific tags we know
        tag_dict = dict(stats["tags_by_file_count"])
        self.assertEqual(tag_dict["python"], 3)  # Appears in 3 files
        self.assertEqual(tag_dict["frontend"], 2)  # Appears in 2 files

    def test_get_file_count_distribution_empty_database(self):
        """Test file count distribution with empty database"""
        from tagmanager.app.stats.service import get_file_count_distribution
        
        stats = get_file_count_distribution()
        
        self.assertEqual(stats["total_tags"], 0)
        self.assertEqual(stats["tags_by_file_count"], [])
        self.assertEqual(stats["distribution_summary"], {})

    def test_get_file_count_distribution_single_occurrence_tags(self):
        """Test distribution when all tags appear only once"""
        from tagmanager.app.stats.service import get_file_count_distribution
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/file1.txt": ["unique1", "unique2"],
            "/file2.txt": ["unique3", "unique4"],
            "/file3.txt": ["unique5"],
        }
        save_tags(test_data)
        
        stats = get_file_count_distribution()
        
        # All tags should have file count of 1
        file_counts = [count for tag, count in stats["tags_by_file_count"]]
        self.assertTrue(all(count == 1 for count in file_counts))
        
        # Distribution summary should show all tags have 1 file
        self.assertEqual(stats["distribution_summary"][1], 5)  # 5 unique tags

    # =================================================================
    # Tests for formatting functions
    # =================================================================

    def test_format_overall_statistics_comprehensive(self):
        """Test formatting overall statistics"""
        from tagmanager.app.stats.service import format_overall_statistics
        
        stats = {
            "total_files": 10,
            "files_without_tags": 2,
            "total_tags": 25,
            "unique_tags": 15,
            "avg_tags_per_file": 2.5,
            "most_common_tags": [("python", 5), ("javascript", 3)],
            "least_common_tags": [("rare", 1)],
            "tag_distribution": {0: 2, 1: 3, 2: 3, 3: 2}
        }
        
        output = format_overall_statistics(stats)
        
        self.assertIn("Tag Manager Statistics", output)
        self.assertIn("Total files: 10", output)
        self.assertIn("Files without tags: 2", output)
        self.assertIn("Total tags: 25", output)
        self.assertIn("python: 5 files", output)
        self.assertIn("3 files have 2 tags", output)

    def test_format_tag_statistics_with_files(self):
        """Test formatting tag-specific statistics"""
        from tagmanager.app.stats.service import format_tag_statistics
        
        stats = {
            "tag_name": "python",
            "files_with_tag": 5,
            "percentage_of_files": 25.0,
            "files": ["/app/main.py", "/app/utils.py"],
            "co_occurring_tags": [("backend", 3), ("api", 2)],
            "file_types": {"py": 4, "txt": 1}
        }
        
        output = format_tag_statistics(stats)
        
        self.assertIn("Statistics for tag: 'python'", output)
        self.assertIn("Files with this tag: 5", output)
        self.assertIn("Percentage of all files: 25.0%", output)
        self.assertIn(".py: 4 files", output)
        self.assertIn("backend: 3 times", output)
        self.assertIn("main.py", output)

    def test_format_tag_statistics_no_files(self):
        """Test formatting when tag has no files"""
        from tagmanager.app.stats.service import format_tag_statistics
        
        stats = {
            "tag_name": "nonexistent",
            "files_with_tag": 0,
            "percentage_of_files": 0,
            "files": [],
            "co_occurring_tags": [],
            "file_types": {}
        }
        
        output = format_tag_statistics(stats)
        
        self.assertIn("Statistics for tag: 'nonexistent'", output)
        self.assertIn("No files found with this tag", output)

    def test_format_file_count_distribution_success(self):
        """Test formatting file count distribution"""
        from tagmanager.app.stats.service import format_file_count_distribution
        
        stats = {
            "total_tags": 10,
            "tags_by_file_count": [("python", 5), ("javascript", 3), ("css", 1)],
            "distribution_summary": {1: 6, 3: 2, 5: 2}
        }
        
        output = format_file_count_distribution(stats)
        
        self.assertIn("Files per Tag Distribution", output)
        self.assertIn("Total tags: 10", output)
        self.assertIn("python: 5 files", output)
        self.assertIn("6 tags have 1 file", output)

    def test_format_file_count_distribution_empty(self):
        """Test formatting when no tags exist"""
        from tagmanager.app.stats.service import format_file_count_distribution
        
        stats = {
            "total_tags": 0,
            "tags_by_file_count": [],
            "distribution_summary": {}
        }
        
        output = format_file_count_distribution(stats)
        
        self.assertIn("Files per Tag Distribution", output)
        self.assertIn("No tags found", output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
