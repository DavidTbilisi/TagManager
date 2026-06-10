"""Minimal local HTTP + JSON-RPC for automation; thin browser GUI at ``/gui``."""

from __future__ import annotations

import json
import os
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from . import gui_handlers
from .helpers import load_tags
from .search.service import combined_search, search_files_by_tags


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: Any) -> None:
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def _html_response(handler: BaseHTTPRequestHandler, status: int, body: bytes) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_gui_html() -> bytes:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thin_gui.html")
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return b"<!DOCTYPE html><html><body><p>GUI asset missing.</p></body></html>"


def _read_preview_html() -> bytes:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_page.html")
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError:
        return b"<!DOCTYPE html><html><body><p>Preview asset missing.</p></body></html>"


def _read_post_json(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    try:
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


class _TagManagerHandler(BaseHTTPRequestHandler):
    server_version = "TagManagerHTTP/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        # quieter default (no path/tag logging at INFO)
        pass

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/gui":
            _html_response(self, 200, _read_gui_html())
            return
        if parsed.path == "/preview":
            _html_response(self, 200, _read_preview_html())
            return
        if parsed.path in ("/api/v1/gui/path-tags", "/api/v1/files/tags"):
            qs = urllib.parse.parse_qs(parsed.query)
            path = (qs.get("path") or [""])[0]
            if not path.strip():
                _json_response(self, 400, {"ok": False, "error": "path required", "tags": []})
                return
            out = gui_handlers.get_path_tags(path)
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/tags":
            _json_response(self, 200, load_tags())
            return
        if parsed.path == "/api/v1/search":
            qs = urllib.parse.parse_qs(parsed.query)
            tags = (qs.get("tags") or [""])[0].split(",") if qs.get("tags") else []
            tags = [t.strip() for t in tags if t.strip()]
            match_all = (qs.get("match_all") or ["0"])[0] in ("1", "true", "yes")
            exclude = (qs.get("exclude") or [""])[0].split(",") if qs.get("exclude") else []
            exclude = [t.strip() for t in exclude if t.strip()]
            path_q = (qs.get("path") or [None])[0]
            if tags and path_q:
                res = combined_search(tags, path_q, match_all, exclude_tags=exclude or None)
            elif tags:
                res = search_files_by_tags(tags, match_all, False, exclude_tags=exclude or None)
            else:
                _json_response(self, 400, {"error": "provide tags= or path="})
                return
            _json_response(self, 200, {"files": res})
            return
        if parsed.path == "/api/v1/all-tags":
            _json_response(self, 200, gui_handlers.get_all_tags_with_counts())
            return
        if parsed.path == "/api/v1/stats":
            _json_response(self, 200, gui_handlers.get_stats())
            return
        if parsed.path == "/api/v1/aliases":
            _json_response(self, 200, gui_handlers.get_aliases_handler())
            return
        if parsed.path == "/api/v1/presets":
            _json_response(self, 200, gui_handlers.get_presets_handler())
            return
        if parsed.path.startswith("/api/v1/stats/tag/"):
            tag = urllib.parse.unquote(parsed.path[len("/api/v1/stats/tag/"):])
            out = gui_handlers.get_tag_stats_handler(tag)
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/filter/duplicates":
            _json_response(self, 200, gui_handlers.filter_duplicates_handler())
            return
        if parsed.path == "/api/v1/filter/orphans":
            _json_response(self, 200, gui_handlers.filter_orphans_handler())
            return
        if parsed.path == "/api/v1/filter/clusters":
            qs = urllib.parse.parse_qs(parsed.query)
            ms = (qs.get("min_size") or ["2"])[0]
            _json_response(self, 200, gui_handlers.filter_clusters_handler(ms))
            return
        if parsed.path == "/api/v1/filter/isolated":
            qs = urllib.parse.parse_qs(parsed.query)
            mx = (qs.get("max_shared") or ["1"])[0]
            _json_response(self, 200, gui_handlers.filter_isolated_handler(mx))
            return
        if parsed.path in ("/", "/api"):
            _json_response(
                self,
                200,
                {
                    "service": "tagmanager-cli",
                    "gui": "/gui",
                    "preview": "/preview",
                    "endpoints": [
                        "GET /gui",
                        "GET /preview",
                        "GET /api/v1/tags",
                        "GET /api/v1/all-tags",
                        "GET /api/v1/stats",
                        "GET /api/v1/stats/tag/<name>",
                        "GET /api/v1/aliases",
                        "GET /api/v1/presets",
                        "GET /api/v1/filter/duplicates",
                        "GET /api/v1/filter/orphans",
                        "GET /api/v1/filter/clusters?min_size=N",
                        "GET /api/v1/filter/isolated?max_shared=N",
                        "GET /api/v1/search?tags=a,b&match_all=0&exclude=c&path=",
                        "GET /api/v1/gui/path-tags?path=",
                        "GET /api/v1/files/tags?path=",
                    ],
                    "rpc": "POST /api/v1/rpc  body: {jsonrpc, method, params, id}",
                    "gui_post": [
                        "POST /api/v1/gui/add-tags",
                        "POST /api/v1/gui/remove",
                        "POST /api/v1/aliases/set     {alias, canonical}",
                        "POST /api/v1/aliases/delete  {alias}",
                        "POST /api/v1/presets/set     {name, tags}",
                        "POST /api/v1/presets/delete  {name}",
                        "POST /api/v1/bulk/preview    {pattern, tags, base_path}",
                        "POST /api/v1/bulk/add        {pattern, tags, base_path}",
                        "POST /api/v1/open            {path, mode: 'file'|'folder'}",
                        "POST /api/v1/clean           {dry_run: bool}",
                    ],
                },
            )
            return
        _json_response(self, 404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/v1/gui/add-tags":
            body = _read_post_json(self)
            path = str(body.get("path") or "")
            tags = body.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            out = gui_handlers.post_add_tags(
                path,
                [str(t) for t in tags],
                dry_run=bool(body.get("dry_run")),
                no_auto=bool(body.get("no_auto")),
                no_aliases=bool(body.get("no_aliases")),
                no_content=bool(body.get("no_content")),
            )
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/gui/remove":
            body = _read_post_json(self)
            out = gui_handlers.post_remove(
                str(body.get("path") or ""),
                str(body.get("mode") or "path"),
                tag=body.get("tag"),
                dry_run=bool(body.get("dry_run")),
            )
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/gui/relocate":
            body = _read_post_json(self)
            out = gui_handlers.relocate_path_handler(
                str(body.get("old_path") or ""),
                str(body.get("new_path") or ""),
            )
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/aliases/set":
            body = _read_post_json(self)
            out = gui_handlers.set_alias_handler(
                str(body.get("alias") or ""),
                str(body.get("canonical") or ""),
            )
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/aliases/delete":
            body = _read_post_json(self)
            out = gui_handlers.delete_alias_handler(str(body.get("alias") or ""))
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/presets/set":
            body = _read_post_json(self)
            tags = body.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            out = gui_handlers.set_preset_handler(
                str(body.get("name") or ""), [str(t) for t in tags],
            )
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/presets/delete":
            body = _read_post_json(self)
            out = gui_handlers.delete_preset_handler(str(body.get("name") or ""))
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/bulk/preview":
            body = _read_post_json(self)
            tags = body.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            out = gui_handlers.bulk_preview_handler(
                str(body.get("pattern") or ""), [str(t) for t in tags],
                str(body.get("base_path") or "."),
            )
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/bulk/add":
            body = _read_post_json(self)
            tags = body.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            out = gui_handlers.bulk_apply_handler(
                str(body.get("pattern") or ""), [str(t) for t in tags],
                str(body.get("base_path") or "."),
            )
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/open":
            body = _read_post_json(self)
            out = gui_handlers.open_path_handler(
                str(body.get("path") or ""),
                str(body.get("mode") or "file"),
            )
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path == "/api/v1/clean":
            body = _read_post_json(self)
            out = gui_handlers.clean_handler(dry_run=bool(body.get("dry_run", True)))
            _json_response(self, 200 if out.get("ok") else 400, out)
            return
        if parsed.path != "/api/v1/rpc":
            _json_response(self, 404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            req = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            _json_response(
                self,
                400,
                {"jsonrpc": "2.0", "error": {"code": -32700, "message": "parse error"}, "id": None},
            )
            return
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}
        if method == "tags.list":
            result = load_tags()
        elif method == "search.files":
            tags = params.get("tags") or []
            if not isinstance(tags, list):
                tags = []
            match_all = bool(params.get("match_all", False))
            exclude = params.get("exclude_tags") or params.get("exclude")
            if exclude and not isinstance(exclude, list):
                exclude = [str(exclude)]
            path_q = params.get("path")
            if tags and path_q:
                result = combined_search(tags, path_q, match_all, exclude_tags=exclude)
            elif tags:
                result = search_files_by_tags(tags, match_all, False, exclude_tags=exclude)
            else:
                _json_response(
                    self,
                    200,
                    {"jsonrpc": "2.0", "error": {"code": -32602, "message": "tags required"}, "id": req_id},
                )
                return
        else:
            _json_response(
                self,
                200,
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"unknown method {method!r}"},
                    "id": req_id,
                },
            )
            return
        _json_response(self, 200, {"jsonrpc": "2.0", "result": result, "id": req_id})


def run_server(host: str, port: int) -> None:
    httpd = ThreadingHTTPServer((host, port), _TagManagerHandler)
    print(f"TagManager HTTP listening on http://{host}:{port}/ (Ctrl+C to stop)")
    print(f"Thin GUI: http://{host}:{port}/gui  |  Preview: http://{host}:{port}/preview")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def run_gui_server(host: str, port: int, open_browser: bool = True) -> None:
    """Serve HTTP + open ``/gui`` in the default browser unless ``open_browser`` is False."""
    if open_browser:

        def _open() -> None:
            import webbrowser

            webbrowser.open(f"http://{host}:{port}/gui")

        threading.Timer(0.35, _open).start()
    if host not in ("127.0.0.1", "localhost", "::1"):
        print(
            "Warning: binding outside loopback exposes the GUI on your network; "
            "there is no authentication.",
            flush=True,
        )
    run_server(host, port)
