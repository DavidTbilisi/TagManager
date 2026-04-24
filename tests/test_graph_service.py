#!/usr/bin/env python3
"""Tests for tagmanager.app.graph — service, export, and html_generator"""

import json
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


SAMPLE_TAGS = {
    "/home/user/project/main.py":   ["python", "backend", "core"],
    "/home/user/project/utils.py":  ["python", "backend", "utils"],
    "/home/user/project/app.js":    ["javascript", "frontend", "core"],
    "/home/user/project/style.css": ["css", "frontend"],
    "/home/user/project/README.md": ["docs", "markdown"],
    "/home/user/project/solo.txt":  ["unique-only"],
}


def _patch_tags(tags=None):
    if tags is None:
        tags = SAMPLE_TAGS
    return patch("tagmanager.app.helpers.get_tag_file_path", return_value=None), \
           patch("tagmanager.app.helpers.load_tags", return_value=dict(tags))


class TestBuildTagGraph(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tag_file = os.path.join(self.test_dir, "tags.json")
        import json
        with open(self.test_tag_file, "w") as f:
            json.dump(SAMPLE_TAGS, f)
        self.patcher = patch("tagmanager.app.helpers.get_tag_file_path", return_value=self.test_tag_file)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        import shutil; shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_returns_dict_with_required_keys(self):
        from tagmanager.app.graph.service import build_tag_graph
        result = build_tag_graph()
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIn("meta", result)
        self.assertEqual(result["meta"]["mode"], "tag")

    def test_node_count_equals_unique_tags(self):
        from tagmanager.app.graph.service import build_tag_graph
        result = build_tag_graph()
        all_tags = set()
        for tags in SAMPLE_TAGS.values():
            all_tags.update(t.lower() for t in tags)
        self.assertEqual(len(result["nodes"]), len(all_tags))

    def test_node_has_required_fields(self):
        from tagmanager.app.graph.service import build_tag_graph
        result = build_tag_graph()
        for node in result["nodes"]:
            self.assertIn("id", node)
            self.assertIn("label", node)
            self.assertIn("type", node)
            self.assertIn("size", node)
            self.assertIn("color", node)
            self.assertIn("group", node)
            self.assertIn("metadata", node)
            self.assertEqual(node["type"], "tag")

    def test_edge_weight_counts_cooccurrences(self):
        from tagmanager.app.graph.service import build_tag_graph
        result = build_tag_graph()
        # python+backend co-occur in main.py and utils.py → weight=2
        python_backend = [
            e for e in result["edges"]
            if set([e["source"], e["target"]]) == {"python", "backend"}
        ]
        self.assertEqual(len(python_backend), 1)
        self.assertEqual(int(python_backend[0]["weight"]), 2)

    def test_min_weight_filter(self):
        from tagmanager.app.graph.service import build_tag_graph
        all_edges = build_tag_graph(min_weight=1)["edges"]
        filtered_edges = build_tag_graph(min_weight=2)["edges"]
        self.assertLessEqual(len(filtered_edges), len(all_edges))

    def test_empty_data(self):
        from tagmanager.app.graph.service import build_tag_graph
        with patch("tagmanager.app.graph.service.load_tags", return_value={}):
            result = build_tag_graph()
        self.assertEqual(result["nodes"], [])
        self.assertEqual(result["edges"], [])

    def test_node_size_positive(self):
        from tagmanager.app.graph.service import build_tag_graph
        result = build_tag_graph()
        for node in result["nodes"]:
            self.assertGreater(node["size"], 0)


class TestBuildFileGraph(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tag_file = os.path.join(self.test_dir, "tags.json")
        with open(self.test_tag_file, "w") as f:
            json.dump(SAMPLE_TAGS, f)
        self.patcher = patch("tagmanager.app.helpers.get_tag_file_path", return_value=self.test_tag_file)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        import shutil; shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_returns_correct_mode(self):
        from tagmanager.app.graph.service import build_file_graph
        result = build_file_graph()
        self.assertEqual(result["meta"]["mode"], "file")

    def test_node_count_equals_file_count(self):
        from tagmanager.app.graph.service import build_file_graph
        result = build_file_graph(threshold=0.0)
        self.assertEqual(len(result["nodes"]), len(SAMPLE_TAGS))

    def test_threshold_1_produces_no_edges(self):
        from tagmanager.app.graph.service import build_file_graph
        result = build_file_graph(threshold=1.0)
        # No two files have identical tag sets → no edges
        self.assertEqual(result["edges"], [])

    def test_threshold_0_produces_some_edges(self):
        from tagmanager.app.graph.service import build_file_graph
        result = build_file_graph(threshold=0.0)
        # At threshold 0, all pairs with any shared tag should appear
        self.assertGreater(len(result["edges"]), 0)

    def test_edge_weight_between_0_and_1(self):
        from tagmanager.app.graph.service import build_file_graph
        result = build_file_graph(threshold=0.0)
        for edge in result["edges"]:
            self.assertGreaterEqual(edge["weight"], 0.0)
            self.assertLessEqual(edge["weight"], 1.0)

    def test_empty_data(self):
        from tagmanager.app.graph.service import build_file_graph
        with patch("tagmanager.app.graph.service.load_tags", return_value={}):
            result = build_file_graph()
        self.assertEqual(result["nodes"], [])
        self.assertEqual(result["edges"], [])


class TestBuildMixedGraph(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tag_file = os.path.join(self.test_dir, "tags.json")
        with open(self.test_tag_file, "w") as f:
            json.dump(SAMPLE_TAGS, f)
        self.patcher = patch("tagmanager.app.helpers.get_tag_file_path", return_value=self.test_tag_file)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        import shutil; shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_returns_correct_mode(self):
        from tagmanager.app.graph.service import build_mixed_graph
        result = build_mixed_graph()
        self.assertEqual(result["meta"]["mode"], "mixed")

    def test_has_both_node_types(self):
        from tagmanager.app.graph.service import build_mixed_graph
        result = build_mixed_graph()
        types = {n["type"] for n in result["nodes"]}
        self.assertIn("tag", types)
        self.assertTrue("file" in types or "folder" in types)

    def test_total_node_count(self):
        from tagmanager.app.graph.service import build_mixed_graph
        result = build_mixed_graph()
        all_tags = set()
        for tags in SAMPLE_TAGS.values():
            all_tags.update(t.lower() for t in tags)
        expected = len(SAMPLE_TAGS) + len(all_tags)
        self.assertEqual(len(result["nodes"]), expected)

    def test_edges_are_directed(self):
        from tagmanager.app.graph.service import build_mixed_graph
        result = build_mixed_graph()
        for edge in result["edges"]:
            self.assertTrue(edge["directed"])

    def test_edge_count_equals_total_tags(self):
        from tagmanager.app.graph.service import build_mixed_graph
        result = build_mixed_graph()
        total_tags = sum(len(v) for v in SAMPLE_TAGS.values())
        self.assertEqual(len(result["edges"]), total_tags)


class TestHexToRgb(unittest.TestCase):
    def test_non_six_hex_returns_gray(self):
        from tagmanager.app.graph.export import _hex_to_rgb

        self.assertEqual(_hex_to_rgb("#abc"), (128, 128, 128))


class TestExportGEXF(unittest.TestCase):
    def _make_graph(self):
        return {
            "nodes": [
                {"id": "python", "label": "python", "type": "tag", "size": 3.0,
                 "color": "#4e79a7", "group": 0,
                 "metadata": {"file_count": 2, "cluster_id": 0, "path": "", "extension": ""}},
                {"id": "backend", "label": "backend", "type": "tag", "size": 2.0,
                 "color": "#f28e2b", "group": 1,
                 "metadata": {"file_count": 1, "cluster_id": 1, "path": "", "extension": ""}},
            ],
            "edges": [
                {"source": "python", "target": "backend", "weight": 2.0,
                 "directed": False, "label": "shared by 2 files"},
            ],
            "meta": {"mode": "tag", "node_count": 2, "edge_count": 1, "total_files": 3},
        }

    def test_valid_xml(self):
        from tagmanager.app.graph.export import to_gexf
        gexf_str = to_gexf(self._make_graph())
        root = ET.fromstring(gexf_str)
        self.assertIsNotNone(root)

    def test_gexf_root_tag(self):
        from tagmanager.app.graph.export import to_gexf
        gexf_str = to_gexf(self._make_graph())
        root = ET.fromstring(gexf_str)
        self.assertIn("gexf", root.tag)

    def test_node_count_in_xml(self):
        from tagmanager.app.graph.export import to_gexf
        gexf_str = to_gexf(self._make_graph())
        root = ET.fromstring(gexf_str)
        ns = {"g": "http://gexf.net/1.3"}
        nodes = root.findall(".//g:node", ns)
        self.assertEqual(len(nodes), 2)

    def test_edge_count_in_xml(self):
        from tagmanager.app.graph.export import to_gexf
        gexf_str = to_gexf(self._make_graph())
        root = ET.fromstring(gexf_str)
        ns = {"g": "http://gexf.net/1.3"}
        edges = root.findall(".//g:edge", ns)
        self.assertEqual(len(edges), 1)

    def test_edge_weight_present(self):
        from tagmanager.app.graph.export import to_gexf
        gexf_str = to_gexf(self._make_graph())
        self.assertIn('weight="2.0"', gexf_str)

    def test_empty_graph(self):
        from tagmanager.app.graph.export import to_gexf
        empty = {"nodes": [], "edges": [], "meta": {"mode": "tag"}}
        gexf_str = to_gexf(empty)
        root = ET.fromstring(gexf_str)
        self.assertIsNotNone(root)


class TestExportGraphML(unittest.TestCase):
    def _make_graph(self):
        return {
            "nodes": [
                {"id": "python", "label": "python", "type": "tag", "size": 3.0,
                 "color": "#4e79a7", "group": 0,
                 "metadata": {"file_count": 2, "cluster_id": 0, "path": "", "extension": ""}},
            ],
            "edges": [
                {"source": "python", "target": "python", "weight": 1.0,
                 "directed": False, "label": "self"},
            ],
            "meta": {"mode": "tag"},
        }

    def test_valid_xml(self):
        from tagmanager.app.graph.export import to_graphml
        xml_str = to_graphml(self._make_graph())
        root = ET.fromstring(xml_str)
        self.assertIsNotNone(root)

    def test_graphml_root_tag(self):
        from tagmanager.app.graph.export import to_graphml
        xml_str = to_graphml(self._make_graph())
        root = ET.fromstring(xml_str)
        self.assertIn("graphml", root.tag)

    def test_key_declarations_present(self):
        from tagmanager.app.graph.export import to_graphml
        xml_str = to_graphml(self._make_graph())
        self.assertIn('attr.name="label"', xml_str)
        self.assertIn('attr.name="weight"', xml_str)

    def test_save_export(self):
        from tagmanager.app.graph.export import to_graphml, save_export
        with tempfile.NamedTemporaryFile(suffix=".graphml", delete=False) as f:
            path = f.name
        try:
            content = to_graphml(self._make_graph())
            save_export(content, path)
            with open(path, encoding="utf-8") as f:
                data = f.read()
            self.assertIn("graphml", data)
        finally:
            os.unlink(path)


class TestGenerateHTML(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_tag_file = os.path.join(self.test_dir, "tags.json")
        with open(self.test_tag_file, "w") as f:
            json.dump(SAMPLE_TAGS, f)
        self.patcher = patch("tagmanager.app.helpers.get_tag_file_path", return_value=self.test_tag_file)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        import shutil; shutil.rmtree(self.test_dir, ignore_errors=True)

    def _get_html(self, **kwargs):
        from tagmanager.app.graph.service import build_tag_graph
        from tagmanager.app.graph.html_generator import generate_html
        graph_data = build_tag_graph()
        return generate_html(graph_data, **kwargs)

    def test_returns_string(self):
        html = self._get_html()
        self.assertIsInstance(html, str)

    def test_contains_doctype(self):
        html = self._get_html()
        self.assertIn("<!DOCTYPE html>", html)

    def test_contains_graph_data(self):
        html = self._get_html()
        self.assertIn("GRAPH_DATA", html)

    def test_contains_forcegraph_reference(self):
        html = self._get_html()
        self.assertIn("ForceGraph", html)

    def test_contains_3d_graph_reference(self):
        html = self._get_html()
        self.assertIn("3d-force-graph", html)

    def test_contains_filter_panel_ids(self):
        html = self._get_html()
        for el_id in ("search", "min-weight", "min-degree", "max-degree",
                      "color-by", "highlight-cluster", "show-isolated"):
            self.assertIn(f'id="{el_id}"', html)

    def test_start_3d_flag(self):
        html_2d = self._get_html(start_3d=False)
        html_3d = self._get_html(start_3d=True)
        self.assertIn("INITIAL_3D = false", html_2d)
        self.assertIn("INITIAL_3D = true", html_3d)

    def test_server_port_embedded(self):
        html = self._get_html(server_port=12345)
        self.assertIn("SERVER_PORT = 12345", html)

    def test_no_server_port_is_null(self):
        html = self._get_html(server_port=None)
        self.assertIn("SERVER_PORT = null", html)

    def test_contains_gexf_download(self):
        html = self._get_html()
        self.assertIn("GEXF_DATA", html)
        self.assertIn("downloadGEXF", html)

    def test_contains_graphml_download(self):
        html = self._get_html()
        self.assertIn("GRAPHML_DATA", html)
        self.assertIn("downloadGraphML", html)


if __name__ == "__main__":
    unittest.main()
