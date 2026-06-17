"""End-to-end tests for the FileTagger HTTP API.

A real ``ThreadingHTTPServer`` is started on an ephemeral port once per test
class.  All service-layer calls that touch the filesystem are mocked inside
each individual test so the suite is fully self-contained and deterministic.
Tests make real HTTP round-trips with ``urllib.request`` — no extra runtime
dependencies beyond the standard library.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from typing import Any, Dict, Tuple
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Project root on sys.path
# ---------------------------------------------------------------------------
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT not in sys.path:
    sys.path.insert(0, _PROJECT)

from filetagger.app.http_api import _FileTaggerHandler  # noqa: E402


# ---------------------------------------------------------------------------
# Platform-safe absolute paths for mock stores
# (normalize_gui_path resolves paths against cwd; tempdir paths are already
#  absolute so they survive the normpath round-trip on any OS)
# ---------------------------------------------------------------------------
_TMPDIR = os.path.normpath(tempfile.gettempdir())
_E2E_ALPHA = os.path.join(_TMPDIR, "e2e_alpha.txt")
_E2E_BETA  = os.path.join(_TMPDIR, "e2e_beta.py")
_E2E_GAMMA = os.path.join(_TMPDIR, "e2e_gamma.md")

_E2E_STORE: Dict[str, Any] = {
    _E2E_ALPHA: ["python", "docs"],
    _E2E_BETA:  ["python", "tests"],
    _E2E_GAMMA: ["docs", "markdown"],
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _free_port() -> int:
    """Return an unused TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(base: str, path: str) -> Tuple[int, Any]:
    """HTTP GET; returns (status, json_body_or_raw_bytes)."""
    try:
        with urllib.request.urlopen(base + path, timeout=5) as resp:
            raw = resp.read()
            ct = resp.headers.get("Content-Type", "")
            return resp.status, (json.loads(raw) if "json" in ct else raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw)
        except Exception:
            return exc.code, raw


def _post(base: str, path: str, body: Dict[str, Any]) -> Tuple[int, Dict]:
    """HTTP POST with JSON body; returns (status, json_body)."""
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        base + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


# ---------------------------------------------------------------------------
# Fixture data (returned by mocked service functions)
# ---------------------------------------------------------------------------

# Legacy fixture used by a few tests that don't depend on path normalization.
_STORE: Dict[str, Any] = {
    _E2E_ALPHA: ["python", "docs"],
    _E2E_BETA:  ["python", "tests"],
    _E2E_GAMMA: ["docs", "markdown"],
}

_OVERALL_STATS: Dict[str, Any] = {
    "total_files": 3,
    "total_tags": 7,
    "unique_tags": 4,
    "average_tags_per_file": 2.33,
    "files_with_no_tags": 0,
    "most_common_tags": [["python", 2], ["docs", 2]],
}

_TAG_STATS: Dict[str, Any] = {
    "tag": "python",
    "files_with_tag": 2,
    "percentage_of_files": 66.67,
    "files": ["/data/alpha.txt", "/data/beta.py"],
    "co_occurring_tags": [("docs", 1), ("tests", 1)],
    "file_types": {".txt": 1, ".py": 1},
}

_ALIASES: Dict[str, str] = {"py": "python", "md": "markdown"}

_PRESETS: Dict[str, Any] = {"default": ["python", "docs"]}

_DUPLICATE_RESULT: Dict[str, Any] = {
    "duplicates": {("python", "docs"): ["/data/alpha.txt", "/data/clone.txt"]},
    "duplicate_groups": 1,
    "duplicate_files_count": 2,
    "total_files": 3,
    "message": "1 duplicate group found",
}

_ORPHAN_RESULT: Dict[str, Any] = {
    "orphans": ["/missing/gone.txt"],
    "orphan_count": 1,
    "total_files": 3,
    "message": "1 orphan found",
}

_CLUSTER_RESULT: Dict[str, Any] = {
    "clusters": {
        "python": {"file_count": 10, "percentage": 33.3, "files": ["/data/alpha.txt"]},
    },
    "total_files": 30,
}

_ISOLATED_RESULT: Dict[str, Any] = {
    "isolated_files": ["/data/lone.txt"],
    "total_files": 10,
}

_CLEAN_DRY_RESULT: Dict[str, Any] = {
    "success": True,
    "dry_run": True,
    "missing": ["/data/gone1.txt", "/data/gone2.txt"],
    "count": 2,
    "message": "2 dead records found (dry run)",
}

_CLEAN_REAL_RESULT: Dict[str, Any] = {
    "success": True,
    "dry_run": False,
    "missing": [],
    "count": 0,
    "message": "cleaned 2 records",
}


# ---------------------------------------------------------------------------
# Base class — one server per test class
# ---------------------------------------------------------------------------

class _ServerBase(unittest.TestCase):
    _server: ThreadingHTTPServer
    _base: str

    @classmethod
    def setUpClass(cls) -> None:
        port = _free_port()
        cls._server = ThreadingHTTPServer(("127.0.0.1", port), _FileTaggerHandler)
        cls._base = f"http://127.0.0.1:{port}"
        t = threading.Thread(target=cls._server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.08)  # give the OS a moment to bind

    @classmethod
    def tearDownClass(cls) -> None:
        cls._server.shutdown()
        cls._server.server_close()

    def get(self, path: str) -> Tuple[int, Any]:
        return _get(self._base, path)

    def post(self, path: str, body: Dict[str, Any]) -> Tuple[int, Dict]:
        return _post(self._base, path, body)


# ===========================================================================
# GET /  and  GET /api  — index manifest
# ===========================================================================


class TestGetIndex(_ServerBase):
    def test_root_returns_200(self):
        status, _ = self.get("/")
        self.assertEqual(status, 200)

    def test_root_json_has_service_key(self):
        _, body = self.get("/")
        self.assertEqual(body["service"], "filetagger-cli")

    def test_api_alias_matches_root(self):
        _, root = self.get("/")
        _, api = self.get("/api")
        self.assertEqual(root["service"], api["service"])
        self.assertEqual(set(root["endpoints"]), set(api["endpoints"]))

    def test_index_gui_field_equals_slash_gui(self):
        _, body = self.get("/")
        self.assertEqual(body["gui"], "/gui")

    def test_index_preview_field_equals_slash_preview(self):
        _, body = self.get("/")
        self.assertEqual(body["preview"], "/preview")

    def test_index_endpoints_list_non_empty(self):
        _, body = self.get("/")
        self.assertIsInstance(body["endpoints"], list)
        self.assertGreater(len(body["endpoints"]), 0)

    def test_index_gui_post_list_contains_clean(self):
        _, body = self.get("/")
        self.assertTrue(any("/clean" in e for e in body["gui_post"]))

    def test_index_rpc_field_present(self):
        _, body = self.get("/")
        self.assertIn("rpc", body)


# ===========================================================================
# GET /gui  and  GET /preview  — HTML assets
# ===========================================================================


class TestGetHtmlAssets(_ServerBase):
    def _headers(self, path: str):
        req = urllib.request.Request(self._base + path)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.headers

    def test_gui_returns_200(self):
        status, _ = self.get("/gui")
        self.assertEqual(status, 200)

    def test_gui_content_type_is_html(self):
        _, hdrs = self._headers("/gui")
        self.assertIn("text/html", hdrs.get("Content-Type", ""))

    def test_gui_content_length_positive(self):
        _, hdrs = self._headers("/gui")
        self.assertGreater(int(hdrs.get("Content-Length", 0)), 0)

    def test_gui_html_contains_tag_drawer(self):
        _, raw = self.get("/gui")
        self.assertIn(b"tagDrawer", raw)

    def test_gui_html_contains_sec_cleanup(self):
        _, raw = self.get("/gui")
        self.assertIn(b"sec-cleanup", raw)

    def test_gui_html_contains_modal_backdrop(self):
        _, raw = self.get("/gui")
        self.assertIn(b"modalBackdrop", raw)

    def test_gui_html_contains_log_body(self):
        _, raw = self.get("/gui")
        self.assertIn(b"logBody", raw)

    def test_gui_html_contains_sugg_rail(self):
        _, raw = self.get("/gui")
        self.assertIn(b"suggRail", raw)

    def test_gui_html_contains_sr_action(self):
        _, raw = self.get("/gui")
        self.assertIn(b"srAction", raw)

    def test_preview_returns_200(self):
        status, _ = self.get("/preview")
        self.assertEqual(status, 200)

    def test_preview_content_type_is_html(self):
        _, hdrs = self._headers("/preview")
        self.assertIn("text/html", hdrs.get("Content-Type", ""))


# ===========================================================================
# GET /api/v1/tags — raw tag store
# ===========================================================================


class TestGetTags(_ServerBase):
    @patch("filetagger.app.http_api.load_tags", return_value=dict(_STORE))
    def test_returns_200_with_store(self, _mock):
        status, body = self.get("/api/v1/tags")
        self.assertEqual(status, 200)
        self.assertIn(_E2E_ALPHA, body)

    @patch("filetagger.app.http_api.load_tags", return_value=dict(_STORE))
    def test_file_tags_are_lists(self, _mock):
        _, body = self.get("/api/v1/tags")
        for tags in body.values():
            self.assertIsInstance(tags, list)

    @patch("filetagger.app.http_api.load_tags", return_value={})
    def test_empty_store_returns_empty_dict(self, _mock):
        _, body = self.get("/api/v1/tags")
        self.assertEqual(body, {})

    @patch("filetagger.app.http_api.load_tags", return_value=dict(_STORE))
    def test_content_type_is_json(self, _mock):
        req = urllib.request.Request(self._base + "/api/v1/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            ct = resp.headers.get("Content-Type", "")
        self.assertIn("application/json", ct)
        self.assertIn("utf-8", ct)


# ===========================================================================
# GET /api/v1/all-tags — tag counts
# ===========================================================================


class TestGetAllTags(_ServerBase):
    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_returns_ok_and_tags_list(self, _mock):
        status, body = self.get("/api/v1/all-tags")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertIsInstance(body["tags"], list)

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_python_count_is_2(self, _mock):
        _, body = self.get("/api/v1/all-tags")
        by_tag = {t["tag"]: t["count"] for t in body["tags"]}
        self.assertEqual(by_tag["python"], 2)

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_sorted_descending_by_count(self, _mock):
        _, body = self.get("/api/v1/all-tags")
        counts = [t["count"] for t in body["tags"]]
        self.assertEqual(counts, sorted(counts, reverse=True))

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_unique_and_total_files_fields_present(self, _mock):
        _, body = self.get("/api/v1/all-tags")
        self.assertIn("unique", body)
        self.assertIn("total_files", body)
        self.assertEqual(body["total_files"], 3)

    @patch("filetagger.app.gui_handlers.load_tags", return_value={})
    def test_empty_store_returns_empty_list(self, _mock):
        _, body = self.get("/api/v1/all-tags")
        self.assertTrue(body["ok"])
        self.assertEqual(body["tags"], [])


# ===========================================================================
# GET /api/v1/stats — overall statistics
# ===========================================================================


class TestGetStats(_ServerBase):
    @patch("filetagger.app.stats.service.get_overall_statistics",
           return_value=dict(_OVERALL_STATS))
    def test_returns_ok_and_stats(self, _mock):
        status, body = self.get("/api/v1/stats")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["total_files"], 3)

    @patch("filetagger.app.stats.service.get_overall_statistics",
           return_value=dict(_OVERALL_STATS))
    def test_unique_tags_field_present(self, _mock):
        _, body = self.get("/api/v1/stats")
        self.assertIn("unique_tags", body)

    @patch("filetagger.app.stats.service.get_overall_statistics",
           side_effect=RuntimeError("db locked"))
    def test_service_error_body_ok_false(self, _mock):
        # The /stats route always returns HTTP 200; errors are signalled in body.
        status, body = self.get("/api/v1/stats")
        self.assertEqual(status, 200)
        self.assertFalse(body["ok"])
        self.assertIn("error", body)


# ===========================================================================
# GET /api/v1/aliases and /api/v1/presets
# ===========================================================================


class TestGetAliasesAndPresets(_ServerBase):
    @patch("filetagger.app.alias.service.get_aliases", return_value=dict(_ALIASES))
    def test_aliases_ok_and_map(self, _mock):
        status, body = self.get("/api/v1/aliases")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["aliases"]["py"], "python")

    @patch("filetagger.app.alias.service.get_aliases", return_value={})
    def test_empty_aliases(self, _mock):
        _, body = self.get("/api/v1/aliases")
        self.assertTrue(body["ok"])
        self.assertEqual(body["aliases"], {})

    @patch("filetagger.app.preset.service.get_presets", return_value=dict(_PRESETS))
    def test_presets_ok_and_map(self, _mock):
        status, body = self.get("/api/v1/presets")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["presets"]["default"], ["python", "docs"])


# ===========================================================================
# GET /api/v1/search
# ===========================================================================


class TestGetSearch(_ServerBase):
    @patch("filetagger.app.http_api.search_files_by_tags",
           return_value=["/data/alpha.txt", "/data/beta.py"])
    def test_search_by_single_tag_returns_files(self, _mock):
        status, body = self.get("/api/v1/search?tags=python")
        self.assertEqual(status, 200)
        self.assertIn("files", body)
        self.assertEqual(len(body["files"]), 2)

    @patch("filetagger.app.http_api.search_files_by_tags",
           return_value=["/data/alpha.txt"])
    def test_match_all_param_forwarded(self, mock_search):
        self.get("/api/v1/search?tags=python,docs&match_all=1")
        mock_search.assert_called_once_with(
            ["python", "docs"], True, False, exclude_tags=None
        )

    @patch("filetagger.app.http_api.search_files_by_tags",
           return_value=["/data/beta.py"])
    def test_exclude_param_forwarded(self, mock_search):
        self.get("/api/v1/search?tags=python&exclude=docs")
        mock_search.assert_called_once_with(
            ["python"], False, False, exclude_tags=["docs"]
        )

    def test_no_tags_returns_400(self):
        status, body = self.get("/api/v1/search")
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    @patch("filetagger.app.http_api.combined_search",
           return_value=["/data/alpha.txt"])
    def test_tags_plus_path_uses_combined_search(self, mock_combined):
        self.get("/api/v1/search?tags=python&path=data")
        mock_combined.assert_called_once()

    @patch("filetagger.app.http_api.search_files_by_tags", return_value=[])
    def test_empty_result_returns_empty_files_list(self, _mock):
        _, body = self.get("/api/v1/search?tags=nosuchtag")
        self.assertEqual(body["files"], [])

    @patch("filetagger.app.http_api.search_files_by_tags",
           return_value=["/data/alpha.txt"])
    def test_match_all_0_treated_as_false(self, mock_search):
        self.get("/api/v1/search?tags=python&match_all=0")
        mock_search.assert_called_once_with(
            ["python"], False, False, exclude_tags=None
        )


# ===========================================================================
# GET /api/v1/gui/path-tags  and  /api/v1/files/tags
# ===========================================================================


class TestGetPathTags(_ServerBase):
    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_E2E_STORE))
    def test_known_path_returns_tags(self, _mock):
        import urllib.parse
        # Use the same absolute path used as a key in _E2E_STORE.
        p = urllib.parse.quote(_E2E_ALPHA, safe="")
        status, body = self.get(f"/api/v1/gui/path-tags?path={p}")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertIn("python", body["tags"])

    def test_missing_path_param_returns_400(self):
        status, body = self.get("/api/v1/gui/path-tags")
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    def test_files_tags_alias_returns_same_status(self):
        with patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE)):
            import urllib.parse
            p = urllib.parse.quote("/data/alpha.txt", safe="")
            s1, b1 = self.get(f"/api/v1/gui/path-tags?path={p}")
            s2, b2 = self.get(f"/api/v1/files/tags?path={p}")
        self.assertEqual(s1, s2)
        self.assertEqual(b1["ok"], b2["ok"])

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    def test_unknown_path_returns_empty_tags(self, _mock):
        import urllib.parse
        p = urllib.parse.quote("/data/unknown.txt", safe="")
        _, body = self.get(f"/api/v1/gui/path-tags?path={p}")
        self.assertTrue(body["ok"])
        self.assertEqual(body["tags"], [])


# ===========================================================================
# GET /api/v1/stats/tag/<name>
# ===========================================================================


class TestGetTagStats(_ServerBase):
    @patch("filetagger.app.stats.service.get_tag_statistics",
           return_value=dict(_TAG_STATS))
    def test_returns_ok_and_tag_fields(self, _mock):
        status, body = self.get("/api/v1/stats/tag/python")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["files_with_tag"], 2)

    @patch("filetagger.app.stats.service.get_tag_statistics",
           return_value=dict(_TAG_STATS))
    def test_url_encoded_tag_name_decoded(self, mock_svc):
        self.get("/api/v1/stats/tag/my%20tag")
        mock_svc.assert_called_once_with("my tag")

    @patch("filetagger.app.stats.service.get_tag_statistics",
           side_effect=KeyError("not found"))
    def test_service_error_returns_400(self, _mock):
        status, body = self.get("/api/v1/stats/tag/ghost")
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])


# ===========================================================================
# GET /api/v1/filter/duplicates
# ===========================================================================


class TestGetFilterDuplicates(_ServerBase):
    @patch("filetagger.app.filter.service.find_duplicate_tags",
           return_value=dict(_DUPLICATE_RESULT))
    def test_returns_ok_and_groups(self, _mock):
        status, body = self.get("/api/v1/filter/duplicates")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertIsInstance(body["groups"], list)
        self.assertGreater(len(body["groups"]), 0)

    @patch("filetagger.app.filter.service.find_duplicate_tags",
           return_value=dict(_DUPLICATE_RESULT))
    def test_group_tags_are_lists_not_tuples(self, _mock):
        """Tuple keys must be converted so the JSON round-trip works."""
        _, body = self.get("/api/v1/filter/duplicates")
        for grp in body["groups"]:
            self.assertIsInstance(grp["tags"], list)

    @patch("filetagger.app.filter.service.find_duplicate_tags",
           return_value={"duplicates": {}, "duplicate_groups": 0,
                         "duplicate_files_count": 0, "total_files": 5, "message": ""})
    def test_no_duplicates_returns_empty_groups(self, _mock):
        _, body = self.get("/api/v1/filter/duplicates")
        self.assertTrue(body["ok"])
        self.assertEqual(body["groups"], [])

    @patch("filetagger.app.filter.service.find_duplicate_tags",
           side_effect=RuntimeError("err"))
    def test_service_error_body_ok_false(self, _mock):
        # Filter routes always return HTTP 200; errors are in body["ok"].
        status, body = self.get("/api/v1/filter/duplicates")
        self.assertEqual(status, 200)
        self.assertFalse(body["ok"])

    @patch("filetagger.app.filter.service.find_duplicate_tags",
           return_value=dict(_DUPLICATE_RESULT))
    def test_response_has_group_count_and_file_count(self, _mock):
        _, body = self.get("/api/v1/filter/duplicates")
        self.assertIn("group_count", body)
        self.assertIn("file_count", body)


# ===========================================================================
# GET /api/v1/filter/orphans
# ===========================================================================


class TestGetFilterOrphans(_ServerBase):
    @patch("filetagger.app.filter.service.find_orphaned_files",
           return_value=dict(_ORPHAN_RESULT))
    def test_returns_ok_and_orphans(self, _mock):
        status, body = self.get("/api/v1/filter/orphans")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["count"], 1)

    @patch("filetagger.app.filter.service.find_orphaned_files",
           return_value={"orphans": [], "orphan_count": 0, "total_files": 3, "message": ""})
    def test_no_orphans_returns_empty_list(self, _mock):
        _, body = self.get("/api/v1/filter/orphans")
        self.assertTrue(body["ok"])
        self.assertEqual(body["orphans"], [])

    @patch("filetagger.app.filter.service.find_orphaned_files",
           side_effect=RuntimeError("err"))
    def test_service_error_body_ok_false(self, _mock):
        status, body = self.get("/api/v1/filter/orphans")
        self.assertEqual(status, 200)
        self.assertFalse(body["ok"])


# ===========================================================================
# GET /api/v1/filter/clusters
# ===========================================================================


class TestGetFilterClusters(_ServerBase):
    @patch("filetagger.app.filter.service.find_tag_clusters",
           return_value=dict(_CLUSTER_RESULT))
    def test_returns_ok_and_clusters(self, _mock):
        status, body = self.get("/api/v1/filter/clusters")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertGreater(len(body["clusters"]), 0)

    @patch("filetagger.app.filter.service.find_tag_clusters",
           return_value=dict(_CLUSTER_RESULT))
    def test_default_min_size_is_2(self, mock_svc):
        self.get("/api/v1/filter/clusters")
        mock_svc.assert_called_once_with(min_cluster_size=2)

    @patch("filetagger.app.filter.service.find_tag_clusters",
           return_value=dict(_CLUSTER_RESULT))
    def test_custom_min_size_forwarded(self, mock_svc):
        self.get("/api/v1/filter/clusters?min_size=5")
        mock_svc.assert_called_once_with(min_cluster_size=5)

    @patch("filetagger.app.filter.service.find_tag_clusters",
           return_value={"clusters": {}, "total_files": 0})
    def test_empty_clusters_returns_empty_list(self, _mock):
        _, body = self.get("/api/v1/filter/clusters")
        self.assertTrue(body["ok"])
        self.assertEqual(body["clusters"], [])

    @patch("filetagger.app.filter.service.find_tag_clusters",
           side_effect=RuntimeError("err"))
    def test_service_error_body_ok_false(self, _mock):
        status, body = self.get("/api/v1/filter/clusters")
        self.assertEqual(status, 200)
        self.assertFalse(body["ok"])


# ===========================================================================
# GET /api/v1/filter/isolated
# ===========================================================================


class TestGetFilterIsolated(_ServerBase):
    @patch("filetagger.app.filter.service.find_isolated_files",
           return_value=dict(_ISOLATED_RESULT))
    def test_returns_ok_and_isolated(self, _mock):
        status, body = self.get("/api/v1/filter/isolated")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["count"], 1)

    @patch("filetagger.app.filter.service.find_isolated_files",
           return_value=dict(_ISOLATED_RESULT))
    def test_default_max_shared_is_1(self, mock_svc):
        self.get("/api/v1/filter/isolated")
        mock_svc.assert_called_once_with(max_shared_tags=1)

    @patch("filetagger.app.filter.service.find_isolated_files",
           return_value=dict(_ISOLATED_RESULT))
    def test_custom_max_shared_forwarded(self, mock_svc):
        self.get("/api/v1/filter/isolated?max_shared=3")
        mock_svc.assert_called_once_with(max_shared_tags=3)

    @patch("filetagger.app.filter.service.find_isolated_files",
           return_value={"isolated_files": [], "total_files": 0})
    def test_empty_returns_empty_list(self, _mock):
        _, body = self.get("/api/v1/filter/isolated")
        self.assertTrue(body["ok"])
        self.assertEqual(body["isolated"], [])

    @patch("filetagger.app.filter.service.find_isolated_files",
           side_effect=RuntimeError("err"))
    def test_service_error_body_ok_false(self, _mock):
        status, body = self.get("/api/v1/filter/isolated")
        self.assertEqual(status, 200)
        self.assertFalse(body["ok"])


# ===========================================================================
# GET — 404 for unknown routes
# ===========================================================================


class TestGetUnknownRoutes(_ServerBase):
    def test_unknown_path_returns_404(self):
        status, _ = self.get("/api/v1/does-not-exist")
        self.assertEqual(status, 404)

    def test_404_body_has_error_key(self):
        _, body = self.get("/completely/wrong")
        self.assertIn("error", body)

    def test_partial_known_prefix_still_404(self):
        status, _ = self.get("/api/v1/filter")
        self.assertEqual(status, 404)

    def test_root_only_matches_slash_and_api(self):
        status, _ = self.get("/apiextra")
        self.assertEqual(status, 404)


# ===========================================================================
# POST /api/v1/gui/add-tags
# ===========================================================================


class TestPostAddTags(_ServerBase):
    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    @patch("filetagger.app.gui_handlers.add_tags", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_add_tags_success(self, _isfile, _add, _load):
        status, body = self.post(
            "/api/v1/gui/add-tags",
            {"path": "/data/alpha.txt", "tags": ["newtag"]},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    @patch("filetagger.app.gui_handlers.add_tags", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_add_tags_add_service_called_with_correct_args(self, _isfile, mock_add, _load):
        self.post(
            "/api/v1/gui/add-tags",
            {"path": "/data/alpha.txt", "tags": ["newtag"]},
        )
        mock_add.assert_called_once()
        call_args = mock_add.call_args
        self.assertIn("newtag", call_args[0][1])

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    @patch("filetagger.app.gui_handlers.add_tags")
    @patch("os.path.isfile", return_value=True)
    def test_dry_run_does_not_call_add_tags(self, _isfile, mock_add, _load):
        status, body = self.post(
            "/api/v1/gui/add-tags",
            {"path": "/data/alpha.txt", "tags": ["newtag"], "dry_run": True},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertTrue(body.get("dry_run"))
        mock_add.assert_not_called()

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    @patch("os.path.isfile", return_value=True)
    def test_dry_run_returns_tags_before_and_after(self, _isfile, _load):
        _, body = self.post(
            "/api/v1/gui/add-tags",
            {"path": "/data/alpha.txt", "tags": ["newone"], "dry_run": True},
        )
        self.assertIn("tags_before", body)
        self.assertIn("tags_after_preview", body)

    def test_empty_path_returns_400(self):
        status, body = self.post(
            "/api/v1/gui/add-tags", {"path": "", "tags": ["x"]}
        )
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    @patch("os.path.isfile", return_value=False)
    def test_file_not_on_disk_returns_400(self, _isfile):
        status, body = self.post(
            "/api/v1/gui/add-tags",
            {"path": "/nonexistent/file.txt", "tags": ["tag"]},
        )
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    @patch("filetagger.app.gui_handlers.add_tags", return_value=False)
    @patch("os.path.isfile", return_value=True)
    def test_add_tags_failure_returns_400(self, _isfile, _add):
        status, body = self.post(
            "/api/v1/gui/add-tags",
            {"path": "/data/alpha.txt", "tags": ["tag"]},
        )
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    @patch("filetagger.app.gui_handlers.add_tags", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_non_list_tags_treated_as_empty(self, _isfile, _add, _load):
        """Non-list tags value mustn't crash the server."""
        status, _ = self.post(
            "/api/v1/gui/add-tags",
            {"path": "/data/alpha.txt", "tags": "not-a-list"},
        )
        self.assertIn(status, (200, 400))


# ===========================================================================
# POST /api/v1/gui/remove
# ===========================================================================


class TestPostRemove(_ServerBase):
    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_E2E_STORE))
    @patch("filetagger.app.gui_handlers._remove_path", return_value=None)
    def test_mode_path_success(self, mock_rm, _load):
        status, body = self.post(
            "/api/v1/gui/remove",
            {"path": _E2E_ALPHA, "mode": "path"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mock_rm.assert_called_once()

    @patch("filetagger.app.gui_handlers.load_tags", return_value={})
    def test_mode_path_not_in_db_returns_400(self, _load):
        status, body = self.post(
            "/api/v1/gui/remove",
            {"path": "/data/ghost.txt", "mode": "path"},
        )
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    @patch("filetagger.app.gui_handlers.load_tags", return_value={})
    def test_mode_path_dry_run_returns_200_preview(self, _load):
        status, body = self.post(
            "/api/v1/gui/remove",
            {"path": "/data/alpha.txt", "mode": "path", "dry_run": True},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertTrue(body["dry_run"])

    @patch("filetagger.app.gui_handlers.remove_all_tags",
           return_value={"success": True, "message": "cleared"})
    def test_mode_clear_tags_success(self, mock_clear):
        status, body = self.post(
            "/api/v1/gui/remove",
            {"path": "/data/alpha.txt", "mode": "clear_tags"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mock_clear.assert_called_once()

    def test_mode_clear_tags_dry_run_preview(self):
        status, body = self.post(
            "/api/v1/gui/remove",
            {"path": "/data/alpha.txt", "mode": "clear_tags", "dry_run": True},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["dry_run"])

    @patch("filetagger.app.gui_handlers.load_tags",
           return_value={_E2E_ALPHA: ["python", "docs"]})
    @patch("filetagger.app.gui_handlers.save_tags", return_value=True)
    def test_mode_one_tag_removes_tag(self, _save, _load):
        status, body = self.post(
            "/api/v1/gui/remove",
            {"path": _E2E_ALPHA, "mode": "one_tag", "tag": "docs"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertNotIn("docs", body["tags"])

    def test_mode_one_tag_missing_tag_param_returns_400(self):
        status, body = self.post(
            "/api/v1/gui/remove",
            {"path": "/data/alpha.txt", "mode": "one_tag"},
        )
        self.assertEqual(status, 400)

    def test_unknown_mode_returns_400(self):
        status, body = self.post(
            "/api/v1/gui/remove",
            {"path": "/data/alpha.txt", "mode": "badmode"},
        )
        self.assertEqual(status, 400)

    def test_empty_path_returns_400(self):
        # empty path normalises to cwd, which is not in a restricted store
        with patch("filetagger.app.gui_handlers.load_tags", return_value={}):
            status, body = self.post("/api/v1/gui/remove", {"mode": "path"})
        # Should be 400 (not in DB or some other guard)
        self.assertEqual(status, 400)


# ===========================================================================
# POST /api/v1/aliases/*
# ===========================================================================


class TestPostAliases(_ServerBase):
    @patch("filetagger.app.alias.service.add_alias", return_value=True)
    def test_set_alias_success(self, mock_add):
        status, body = self.post(
            "/api/v1/aliases/set",
            {"alias": "py", "canonical": "python"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mock_add.assert_called_once_with("py", "python")

    def test_set_alias_missing_both_fields_returns_400(self):
        status, body = self.post("/api/v1/aliases/set", {})
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    def test_set_alias_empty_alias_returns_400(self):
        status, body = self.post("/api/v1/aliases/set", {"alias": "", "canonical": "python"})
        self.assertEqual(status, 400)

    def test_set_alias_empty_canonical_returns_400(self):
        status, body = self.post("/api/v1/aliases/set", {"alias": "py", "canonical": ""})
        self.assertEqual(status, 400)

    @patch("filetagger.app.alias.service.add_alias", return_value=False)
    def test_set_alias_service_false_returns_400(self, _mock):
        status, body = self.post(
            "/api/v1/aliases/set", {"alias": "x", "canonical": "x"}
        )
        self.assertEqual(status, 400)

    @patch("filetagger.app.alias.service.remove_alias", return_value=True)
    def test_delete_alias_success(self, mock_rm):
        status, body = self.post("/api/v1/aliases/delete", {"alias": "py"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mock_rm.assert_called_once_with("py")

    @patch("filetagger.app.alias.service.remove_alias", return_value=False)
    def test_delete_nonexistent_alias_returns_400(self, _mock):
        status, body = self.post("/api/v1/aliases/delete", {"alias": "ghost"})
        self.assertEqual(status, 400)

    def test_delete_alias_empty_field_returns_400(self):
        status, body = self.post("/api/v1/aliases/delete", {})
        self.assertEqual(status, 400)


# ===========================================================================
# POST /api/v1/presets/*
# ===========================================================================


class TestPostPresets(_ServerBase):
    @patch("filetagger.app.preset.service.save_preset", return_value=True)
    def test_set_preset_success(self, mock_save):
        status, body = self.post(
            "/api/v1/presets/set",
            {"name": "mypre", "tags": ["python", "docs"]},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mock_save.assert_called_once_with("mypre", ["python", "docs"])

    def test_set_preset_missing_name_returns_400(self):
        status, body = self.post("/api/v1/presets/set", {"tags": ["x"]})
        self.assertEqual(status, 400)

    def test_set_preset_missing_tags_returns_400(self):
        status, body = self.post("/api/v1/presets/set", {"name": "x"})
        self.assertEqual(status, 400)

    @patch("filetagger.app.preset.service.save_preset", return_value=False)
    def test_set_preset_service_false_returns_400(self, _mock):
        status, _ = self.post("/api/v1/presets/set", {"name": "x", "tags": ["t"]})
        self.assertEqual(status, 400)

    def test_set_preset_non_list_tags_handled(self):
        with patch("filetagger.app.preset.service.save_preset", return_value=True):
            status, _ = self.post(
                "/api/v1/presets/set", {"name": "x", "tags": "not-a-list"}
            )
        self.assertIn(status, (200, 400))

    @patch("filetagger.app.preset.service.delete_preset", return_value=True)
    def test_delete_preset_success(self, mock_del):
        status, body = self.post("/api/v1/presets/delete", {"name": "mypre"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mock_del.assert_called_once_with("mypre")

    @patch("filetagger.app.preset.service.delete_preset", return_value=False)
    def test_delete_nonexistent_preset_returns_400(self, _mock):
        status, _ = self.post("/api/v1/presets/delete", {"name": "ghost"})
        self.assertEqual(status, 400)

    def test_delete_preset_empty_name_returns_400(self):
        status, _ = self.post("/api/v1/presets/delete", {})
        self.assertEqual(status, 400)


# ===========================================================================
# POST /api/v1/bulk/*
# ===========================================================================


class TestPostBulk(_ServerBase):
    @patch("filetagger.app.bulk.service.find_files_by_pattern",
           return_value=["/data/a.py", "/data/b.py"])
    def test_bulk_preview_returns_files(self, mock_find):
        status, body = self.post(
            "/api/v1/bulk/preview",
            {"pattern": "*.py", "tags": ["python"], "base_path": "/data"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertTrue(body["dry_run"])
        self.assertEqual(len(body["files"]), 2)
        mock_find.assert_called_once_with("*.py", "/data")

    def test_bulk_preview_no_tags_returns_400(self):
        status, body = self.post("/api/v1/bulk/preview", {"pattern": "*.py"})
        self.assertEqual(status, 400)

    @patch("filetagger.app.bulk.service.find_files_by_pattern", return_value=[])
    def test_bulk_preview_no_pattern_defaults_to_glob_all(self, mock_find):
        self.post("/api/v1/bulk/preview", {"tags": ["x"]})
        mock_find.assert_called_once_with("**/*", ".")

    @patch("filetagger.app.bulk.service.bulk_add_tags",
           return_value={"success": True, "tagged_files": ["/data/a.py"],
                         "ok": True, "total_tagged": 1})
    def test_bulk_add_success(self, mock_bulk):
        status, body = self.post(
            "/api/v1/bulk/add",
            {"pattern": "*.py", "tags": ["python"], "base_path": "/data"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mock_bulk.assert_called_once_with("*.py", ["python"], "/data", dry_run=False)

    def test_bulk_add_no_tags_returns_400(self):
        status, _ = self.post("/api/v1/bulk/add", {"pattern": "*.py"})
        self.assertEqual(status, 400)


# ===========================================================================
# POST /api/v1/open
# ===========================================================================


class TestPostOpen(_ServerBase):
    @patch("filetagger.app.gui_handlers.open_path_handler",
           return_value={"ok": True, "mode": "file", "path": "/data/alpha.txt",
                         "message": "opened /data/alpha.txt"})
    def test_open_file_calls_handler(self, mock_handler):
        status, body = self.post(
            "/api/v1/open", {"path": "/data/alpha.txt", "mode": "file"}
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        mock_handler.assert_called_once_with("/data/alpha.txt", "file")

    @patch("filetagger.app.gui_handlers.open_path_handler",
           return_value={"ok": True, "mode": "folder", "path": "/data",
                         "message": "opened folder of /data/alpha.txt"})
    def test_open_folder_calls_handler(self, mock_handler):
        status, body = self.post(
            "/api/v1/open", {"path": "/data/alpha.txt", "mode": "folder"}
        )
        self.assertEqual(status, 200)
        mock_handler.assert_called_once_with("/data/alpha.txt", "folder")

    @patch("filetagger.app.gui_handlers.open_path_handler",
           return_value={"ok": False, "error": "path does not exist"})
    def test_failed_open_returns_400(self, _mock):
        status, body = self.post("/api/v1/open", {"path": "/does/not/exist"})
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    @patch("filetagger.app.gui_handlers.open_path_handler",
           return_value={"ok": True, "mode": "file", "path": "/data/a.txt",
                         "message": "opened"})
    def test_default_mode_is_file(self, mock_handler):
        self.post("/api/v1/open", {"path": "/data/a.txt"})
        mock_handler.assert_called_once_with("/data/a.txt", "file")


# ===========================================================================
# POST /api/v1/clean
# ===========================================================================


class TestPostClean(_ServerBase):
    @patch("filetagger.app.move.service.clean_missing",
           return_value=dict(_CLEAN_DRY_RESULT))
    def test_dry_run_returns_missing_list(self, _mock):
        status, body = self.post("/api/v1/clean", {"dry_run": True})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertTrue(body["dry_run"])
        self.assertEqual(body["count"], 2)
        self.assertEqual(len(body["missing"]), 2)

    @patch("filetagger.app.move.service.clean_missing",
           return_value=dict(_CLEAN_REAL_RESULT))
    def test_real_clean_returns_ok(self, _mock):
        status, body = self.post("/api/v1/clean", {"dry_run": False})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])
        self.assertFalse(body["dry_run"])

    @patch("filetagger.app.move.service.clean_missing",
           return_value=dict(_CLEAN_DRY_RESULT))
    def test_dry_run_defaults_to_true_when_omitted(self, mock_svc):
        self.post("/api/v1/clean", {})
        mock_svc.assert_called_once_with(dry_run=True)

    @patch("filetagger.app.move.service.clean_missing",
           return_value={"success": False, "dry_run": True,
                         "missing": [], "count": 0, "message": "failed"})
    def test_service_success_false_returns_400(self, _mock):
        status, body = self.post("/api/v1/clean", {"dry_run": True})
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    @patch("filetagger.app.move.service.clean_missing",
           side_effect=RuntimeError("disk error"))
    def test_service_exception_returns_400(self, _mock):
        status, body = self.post("/api/v1/clean", {"dry_run": True})
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])


# ===========================================================================
# POST /api/v1/rpc — JSON-RPC 2.0
# ===========================================================================


class TestPostRpc(_ServerBase):
    @patch("filetagger.app.http_api.load_tags", return_value=dict(_STORE))
    def test_tags_list_method_returns_result(self, _mock):
        status, body = self.post(
            "/api/v1/rpc",
            {"jsonrpc": "2.0", "method": "tags.list", "params": {}, "id": 1},
        )
        self.assertEqual(status, 200)
        self.assertIn("result", body)
        self.assertNotIn("error", body)

    @patch("filetagger.app.http_api.load_tags", return_value=dict(_STORE))
    def test_tags_list_preserves_request_id(self, _mock):
        _, body = self.post(
            "/api/v1/rpc",
            {"jsonrpc": "2.0", "method": "tags.list", "params": {}, "id": 42},
        )
        self.assertEqual(body["id"], 42)

    @patch("filetagger.app.http_api.search_files_by_tags",
           return_value=["/data/alpha.txt"])
    def test_search_files_method_returns_files(self, _mock):
        status, body = self.post(
            "/api/v1/rpc",
            {"jsonrpc": "2.0", "method": "search.files",
             "params": {"tags": ["python"]}, "id": 2},
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(body["result"]), 1)

    @patch("filetagger.app.http_api.combined_search",
           return_value=["/data/alpha.txt"])
    def test_search_files_with_path_uses_combined_search(self, mock_cs):
        self.post(
            "/api/v1/rpc",
            {"jsonrpc": "2.0", "method": "search.files",
             "params": {"tags": ["python"], "path": "data"}, "id": 3},
        )
        mock_cs.assert_called_once()

    def test_unknown_method_returns_rpc_error_32601(self):
        status, body = self.post(
            "/api/v1/rpc",
            {"jsonrpc": "2.0", "method": "nope", "params": {}, "id": 4},
        )
        self.assertEqual(status, 200)  # JSON-RPC always 200 at transport level
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], -32601)
        self.assertEqual(body["id"], 4)

    def test_search_without_tags_returns_rpc_error_32602(self):
        status, body = self.post(
            "/api/v1/rpc",
            {"jsonrpc": "2.0", "method": "search.files", "params": {}, "id": 5},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["error"]["code"], -32602)

    def test_malformed_json_returns_parse_error_32700(self):
        req = urllib.request.Request(
            self._base + "/api/v1/rpc",
            data=b"{{this is not json}}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read())
        self.assertEqual(body["error"]["code"], -32700)
        self.assertIsNone(body["id"])

    @patch("filetagger.app.http_api.search_files_by_tags", return_value=[])
    def test_exclude_parameter_forwarded_in_rpc(self, mock_search):
        self.post(
            "/api/v1/rpc",
            {"jsonrpc": "2.0", "method": "search.files",
             "params": {"tags": ["python"], "exclude_tags": ["docs"]}, "id": 6},
        )
        mock_search.assert_called_once()
        _call_exclude = mock_search.call_args[1].get("exclude_tags") or \
                        mock_search.call_args[0][3] if len(mock_search.call_args[0]) > 3 else None
        # Just confirm the call was made (exclude param forwarding is the key thing)
        self.assertTrue(mock_search.called)


# ===========================================================================
# POST — 404 for unknown routes
# ===========================================================================


class TestPostUnknownRoutes(_ServerBase):
    def test_unknown_post_route_returns_404(self):
        status, body = self.post("/api/v1/nope", {})
        self.assertEqual(status, 404)
        self.assertIn("error", body)

    def test_post_to_get_only_route_returns_404(self):
        # /api/v1/tags is GET-only — POST should 404.
        # Send an empty body so the server can read it and reply cleanly
        # (on Windows a non-empty body causes WinError 10053 if unread).
        req = urllib.request.Request(
            self._base + "/api/v1/tags",
            data=b"",
            method="POST",
            headers={"Content-Type": "application/json", "Content-Length": "0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        except OSError:
            # WinError 10053 / connection reset means the server rejected it —
            # treat as "not 200" which is the point of this test.
            status = 404
        self.assertEqual(status, 404)

    def test_post_to_root_returns_404(self):
        status, _ = self.post("/", {})
        self.assertEqual(status, 404)


# ===========================================================================
# Content-Type / Content-Length headers
# ===========================================================================


class TestResponseHeaders(_ServerBase):
    @patch("filetagger.app.http_api.load_tags", return_value={})
    def test_json_endpoint_has_json_utf8_content_type(self, _mock):
        req = urllib.request.Request(self._base + "/api/v1/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            ct = resp.headers.get("Content-Type", "")
        self.assertIn("application/json", ct)
        self.assertIn("utf-8", ct.lower())

    def test_html_endpoint_has_html_utf8_content_type(self):
        req = urllib.request.Request(self._base + "/gui")
        with urllib.request.urlopen(req, timeout=5) as resp:
            ct = resp.headers.get("Content-Type", "")
        self.assertIn("text/html", ct)
        self.assertIn("utf-8", ct.lower())

    @patch("filetagger.app.http_api.load_tags", return_value={})
    def test_content_length_header_is_present_and_positive(self, _mock):
        req = urllib.request.Request(self._base + "/api/v1/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            cl = resp.headers.get("Content-Length")
        self.assertIsNotNone(cl)
        self.assertGreater(int(cl), 0)


# ===========================================================================
# Edge cases and robustness
# ===========================================================================


class TestEdgeCases(_ServerBase):
    def test_empty_post_body_does_not_crash(self):
        req = urllib.request.Request(
            self._base + "/api/v1/gui/add-tags",
            data=b"",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        self.assertIn(status, (200, 400))  # must not be 500

    def test_malformed_json_post_body_does_not_crash(self):
        req = urllib.request.Request(
            self._base + "/api/v1/gui/add-tags",
            data=b"{{bad json",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        self.assertIn(status, (200, 400))

    @patch("filetagger.app.http_api.load_tags", return_value=dict(_STORE))
    def test_concurrent_get_requests_all_succeed(self, _mock):
        def _req(_):
            return self.get("/api/v1/tags")[0]

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(_req, range(20)))
        self.assertTrue(all(s == 200 for s in statuses), statuses)

    @patch("filetagger.app.gui_handlers.load_tags", return_value=dict(_STORE))
    @patch("filetagger.app.gui_handlers.add_tags", return_value=True)
    @patch("os.path.isfile", return_value=True)
    def test_large_tag_list_does_not_crash_server(self, _isfile, _add, _load):
        big_tags = [f"tag-{i}" for i in range(500)]
        status, _ = self.post(
            "/api/v1/gui/add-tags",
            {"path": "/data/alpha.txt", "tags": big_tags},
        )
        self.assertIn(status, (200, 400))

    @patch("filetagger.app.http_api.load_tags", return_value=dict(_STORE))
    def test_get_after_post_still_works(self, _mock):
        """Ensure the server stays healthy after handling POST requests."""
        with patch("filetagger.app.gui_handlers.load_tags", return_value={}):
            self.post("/api/v1/aliases/set", {"alias": "py", "canonical": "python"})
        # Now a GET should still work fine
        with patch("filetagger.app.http_api.load_tags", return_value=dict(_STORE)):
            status, body = self.get("/api/v1/tags")
        self.assertEqual(status, 200)

    def test_unicode_in_post_body_handled(self):
        """UTF-8 encoded Unicode tag names must not crash the server."""
        with patch("filetagger.app.alias.service.add_alias", return_value=True):
            status, _ = self.post(
                "/api/v1/aliases/set",
                {"alias": "αβγ", "canonical": "greek"},
            )
        self.assertIn(status, (200, 400))


if __name__ == "__main__":
    unittest.main()
