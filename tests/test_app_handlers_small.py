#!/usr/bin/env python3
"""Unit tests for small CLI handlers and related services (paths, storage, stats, list_all, visualization)."""

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestPathsHandlerAndService(unittest.TestCase):
    @patch("tagmanager.app.paths.handler.fuzzy_search_path", return_value="/match")
    @patch("builtins.print")
    def test_handle_path_command_fuzzy(self, mock_print, mock_fuzzy):
        from tagmanager.app.paths.handler import handle_path_command

        args = MagicMock()
        args.fuzzy = True
        args.filepath = "query"
        handle_path_command(args)
        mock_fuzzy.assert_called_once_with("query")
        mock_print.assert_called_once_with("/match")

    @patch("tagmanager.app.paths.handler.path_tags", return_value=["a", "b"])
    @patch("builtins.print")
    def test_handle_path_command_not_fuzzy(self, mock_print, mock_path_tags):
        from tagmanager.app.paths.handler import handle_path_command

        args = MagicMock()
        args.fuzzy = False
        args.filepath = "file.py"
        handle_path_command(args)
        mock_path_tags.assert_called_once_with("file.py")
        mock_print.assert_called_once_with(["a", "b"])

    @patch("tagmanager.app.paths.service.load_tags", return_value={"/abs/x.py": ["t"]})
    @patch("tagmanager.app.paths.service.os.getcwd", return_value="/proj")
    @patch("tagmanager.app.paths.service.os.path.abspath", return_value="/abs/x.py")
    @patch("tagmanager.app.paths.service.os.path.join", return_value="rel")
    @patch("builtins.print")
    def test_path_tags_resolves_and_returns(self, mock_print, mock_join, mock_abspath, mock_cwd, mock_load):
        from tagmanager.app.paths.service import path_tags

        out = path_tags("src/x.py")
        self.assertEqual(out, ["t"])
        mock_print.assert_called()

    @patch("tagmanager.app.paths.service.load_tags", side_effect=RuntimeError("db"))
    @patch("builtins.print")
    def test_fuzzy_search_path_load_error(self, mock_print, mock_load):
        from tagmanager.app.paths.service import fuzzy_search_path

        self.assertEqual(fuzzy_search_path("anything"), "")

    @patch("tagmanager.app.paths.service.load_tags", return_value={})
    def test_fuzzy_search_path_empty_db(self, mock_load):
        from tagmanager.app.paths.service import fuzzy_search_path

        self.assertEqual(fuzzy_search_path("q"), "")

    @patch("tagmanager.app.paths.service.load_tags", return_value={"/a.py": [], "/z.py": []})
    @patch("tagmanager.app.paths.service.normalized_levenshtein_distance", return_value=0.9)
    def test_fuzzy_search_path_returns_best(self, mock_dist, mock_load):
        from tagmanager.app.paths.service import fuzzy_search_path

        self.assertEqual(fuzzy_search_path("needle"), "/a.py")


class TestStorageHandlerAndService(unittest.TestCase):
    @patch("tagmanager.app.storage.handler.open_storage_location")
    def test_handle_storage_open(self, mock_open):
        from tagmanager.app.storage.handler import handle_storage_command

        args = MagicMock()
        args.open = True
        handle_storage_command(args)
        mock_open.assert_called_once()

    @patch("tagmanager.app.storage.handler.show_storage_location", return_value="/tags.json")
    @patch("builtins.print")
    def test_handle_storage_show(self, mock_print, mock_show):
        from tagmanager.app.storage.handler import handle_storage_command

        args = MagicMock()
        args.open = False
        handle_storage_command(args)
        mock_print.assert_called_once_with("/tags.json")

    @patch("tagmanager.app.storage.service.get_tag_file_path", return_value=r"C:\data\tags.json")
    def test_show_storage_location(self, mock_gtfp):
        from tagmanager.app.storage.service import show_storage_location

        self.assertEqual(show_storage_location(), r"C:\data\tags.json")

    @patch("tagmanager.app.storage.service.subprocess.run")
    @patch("tagmanager.app.storage.service.get_tag_file_path", return_value="/t.json")
    def test_open_storage_location_darwin(self, mock_gtfp, mock_run):
        from tagmanager.app.storage import service as svc

        with patch.object(svc.sys, "platform", "darwin"):
            svc.open_storage_location()
        mock_run.assert_called_once_with(["open", "/t.json"])

    @patch("tagmanager.app.storage.service.subprocess.run")
    @patch("tagmanager.app.storage.service.get_tag_file_path", return_value="/t.json")
    def test_open_storage_location_linux(self, mock_gtfp, mock_run):
        from tagmanager.app.storage import service as svc

        with patch.object(svc.sys, "platform", "linux"):
            svc.open_storage_location()
        mock_run.assert_called_once_with(["xdg-open", "/t.json"])

    @patch("tagmanager.app.storage.service.get_tag_file_path", return_value="/t.json")
    @patch("builtins.print")
    def test_open_storage_location_unsupported_os(self, mock_print, mock_gtfp):
        from tagmanager.app.storage import service as svc

        with patch.object(svc.sys, "platform", "freebsd12"):
            svc.open_storage_location()
        mock_print.assert_called_once()
        self.assertIn("Unsupported", mock_print.call_args[0][0])

    @unittest.skipUnless(sys.platform.startswith("win"), "os.startfile is Windows-only")
    @patch("os.startfile")
    @patch("tagmanager.app.storage.service.get_tag_file_path", return_value=r"C:\t.json")
    def test_open_storage_location_windows(self, mock_gtfp, mock_startfile):
        from tagmanager.app.storage import service as svc

        svc.open_storage_location()
        mock_startfile.assert_called_once_with(r"C:\t.json")


class TestStatsHandler(unittest.TestCase):
    @patch("tagmanager.app.stats.handler.format_namespace_statistics")
    @patch("tagmanager.app.stats.handler.get_namespace_statistics", return_value={"n": 1})
    @patch("builtins.print")
    def test_namespaces_branch(self, mock_print, mock_get, mock_fmt):
        from tagmanager.app.stats.handler import handle_stats_command

        mock_fmt.return_value = "NS"
        handle_stats_command(namespaces=True)
        mock_print.assert_called_once_with("NS")

    @patch("tagmanager.app.stats.handler.format_tag_statistics")
    @patch("tagmanager.app.stats.handler.get_tag_statistics", return_value={})
    @patch("builtins.print")
    def test_tag_branch(self, mock_print, mock_get, mock_fmt):
        from tagmanager.app.stats.handler import handle_stats_command

        mock_fmt.return_value = "TAG"
        handle_stats_command(tag="python")
        mock_get.assert_called_once_with("python")
        mock_print.assert_called_once_with("TAG")

    @patch("tagmanager.app.stats.handler.format_file_count_distribution")
    @patch("tagmanager.app.stats.handler.get_file_count_distribution", return_value=[])
    @patch("builtins.print")
    def test_file_count_branch(self, mock_print, mock_get, mock_fmt):
        from tagmanager.app.stats.handler import handle_stats_command

        mock_fmt.return_value = "FC"
        handle_stats_command(file_count=True)
        mock_print.assert_called_once_with("FC")

    @patch("tagmanager.app.stats.handler.format_overall_statistics")
    @patch("tagmanager.app.stats.handler.get_overall_statistics", return_value={})
    @patch("builtins.print")
    def test_overall_branch(self, mock_print, mock_get, mock_fmt):
        from tagmanager.app.stats.handler import handle_stats_command

        mock_fmt.return_value = "ALL"
        handle_stats_command()
        mock_print.assert_called_once_with("ALL")


class TestListAllHandler(unittest.TestCase):
    @patch("tagmanager.app.list_all.handler.print_list_tags_all_table")
    @patch("builtins.print")
    def test_handle_list_all_command(self, mock_print, mock_table):
        from tagmanager.app.list_all.handler import handle_list_all_command

        handle_list_all_command(MagicMock())
        mock_table.assert_called_once()


class TestVisualizationHandler(unittest.TestCase):
    @patch("tagmanager.app.visualization.handler.typer.echo")
    @patch("tagmanager.app.visualization.handler.generate_tree_view", return_value="tree")
    def test_handle_tree_view(self, mock_gen, mock_echo):
        from tagmanager.app.visualization.handler import handle_tree_view

        handle_tree_view()
        mock_echo.assert_called_once_with("tree")

    @patch("tagmanager.app.visualization.handler.typer.echo")
    @patch("tagmanager.app.visualization.handler.generate_tag_cloud", return_value="cloud")
    def test_handle_tag_cloud(self, mock_gen, mock_echo):
        from tagmanager.app.visualization.handler import handle_tag_cloud

        handle_tag_cloud()
        mock_echo.assert_called_once_with("cloud")

    @patch("tagmanager.app.visualization.handler.typer.echo")
    @patch("tagmanager.app.visualization.handler.generate_stats_charts", return_value="charts")
    def test_handle_stats_charts(self, mock_gen, mock_echo):
        from tagmanager.app.visualization.handler import handle_stats_charts

        handle_stats_charts()
        mock_echo.assert_called_once_with("charts")


if __name__ == "__main__":
    unittest.main()
