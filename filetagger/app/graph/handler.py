import os
import sys
import tempfile
import threading
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

import typer

from .service import build_tag_graph, build_file_graph, build_mixed_graph
from .html_generator import generate_html
from .export import to_gexf, to_graphml, save_export


def _open_path(path: str) -> None:
    """Open a file or directory in the OS default viewer."""
    if not os.path.exists(path):
        return
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        import subprocess
        subprocess.run(["open", path], check=False)
    else:
        import subprocess
        subprocess.run(["xdg-open", path], check=False)


def _make_handler(shutdown_timer_ref: list) -> type:
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)

            # Reset inactivity timer
            if shutdown_timer_ref[0] is not None:
                shutdown_timer_ref[0].cancel()

            if parsed.path == "/open":
                path = qs.get("path", [""])[0]
                if path:
                    _open_path(path)
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "null")
                self.send_header("Access-Control-Allow-Origin", "file://")
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"ok")
            elif parsed.path == "/ping":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"pong")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *args) -> None:  # suppress request logs
            pass

    return _Handler


def _start_open_server(idle_timeout: int = 1800) -> Optional[int]:
    """
    Start a localhost-only HTTP server to handle click-to-open requests.
    Binds on a random free port; runs in a daemon thread.
    Returns the chosen port number, or None on failure.
    """
    shutdown_timer_ref = [None]

    Handler = _make_handler(shutdown_timer_ref)
    try:
        server = HTTPServer(("127.0.0.1", 0), Handler)
    except OSError:
        return None

    port = server.server_address[1]

    def _shutdown():
        server.shutdown()

    def _reset_timer():
        if shutdown_timer_ref[0] is not None:
            shutdown_timer_ref[0].cancel()
        t = threading.Timer(idle_timeout, _shutdown)
        t.daemon = True
        shutdown_timer_ref[0] = t
        t.start()

    _reset_timer()

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return port


def handle_graph_command(
    mode: str = "tag",
    three_d: bool = False,
    output: Optional[str] = None,
    export_format: Optional[str] = None,
    export_path: Optional[str] = None,
    min_weight: int = 1,
    threshold: float = 0.2,
    no_open: bool = False,
    no_server: bool = False,
) -> None:
    # ── Build graph data ─────────────────────────────────────────────────────
    typer.echo(f"Building {mode} graph…")

    if mode == "tag":
        graph_data = build_tag_graph(min_weight=min_weight)
    elif mode == "file":
        typer.echo(f"  Computing file similarity (threshold={threshold})…")
        graph_data = build_file_graph(threshold=threshold)
    elif mode == "mixed":
        graph_data = build_mixed_graph(min_weight=min_weight)
    else:
        typer.echo(f"Unknown mode '{mode}'. Choose: tag, file, mixed.", err=True)
        raise typer.Exit(1)

    n_nodes = graph_data["meta"]["node_count"]
    n_edges = graph_data["meta"]["edge_count"]
    typer.echo(f"  {n_nodes} nodes, {n_edges} edges")

    if n_nodes == 0:
        typer.echo("No tagged files found. Add some tags first with: tm add <file> --tags <tag>")
        raise typer.Exit(0)

    # ── Export GEXF / GraphML ─────────────────────────────────────────────────
    if export_format:
        fmt = export_format.lower()
        if fmt == "gexf":
            content = to_gexf(graph_data)
            ext = "gexf"
        elif fmt == "graphml":
            content = to_graphml(graph_data)
            ext = "graphml"
        else:
            typer.echo(f"Unknown export format '{export_format}'. Use: gexf, graphml", err=True)
            raise typer.Exit(1)
        out = export_path or f"tag_network.{ext}"
        save_export(content, out)
        typer.echo(f"  Exported {fmt.upper()} to: {out}")

    # ── Start helper server ───────────────────────────────────────────────────
    server_port: Optional[int] = None
    if not no_server:
        server_port = _start_open_server()
        if server_port:
            typer.echo(f"  Helper server on port {server_port} (click nodes to open files)")
        else:
            typer.echo("  Warning: could not start helper server; click-to-open disabled.")

    # ── Generate HTML ─────────────────────────────────────────────────────────
    html = generate_html(
        graph_data,
        start_3d=three_d,
        server_port=server_port,
        title="Tag Network",
    )

    # ── Write to file ─────────────────────────────────────────────────────────
    if output:
        html_path = output
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
    else:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8", prefix="tm_graph_"
        )
        tmp.write(html)
        tmp.close()
        html_path = tmp.name

    # ── Open browser ──────────────────────────────────────────────────────────
    if not no_open:
        # file:// URI needs forward slashes on Windows
        uri = "file:///" + html_path.replace("\\", "/")
        webbrowser.open(uri)
        typer.echo(f"Opened graph: {html_path}")
    else:
        typer.echo(f"Graph saved to: {html_path}")
