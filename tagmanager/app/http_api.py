"""Minimal local HTTP + JSON-RPC for automation (read-heavy, bind localhost)."""

from __future__ import annotations

import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from .helpers import load_tags
from .search.service import combined_search, search_files_by_tags


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: Any) -> None:
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


class _TagManagerHandler(BaseHTTPRequestHandler):
    server_version = "TagManagerHTTP/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        # quieter default
        pass

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
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
                    "endpoints": ["GET /api/v1/tags", "GET /api/v1/search?tags=a,b&match_all=0"],
                    "rpc": "POST /api/v1/rpc  body: {jsonrpc, method, params, id}",
                },
            )
            return
        _json_response(self, 404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/v1/rpc":
            _json_response(self, 404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            req = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            _json_response(self, 400, {"jsonrpc": "2.0", "error": {"code": -32700, "message": "parse error"}, "id": None})
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
                {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"unknown method {method!r}"}, "id": req_id},
            )
            return
        _json_response(self, 200, {"jsonrpc": "2.0", "result": result, "id": req_id})


def run_server(host: str, port: int) -> None:
    httpd = ThreadingHTTPServer((host, port), _TagManagerHandler)
    print(f"TagManager HTTP listening on http://{host}:{port}/ (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
