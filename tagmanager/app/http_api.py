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
        if parsed.path in ("/", "/api"):
            _json_response(
                self,
                200,
                {
                    "service": "tagmanager-cli",
                    "gui": "/gui",
                    "endpoints": [
                        "GET /gui",
                        "GET /api/v1/tags",
                        "GET /api/v1/search?tags=a,b&match_all=0",
                        "GET /api/v1/gui/path-tags?path=",
                        "GET /api/v1/files/tags?path=",
                    ],
                    "rpc": "POST /api/v1/rpc  body: {jsonrpc, method, params, id}",
                    "gui_post": [
                        "POST /api/v1/gui/add-tags",
                        "POST /api/v1/gui/remove",
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
    print(f"Thin GUI: http://{host}:{port}/gui")
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
