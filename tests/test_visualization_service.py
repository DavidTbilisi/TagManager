#!/usr/bin/env python3
"""
Comprehensive tests for tagmanager.app.visualization.service
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


class TestVisualizationService(unittest.TestCase):
    """Comprehensive tests for visualization service functionality"""

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
        """Setup comprehensive test data for visualization"""
        from tagmanager.app.helpers import save_tags
        
        test_data = {
            "/project/src/main.py": ["python", "backend", "api"],
            "/project/src/utils.py": ["python", "backend", "utilities"],
            "/project/tests/test_main.py": ["python", "testing", "unit"],
            "/project/frontend/app.js": ["javascript", "frontend", "react"],
            "/project/frontend/styles.css": ["css", "frontend", "styling"],
            "/project/docs/readme.md": ["documentation", "markdown"],
            "/config/settings.json": ["config", "json"],
            "/data/sample.txt": ["data", "text"],
        }
        save_tags(test_data)
        return test_data

    # =================================================================
    # Tests for create_tree_structure
    # =================================================================

    def test_create_tree_structure_basic(self):
        """Test basic tree structure creation"""
        from tagmanager.app.visualization.service import create_tree_structure
        
        files_data = {
            "/project/main.py": ["python", "main"],
            "/project/utils.py": ["python", "utilities"],
            "/docs/readme.md": ["documentation"]
        }
        
        tree = create_tree_structure(files_data)
        
        # Check root structure (Windows creates \ root)
        if "\\" in tree:
            root = tree["\\"]
        else:
            root = tree
        
        self.assertIn("project", root["children"])
        self.assertIn("docs", root["children"])
        
        # Check project directory
        project_node = root["children"]["project"]
        self.assertEqual(project_node["type"], "directory")
        self.assertIn("main.py", project_node["children"])
        self.assertIn("utils.py", project_node["children"])
        
        # Check file nodes
        main_file = project_node["children"]["main.py"]
        self.assertEqual(main_file["type"], "file")
        self.assertEqual(main_file["tags"], ["python", "main"])

    def test_create_tree_structure_empty_input(self):
        """Test tree structure with empty input"""
        from tagmanager.app.visualization.service import create_tree_structure
        
        tree = create_tree_structure({})
        self.assertEqual(tree, {})

    def test_create_tree_structure_single_file(self):
        """Test tree structure with single file"""
        from tagmanager.app.visualization.service import create_tree_structure
        
        files_data = {"/single.py": ["python"]}
        tree = create_tree_structure(files_data)
        
        # Handle Windows root structure
        if "\\" in tree:
            root = tree["\\"]
            self.assertIn("single.py", root["children"])
            self.assertEqual(root["children"]["single.py"]["type"], "file")
            self.assertEqual(root["children"]["single.py"]["tags"], ["python"])
        else:
            self.assertIn("single.py", tree)
            self.assertEqual(tree["single.py"]["type"], "file")
            self.assertEqual(tree["single.py"]["tags"], ["python"])

    def test_create_tree_structure_nested_paths(self):
        """Test tree structure with deeply nested paths"""
        from tagmanager.app.visualization.service import create_tree_structure
        
        files_data = {
            "/a/b/c/d/file.py": ["deep", "nested"],
            "/a/b/other.py": ["shallow"]
        }
        
        tree = create_tree_structure(files_data)
        
        # Handle Windows root structure
        if "\\" in tree:
            root = tree["\\"]
        else:
            root = tree
        
        # Navigate through the tree
        self.assertIn("a", root["children"])
        a_node = root["children"]["a"]
        self.assertEqual(a_node["type"], "directory")
        
        b_node = a_node["children"]["b"]
        self.assertEqual(b_node["type"], "directory")
        
        # Check both files exist at their correct levels
        self.assertIn("other.py", b_node["children"])
        c_node = b_node["children"]["c"]
        d_node = c_node["children"]["d"]
        self.assertIn("file.py", d_node["children"])

    # =================================================================
    # Tests for render_tree
    # =================================================================

    def test_render_tree_basic(self):
        """Test basic tree rendering"""
        from tagmanager.app.visualization.service import create_tree_structure, render_tree
        
        files_data = {
            "/project/main.py": ["python"],
            "/project/utils.py": ["python"]
        }
        
        tree = create_tree_structure(files_data)
        lines = render_tree(tree)
        
        # Check that we get rendered lines
        self.assertGreater(len(lines), 0)
        
        # Check for expected content
        rendered = "\n".join(lines)
        self.assertIn("project", rendered)
        self.assertIn("main.py", rendered)
        self.assertIn("utils.py", rendered)
        self.assertIn("📁", rendered)  # Folder icon
        self.assertIn("📄", rendered)  # File icon

    def test_render_tree_with_tags(self):
        """Test tree rendering with tags shown"""
        from tagmanager.app.visualization.service import create_tree_structure, render_tree
        
        files_data = {"/test.py": ["python", "test"]}
        tree = create_tree_structure(files_data)
        lines = render_tree(tree, show_tags=True)
        
        rendered = "\n".join(lines)
        self.assertIn("python", rendered)
        self.assertIn("test", rendered)
        self.assertIn("🏷️", rendered)  # Tag icon

    def test_render_tree_without_tags(self):
        """Test tree rendering with tags hidden"""
        from tagmanager.app.visualization.service import create_tree_structure, render_tree
        
        files_data = {"/test.py": ["python", "test"]}
        tree = create_tree_structure(files_data)
        lines = render_tree(tree, show_tags=False)
        
        rendered = "\n".join(lines)
        self.assertNotIn("python", rendered)
        self.assertNotIn("🏷️", rendered)

    def test_render_tree_empty(self):
        """Test rendering empty tree"""
        from tagmanager.app.visualization.service import render_tree
        
        lines = render_tree({})
        self.assertEqual(lines, [])

    def test_render_tree_ascii_characters(self):
        """Test that tree uses correct ASCII box drawing characters"""
        from tagmanager.app.visualization.service import create_tree_structure, render_tree
        
        files_data = {
            "/dir/file1.py": ["python"],
            "/dir/file2.py": ["python"]
        }
        
        tree = create_tree_structure(files_data)
        lines = render_tree(tree)
        
        rendered = "\n".join(lines)
        # Should contain tree drawing characters
        self.assertTrue(any(char in rendered for char in ["├──", "└──", "│"]))

    # =================================================================
    # Tests for create_tag_cloud_data
    # =================================================================

    def test_create_tag_cloud_data_basic(self):
        """Test basic tag cloud data creation"""
        from tagmanager.app.visualization.service import create_tag_cloud_data
        
        files_data = {
            "/file1.py": ["python", "backend"],
            "/file2.py": ["python", "frontend"],
            "/file3.js": ["javascript", "frontend"]
        }
        
        tag_data = create_tag_cloud_data(files_data)
        
        # Should return list of tuples (tag, count, size)
        self.assertIsInstance(tag_data, list)
        self.assertGreater(len(tag_data), 0)
        
        # Check tuple structure
        for item in tag_data:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 3)
            tag, count, size = item
            self.assertIsInstance(tag, str)
            self.assertIsInstance(count, int)
            self.assertIsInstance(size, float)

    def test_create_tag_cloud_data_frequency_order(self):
        """Test that tag cloud data is ordered by frequency"""
        from tagmanager.app.visualization.service import create_tag_cloud_data
        
        files_data = {
            "/file1.py": ["common", "rare"],
            "/file2.py": ["common", "medium"],
            "/file3.py": ["common", "medium"],
            "/file4.py": ["common"]
        }
        
        tag_data = create_tag_cloud_data(files_data)
        
        # Should be ordered by frequency (descending)
        frequencies = [count for _, count, _ in tag_data]
        self.assertEqual(frequencies, sorted(frequencies, reverse=True))
        
        # Most frequent should be "common" (4 occurrences)
        self.assertEqual(tag_data[0][0], "common")
        self.assertEqual(tag_data[0][1], 4)

    def test_create_tag_cloud_data_size_scaling(self):
        """Test that relative sizes are calculated correctly"""
        from tagmanager.app.visualization.service import create_tag_cloud_data
        
        files_data = {
            "/file1.py": ["frequent", "frequent", "frequent"],  # Will count as 1 per file
            "/file2.py": ["frequent", "rare"],
            "/file3.py": ["frequent"]
        }
        
        # Actually, each file contributes 1 count per tag, so "frequent" = 3, "rare" = 1
        files_data = {
            "/file1.py": ["frequent"],
            "/file2.py": ["frequent"],
            "/file3.py": ["frequent"],
            "/file4.py": ["rare"]
        }
        
        tag_data = create_tag_cloud_data(files_data)
        
        # Check size scaling (should be between 1.0 and 5.0)
        for _, _, size in tag_data:
            self.assertGreaterEqual(size, 1.0)
            self.assertLessEqual(size, 5.0)

    def test_create_tag_cloud_data_empty_input(self):
        """Test tag cloud with empty input"""
        from tagmanager.app.visualization.service import create_tag_cloud_data
        
        tag_data = create_tag_cloud_data({})
        self.assertEqual(tag_data, [])

    def test_create_tag_cloud_data_same_frequency(self):
        """Test tag cloud when all tags have same frequency"""
        from tagmanager.app.visualization.service import create_tag_cloud_data
        
        files_data = {
            "/file1.py": ["tag1"],
            "/file2.py": ["tag2"],
            "/file3.py": ["tag3"]
        }
        
        tag_data = create_tag_cloud_data(files_data)
        
        # All should have same size (3.0 default)
        for _, count, size in tag_data:
            self.assertEqual(count, 1)
            self.assertEqual(size, 3.0)

    # =================================================================
    # Tests for render_tag_cloud
    # =================================================================

    def test_render_tag_cloud_basic(self):
        """Test basic tag cloud rendering"""
        from tagmanager.app.visualization.service import render_tag_cloud
        
        tag_data = [
            ("python", 5, 5.0),
            ("javascript", 3, 3.0),
            ("css", 1, 1.0)
        ]
        
        lines = render_tag_cloud(tag_data)
        
        self.assertGreater(len(lines), 0)
        rendered = " ".join(lines)
        
        # Check that all tags appear
        self.assertIn("python", rendered)
        self.assertIn("javascript", rendered)
        self.assertIn("css", rendered)
        
        # Check that counts appear
        self.assertIn("(5)", rendered)
        self.assertIn("(3)", rendered)
        self.assertIn("(1)", rendered)

    def test_render_tag_cloud_size_indicators(self):
        """Test that different size indicators are used"""
        from tagmanager.app.visualization.service import render_tag_cloud
        
        tag_data = [
            ("huge", 10, 5.0),    # Should get ★
            ("big", 7, 4.0),      # Should get ◆
            ("medium", 5, 3.0),   # Should get ●
            ("small", 3, 2.0),    # Should get •
            ("tiny", 1, 1.0)      # Should get ·
        ]
        
        lines = render_tag_cloud(tag_data)
        rendered = " ".join(lines)
        
        # Check for different size characters
        self.assertIn("★", rendered)  # Largest
        self.assertIn("◆", rendered)  # Very frequent
        self.assertIn("●", rendered)  # Medium
        self.assertIn("•", rendered)  # Less frequent
        self.assertIn("·", rendered)  # Smallest

    def test_render_tag_cloud_width_wrapping(self):
        """Test that tag cloud wraps at specified width"""
        from tagmanager.app.visualization.service import render_tag_cloud
        
        tag_data = [("verylongtagname", 1, 3.0) for _ in range(10)]
        
        lines = render_tag_cloud(tag_data, width=20)  # Very narrow
        
        # Should create multiple lines due to width constraint
        self.assertGreater(len(lines), 1)

    def test_render_tag_cloud_empty_input(self):
        """Test rendering empty tag cloud"""
        from tagmanager.app.visualization.service import render_tag_cloud
        
        lines = render_tag_cloud([])
        self.assertEqual(lines, ["No tags found."])

    # =================================================================
    # Tests for create_ascii_bar_chart
    # =================================================================

    def test_create_ascii_bar_chart_basic(self):
        """Test basic ASCII bar chart creation"""
        from tagmanager.app.visualization.service import create_ascii_bar_chart
        
        data = {"Python": 10, "JavaScript": 7, "CSS": 3}
        lines = create_ascii_bar_chart(data, "Languages")
        
        self.assertGreater(len(lines), 0)
        rendered = "\n".join(lines)
        
        # Check title
        self.assertIn("Languages", rendered)
        
        # Check data labels
        self.assertIn("Python", rendered)
        self.assertIn("JavaScript", rendered)
        self.assertIn("CSS", rendered)
        
        # Check bars (█ character)
        self.assertIn("█", rendered)
        
        # Check percentages
        self.assertIn("%", rendered)

    def test_create_ascii_bar_chart_ordering(self):
        """Test that bars are ordered by value (descending)"""
        from tagmanager.app.visualization.service import create_ascii_bar_chart
        
        data = {"Low": 1, "High": 10, "Medium": 5}
        lines = create_ascii_bar_chart(data)
        
        rendered = "\n".join(lines)
        
        # "High" should appear before "Medium" which should appear before "Low"
        high_pos = rendered.find("High")
        medium_pos = rendered.find("Medium")
        low_pos = rendered.find("Low")
        
        self.assertLess(high_pos, medium_pos)
        self.assertLess(medium_pos, low_pos)

    def test_create_ascii_bar_chart_empty_data(self):
        """Test bar chart with empty data"""
        from tagmanager.app.visualization.service import create_ascii_bar_chart
        
        lines = create_ascii_bar_chart({}, "Empty Chart")
        
        rendered = "\n".join(lines)
        self.assertIn("Empty Chart", rendered)
        self.assertIn("No data available", rendered)

    def test_create_ascii_bar_chart_zero_values(self):
        """Test bar chart with all zero values"""
        from tagmanager.app.visualization.service import create_ascii_bar_chart
        
        data = {"A": 0, "B": 0, "C": 0}
        lines = create_ascii_bar_chart(data)
        
        rendered = "\n".join(lines)
        self.assertIn("No data to display", rendered)

    def test_create_ascii_bar_chart_scaling(self):
        """Test that bars scale properly"""
        from tagmanager.app.visualization.service import create_ascii_bar_chart
        
        data = {"Max": 100, "Half": 50, "Quarter": 25}
        lines = create_ascii_bar_chart(data, max_width=40)
        
        # Find the bar lines
        bar_lines = [line for line in lines if "█" in line]
        
        # Max should have longest bar, Quarter should have shortest
        max_line = next(line for line in bar_lines if "Max" in line)
        quarter_line = next(line for line in bar_lines if "Quarter" in line)
        
        max_bar_length = max_line.count("█")
        quarter_bar_length = quarter_line.count("█")
        
        self.assertGreater(max_bar_length, quarter_bar_length)

    # =================================================================
    # Tests for create_ascii_histogram
    # =================================================================

    def test_create_ascii_histogram_basic(self):
        """Test basic ASCII histogram creation"""
        from tagmanager.app.visualization.service import create_ascii_histogram
        
        data = [1, 2, 2, 3, 3, 3, 4, 4, 5]
        lines = create_ascii_histogram(data, "Test Histogram")
        
        self.assertGreater(len(lines), 0)
        rendered = "\n".join(lines)
        
        # Check title
        self.assertIn("Test Histogram", rendered)
        
        # Check that bins are created
        self.assertIn("█", rendered)
        
        # Check that ranges are shown
        self.assertIn("-", rendered)  # Range separator

    def test_create_ascii_histogram_empty_data(self):
        """Test histogram with empty data"""
        from tagmanager.app.visualization.service import create_ascii_histogram
        
        lines = create_ascii_histogram([], "Empty Histogram")
        
        rendered = "\n".join(lines)
        self.assertIn("Empty Histogram", rendered)
        self.assertIn("No data available", rendered)

    def test_create_ascii_histogram_single_value(self):
        """Test histogram with all same values"""
        from tagmanager.app.visualization.service import create_ascii_histogram
        
        data = [5, 5, 5, 5, 5]
        lines = create_ascii_histogram(data)
        
        rendered = "\n".join(lines)
        self.assertIn("All values are 5", rendered)

    def test_create_ascii_histogram_custom_bins(self):
        """Test histogram with custom number of bins"""
        from tagmanager.app.visualization.service import create_ascii_histogram
        
        data = list(range(100))  # 0 to 99
        lines = create_ascii_histogram(data, bins=5)
        
        # Should have 5 bins
        bin_lines = [line for line in lines if "█" in line or "-" in line]
        # Filter for actual bin lines (not title)
        actual_bins = [line for line in bin_lines if "." in line and "-" in line]
        self.assertEqual(len(actual_bins), 5)

    # =================================================================
    # Tests for generate_tree_view
    # =================================================================

    def test_generate_tree_view_success(self):
        """Test successful tree view generation"""
        from tagmanager.app.visualization.service import generate_tree_view
        
        self._setup_test_data()
        
        result = generate_tree_view()
        
        self.assertIsInstance(result, str)
        self.assertIn("Tagged Files Tree View", result)
        self.assertIn("📁", result)  # Folder icons
        self.assertIn("📄", result)  # File icons
        self.assertIn("Total files:", result)

    def test_generate_tree_view_empty_data(self):
        """Test tree view with no data"""
        from tagmanager.app.visualization.service import generate_tree_view
        
        result = generate_tree_view()
        
        self.assertIn("No tagged files found", result)

    # =================================================================
    # Tests for generate_tag_cloud
    # =================================================================

    def test_generate_tag_cloud_success(self):
        """Test successful tag cloud generation"""
        from tagmanager.app.visualization.service import generate_tag_cloud
        
        self._setup_test_data()
        
        result = generate_tag_cloud()
        
        self.assertIsInstance(result, str)
        self.assertIn("Tag Cloud", result)
        self.assertIn("Legend:", result)
        self.assertIn("Total unique tags:", result)
        
        # Should contain some of our test tags
        self.assertIn("python", result)
        self.assertIn("frontend", result)

    def test_generate_tag_cloud_empty_data(self):
        """Test tag cloud with no data"""
        from tagmanager.app.visualization.service import generate_tag_cloud
        
        result = generate_tag_cloud()
        
        self.assertIn("No tags found", result)

    # =================================================================
    # Tests for generate_stats_charts
    # =================================================================

    def test_generate_stats_charts_success(self):
        """Test successful stats charts generation"""
        from tagmanager.app.visualization.service import generate_stats_charts
        
        self._setup_test_data()
        
        result = generate_stats_charts()
        
        self.assertIsInstance(result, str)
        self.assertIn("TagManager Statistics Charts", result)
        self.assertIn("Files by Tag Count", result)
        self.assertIn("Top 10 Most Used Tags", result)
        self.assertIn("Summary Statistics", result)
        self.assertIn("Total files:", result)
        self.assertIn("Average tags per file:", result)

    def test_generate_stats_charts_empty_data(self):
        """Test stats charts with no data"""
        from tagmanager.app.visualization.service import generate_stats_charts
        
        result = generate_stats_charts()
        
        self.assertIn("No data available for charts", result)

    def test_generate_stats_charts_histogram_generation(self):
        """Test that histogram is included when there's enough data"""
        from tagmanager.app.visualization.service import generate_stats_charts
        
        self._setup_test_data()
        
        result = generate_stats_charts()
        
        # Should include histogram for tag count distribution
        self.assertIn("Tag Count Distribution Histogram", result)

    def test_generate_stats_charts_single_file(self):
        """Test stats charts with only one file (no histogram)"""
        from tagmanager.app.visualization.service import generate_stats_charts
        from tagmanager.app.helpers import save_tags
        
        # Setup single file
        save_tags({"/single.py": ["python", "test"]})
        
        result = generate_stats_charts()
        
        self.assertIn("TagManager Statistics Charts", result)
        # Should not include histogram with only one data point
        self.assertNotIn("Tag Count Distribution Histogram", result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
