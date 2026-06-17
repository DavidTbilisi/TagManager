# 🏷️ FileTagger

<div align="center">

**The Ultimate Command-Line File Tagging System**

_Transform chaos into order with intelligent file organization_

[![PyPI](https://img.shields.io/pypi/v/filetagger-cli.svg)](https://pypi.org/project/filetagger-cli/)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](README.md)
[![Tests](https://img.shields.io/badge/Tests-473%20passed-brightgreen.svg)](tests/)

[Features](#-features) • [Installation](#-installation) • [MCP clients](#mcp-cursor-claude-chatgpt-and-codex) • [Quick Start](#-quick-start) • [Commands](#-commands) • [Examples](#-examples)

</div>

---

## 🌟 Why FileTagger?

Folder hierarchies force you to put a file in one place. Tags let a file belong to everything it actually is.

```bash
# One command to tag — one command to find
ftag add report.pdf --tags work client-a q1 2024 final
ftag search --tags work q1        # instantly surface it
```

FileTagger stores tags in a lightweight JSON sidecar (`~/file_tags.json`) — no database, no daemon required — and ships a full command set for search, bulk operations, smart filtering, an interactive network graph, and a file-system watcher that tags new files automatically.

---

## ✨ Features

| Category | What you get |
|---|---|
| **Core** | Add/remove/search tags, fuzzy path search, list & tree views |
| **Bulk** | Mass-tag with glob patterns, retag, bulk-remove — all with `--dry-run` |
| **Auto-tag** | Extension-based tag suggestions (60+ file types built-in) |
| **Aliases** | Normalize tag variants: `py → python`, `js → javascript` |
| **Presets** | Save named tag bundles and apply them in one flag |
| **Filters** | Duplicate sets, orphans, similarity (Jaccard), clusters, isolated files |
| **Stats** | Tag frequency, co-occurrence, ASCII bar charts & histograms |
| **Visualizer** | Interactive 2D/3D network graph in your browser — click to open files |
| **Watch mode** | Auto-tag files the moment they land in a directory |
| **Move tracking** | `ftag mv` keeps tag records in sync when you rename files |
| **Config** | Full dot-notation config system with export/import |
| **Thin GUI** | `ftag gui` — local browser UI for tags + search (`/gui`); dry-run **preview** page at `/preview` |
| **Shell completion** | Typer/bash/zsh tab-complete tags, presets, aliases; **Fish:** [completions/ftag.fish](completions/ftag.fish) |

---

## 🚀 Installation

```bash
pip install filetagger-cli
```

Commands are available as both `ftag` (short) and `filetagger` (long form).

### Optional: Watch mode

Watch mode requires [watchdog](https://pypi.org/project/watchdog/):

```bash
pip install filetagger-cli[watch]
# or separately
pip install watchdog
```

### Install from source

```bash
git clone https://github.com/davidtbilisi/FileTagger.git
cd FileTagger
pip install -e .
```

### Optional: MCP (AI assistants)

To expose FileTagger to **Cursor**, **Claude Desktop**, **ChatGPT** (where local stdio is supported), **OpenAI Codex**, or any MCP client over stdio, install the optional SDK:

```bash
pip install "filetagger-cli[mcp]"
# or, from a clone:
pip install -e ".[mcp]"
```

See [MCP clients](#mcp-cursor-claude-chatgpt-and-codex) for wiring it into your tools.

### Automation snippets

CI and hook examples (GitHub Actions, `uvx`, sample pre-commit): [tasks/recipes/README.md](tasks/recipes/README.md).

**PyPI releases:** a `v*` tag triggers [`.github/workflows/release.yml`](.github/workflows/release.yml) (build + publish). After bumping version and `release_notes.md`, run **`./publish.sh release`** ([`gh`](https://cli.github.com/) under the hood) — see [docs/RELEASE_CI.md](docs/RELEASE_CI.md).

---

## MCP: Cursor, Claude, ChatGPT, and Codex

FileTagger ships a **Model Context Protocol** server (`filetagger/mcp_stdio.py`) that exposes tools such as listing tags, searching files by tag, reading tags for a path, and adding tags (default **dry run**). You can run it manually as:

```bash
ftag-mcp          # console script, if installed
# or
ftag mcp          # same server via the main CLI
```

### Cursor

1. Install the MCP extra (see [Optional: MCP](#optional-mcp-ai-assistants)).
2. Open the **FileTagger repository folder** as your workspace in Cursor (the config below relies on `${workspaceFolder}`).
3. This repo includes **`.cursor/mcp.json`**, which registers a server named **`filetagger`** using:
   - `python -m filetagger.mcp_stdio`
   - `PYTHONPATH=${workspaceFolder}` so a local clone works without a separate `pip install` of the package into that interpreter.
4. In Cursor, open **Settings → MCP** (or the MCP panel), then **refresh** or restart Cursor so the project server is loaded.
5. If the server fails to start, point **`command`** in `.cursor/mcp.json` at the same Python executable you used for `pip install` (on Windows you can use `py` with `args` like `["-3", "-m", "filetagger.mcp_stdio"]`).

### Claude Desktop

Claude Desktop reads **its own** MCP config file (not `.cursor/mcp.json`). In the app, use **Settings → Developer → Edit Config** to open it (or edit the path below manually).

| OS | File |
|----|------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

1. Install the MCP extra in the Python environment you will reference below.
2. Quit Claude Desktop before editing the file.
3. Add or merge a `mcpServers` entry. **Example** when you develop from a clone (replace the path with your real repo directory):

```json
{
  "mcpServers": {
    "filetagger": {
      "command": "python",
      "args": ["-m", "filetagger.mcp_stdio"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/FileTagger"
      }
    }
  }
}
```

If `filetagger-cli[mcp]` is installed in that Python environment and imports resolve globally, you can omit `env` and use only `"command": "python"` and `"args": ["-m", "filetagger.mcp_stdio"]`. Alternatively, if the `ftag-mcp` script is on `PATH` for the same environment:

```json
{
  "mcpServers": {
    "filetagger": {
      "command": "ftag-mcp",
      "args": []
    }
  }
}
```

4. Save the file and start Claude Desktop again; enable the **filetagger** MCP server in the app if prompted. Use the developer **logs** or the tools / hammer control in the chat UI to confirm the server loaded.

### ChatGPT and OpenAI

FileTagger’s MCP server speaks **stdio** (a local subprocess). How that maps to ChatGPT depends on which product you use.

#### ChatGPT in the browser (Developer mode / custom apps)

ChatGPT **custom apps** (developer mode) connect to an MCP server over a **remote URL** (for example **SSE** or **streamable HTTP**), not by spawning your local `python -m filetagger.mcp_stdio` directly. This repository does not ship an HTTP MCP bridge.

To use FileTagger from **web** ChatGPT you would need a **trusted** network path from OpenAI’s infrastructure to your tools (for example a small **stdio → HTTP** gateway you control, or a hosted deployment), then register that URL under **Settings → Apps** per your workspace rules. Plan and admin requirements change over time; start from OpenAI’s docs: [Developer mode and MCP apps](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt-beta), [ChatGPT developer mode](https://developers.openai.com/api/docs/guides/developer-mode).

#### ChatGPT Desktop (local JSON, when available)

Some **ChatGPT Desktop** builds load MCP servers from a JSON file on disk, similar to Claude Desktop. Community-reported locations (confirm in your app version under **Settings** / developer options):

| OS | File (may vary by release) |
|----|------|
| **macOS** | `~/Library/Application Support/ChatGPT/chatgpt_mcp_config.json` |
| **Windows** | `%APPDATA%\OpenAI\ChatGPT\chatgpt_mcp_config.json` |

If that file exists and expects the same `mcpServers` shape as Claude, reuse the **JSON example** from the [Claude Desktop](#claude-desktop) section (same `command` / `args` / `env` as there). Fully quit and restart the desktop app after edits.

#### OpenAI Codex (local stdio)

[OpenAI Codex](https://developers.openai.com/codex/mcp) documents **stdio** MCP servers in `~/.codex/config.toml` (or a trusted project’s `.codex/config.toml`). Example for a local clone:

```toml
[mcp_servers.filetagger]
command = "python"
args = ["-m", "filetagger.mcp_stdio"]

[mcp_servers.filetagger.env]
PYTHONPATH = "/absolute/path/to/FileTagger"
```

Use the same Python you used for `pip install "filetagger-cli[mcp]"`. Then use Codex’s MCP UI or `codex mcp` to verify the server starts.

Further reading: [Cursor MCP](https://cursor.com/docs/mcp), [Connecting local MCP servers (Claude Desktop)](https://modelcontextprotocol.io/docs/develop/connect-local-servers), [OpenAI Codex MCP](https://developers.openai.com/codex/mcp).

---

## ⚡ Quick Start

```bash
# Tag a file (auto-tags by extension too)
ftag add main.py --tags backend core

# Tag everything matching a glob
ftag bulk add "src/**/*.py" --tags python

# Find files
ftag search --tags backend core     # either tag
ftag search --tags backend --match-all core  # both tags

# Visual overview
ftag ls --tree
ftag tags --cloud
ftag stats --chart

# Interactive network graph (opens in browser)
ftag graph

# Watch a directory — auto-tag as files arrive
ftag watch ~/Downloads --tags inbox

# Portable export (paths relative to project root)
ftag export -o tags.json --relative-to .

# Thin browser GUI (localhost; opens browser — same tag DB as CLI)
ftag gui
# ftag gui --no-browser --port 8844
# Optional path jail: FILETAGGER_GUI_ROOT=C:\your\project
```

### Thin browser GUI (`ftag gui`)

The web UI is a **single page** served over HTTP on your machine. It uses the **same tag file** as `ftag add`, `ftag search`, etc.—nothing is stored in the cloud.

#### Start and stop

1. Run **`ftag gui`** in a terminal. By default the server listens on **`127.0.0.1:8844`**, your browser opens to **`http://127.0.0.1:8844/gui`**, and the UI loads.
2. **Stop** the server with **Ctrl+C** in that terminal (the process exits; refresh the tab afterward and it will fail to connect—that is expected).
3. **Without auto-opening a browser:** `ftag gui --no-browser` (same host/port; open `/gui` yourself).
4. **Custom bind or port:** `ftag gui --host 127.0.0.1 --port 8844` (defaults are loopback + **8844**).

#### Preview page (`/preview`)

A second page on the **same server**: **`http://127.0.0.1:8844/preview`** (adjust host/port if you changed them). Nothing on `/preview` writes the database by itself—it always calls the API with **`dry_run: true`**.

- **Saved tag database** — on load (and **Refresh from server**), fetches **`GET /api/v1/tags`**: a **sortable table** of every saved path and its tags, plus a chip list of **all distinct tag names**, with a client-side **filter** (matches path or tag text).
- **Preview add tags** — enter a file path, optional tags to add, and the same **no auto-tag / no aliases / no content** toggles as `/gui`. **Preview merge** shows **before** and **after** tag sets (after includes extension auto-tags and alias resolution when those options are off).
- **Preview remove / clear / drop** — pick a mode and (for “one tag”) a tag name; the server returns a JSON payload describing what would happen.

The main **`/gui`** page links here; the terminal banner also prints the preview URL when the server starts.

**JSON-only HTTP** (no HTML page): **`ftag serve`** or **`ftag server`** on port **8765** by default—the same API routes work (`/api/v1/...`). Use that when you only need scripts or `curl`, not the browser form.

#### Page layout: “File” and “Search”

**File** — one path at a time (a file path your OS can resolve):

| Control | What it does |
|--------|----------------|
| **Path** | Absolute or relative path to the file. After **Load tags**, the server may echo back a **normalized absolute path**. |
| **Dry-run** | When checked, **Add tags** and remove actions **do not write** the database; you get a preview-style success message. Uncheck to apply changes. |
| **Load tags** | `GET` current tags for that path (same data as `ftag path` for that file). |
| **Tags to add** | Comma-separated list, same idea as `ftag add … --tags a,b`. Then **Add tags**. |
| **No auto-tag / No aliases / No content rules** | Match `ftag add`’s `--no-auto`, `--no-aliases`, and skipping content-based rules—useful when you want **only** the tags you typed. |
| **Remove one tag…** | Prompts for a tag name; removes that tag from the file (like removing one chip). |
| **Clear all tags on file** | Empties the tag list but **keeps** the path in the database (`ftag remove --path … --all-tags`). Confirms before running. |
| **Remove file from DB** | Drops the path entirely from the tag store (`ftag remove --path …` without `--all-tags`). Confirms before running—this is stronger than “clear tags”. |

**Search** — same tag logic as the CLI for a multi-tag query:

| Control | What it does |
|--------|----------------|
| **Tags** | Comma-separated tag names to search for. |
| **Match all (AND)** | Checked: file must have **every** listed tag. Unchecked: file needs **any** listed tag (**OR**), same spirit as `ftag search` without `--match-all`. |
| **Search** | Lists matching file paths below the button (paths may be truncated per your `ftag ls` / list display config). |

Status text (green/red) under the form shows the last result or error. If **`FILETAGGER_GUI_ROOT`** is set to an absolute directory, paths **outside** that tree are rejected for GUI operations (safety rail for shared machines).

#### Security (read this once)

- Default binding is **loopback only**. There is **no login**; anyone who can open the URL on your machine can use the UI if they reach the port.
- **Do not** use `--host 0.0.0.0` on untrusted networks unless you understand you are exposing the API.

#### Implementation note

Mutations go through **`filetagger/app/gui_handlers.py`** (same **`load_tags` / `save_tags`** stack as the CLI). HTML assets: **`filetagger/app/thin_gui.html`**, **`filetagger/app/preview_page.html`**. REST-style discovery: open **`http://127.0.0.1:8844/`** or **`…/api`** while the server is running for a short JSON list of routes (includes **`GET /preview`**, **`GET /api/v1/files/tags?path=`** for scripts).

---

## 📖 Commands

### `ftag add` — Tag files

```bash
ftag add <file> --tags <tag> [<tag>...]   # basic
ftag add <file> --tags python --preset webproject  # combine with preset
ftag add <file> --no-auto                 # skip extension-based auto-tags
ftag add <file> --no-aliases              # skip alias resolution
```

### `ftag search` — Find files

```bash
ftag search --tags python web            # files with EITHER tag
ftag search --tags python --match-all    # files with ALL listed tags
ftag search --path /projects/            # by path fragment
ftag search --tags python --exact        # exact tag match (no fuzzy)
```

### `ftag ls` — List tagged files

```bash
ftag ls           # flat table
ftag ls --tree    # directory tree with inline tags
```

### `ftag tags` — Explore tags

```bash
ftag tags                  # list all tags
ftag tags --search py      # filter tags by name
ftag tags --cloud          # frequency cloud
ftag tags --where python   # which files carry this tag
```

### `ftag stats` — Analytics

```bash
ftag stats              # summary
ftag stats --chart      # ASCII bar charts
ftag stats --tag python # deep-dive on one tag (co-occurrence, file types)
```

### `ftag graph` — Interactive network visualizer

Opens a self-contained HTML graph in your default browser.

```bash
ftag graph                        # tag co-occurrence graph, 2D
ftag graph --3d                   # start in 3D (toggle button in UI too)
ftag graph --mode file            # file similarity graph (Jaccard)
ftag graph --mode mixed           # bipartite file↔tag graph
ftag graph --export gexf          # also export tag_network.gexf (Gephi)
ftag graph --export graphml       # for Cytoscape / yEd
ftag graph --min-weight 2         # only show edges with ≥2 co-occurrences
ftag graph --output ~/graph.html  # save to a specific path
```

**In the browser UI:**
- Sidebar with 10 live filters (search, tag/extension multi-select, weight & degree sliders, cluster highlight, color-by)
- 2D / 3D toggle — WebGL via Three.js, handles thousands of nodes
- Click any file node → opens it in your OS file explorer
- Download GEXF / GraphML buttons (embedded, no server needed)

### `ftag watch` — Auto-tag new files

Monitors a directory with [watchdog](https://pypi.org/project/watchdog/) and tags files as they arrive.

```bash
ftag watch                         # watch current dir
ftag watch ~/Downloads             # watch a specific dir
ftag watch . --tags inbox          # always add "inbox" to every new file
ftag watch . --preset webproject   # apply a saved preset
ftag watch . --no-auto             # skip extension auto-tagging
ftag watch . --clean-on-delete     # remove tag entry when file is deleted
ftag watch . --no-recursive        # top-level only
ftag watch . --ignore "*.log"      # extra ignore patterns
ftag watch . --plain               # plain text output (no Rich live display)
```

Rich live display shows a colour-coded event log (`✚ created`, `→ moved`, `✖ deleted`) with resolved tags. Press **Ctrl+C** to stop.

### `ftag filter` — Smart analysis

```bash
ftag filter duplicates             # files with identical tag sets
ftag filter orphans                # files with no tags
ftag filter similar <file>         # files similar to this one (Jaccard)
ftag filter clusters               # group files by shared tag
ftag filter isolated               # files that share few tags with others
```

### `ftag bulk` — Mass operations

```bash
ftag bulk add "*.py" --tags python          # tag by glob
ftag bulk remove --tag deprecated           # remove a tag from all files
ftag bulk retag --from js --to javascript   # rename a tag everywhere
# All bulk commands support --dry-run
# With journal on (FILETAGGER_JOURNAL=1 or journal.enabled), retag is undoable: ftag undo
# Aliases (ftag alias) normalize names at tag time; retag rewrites stored tags in the DB
```

### Aliases, Presets, Move tracking

```bash
# Aliases — normalize tag variants
ftag alias add py python
ftag alias list
ftag alias remove py

# Presets — named tag bundles
ftag preset save webproject --tags python django web
ftag preset apply webproject app.py
ftag preset list

# Move tracking — keep the DB in sync
ftag mv old/path.py new/path.py
ftag clean             # remove entries for deleted files
ftag clean --dry-run   # preview
```

### Config

```bash
ftag config list                         # all settings
ftag config set display.emojis false
ftag config set search.fuzzy_threshold 0.8
ftag config export --file settings.json
ftag config import team_settings.json
ftag config reset                        # back to defaults
```

---

## 🎨 Examples

### Network graph

```
Tag co-occurrence network — 42 nodes, 180 edges
Sidebar filters: search · tag multiselect · min-weight slider · degree range
                 color-by cluster · highlight cluster · show/hide node types
2D ↔ 3D toggle  |  Download GEXF  |  Download GraphML
Click file node → opens in Finder/Explorer
```

### Watch mode output

```
Watching: /home/user/Downloads
  Recursive: True | Auto-tag: True | Clean-on-delete: False
  Always add tags: ['inbox']
Press Ctrl+C to stop.

[14:02:11] ✚ created ✓  report_q1.pdf  [inbox, pdf, document]
[14:02:45] ✚ created ✓  script.py      [inbox, python]
[14:03:10] → moved   ✓  script.py  →  processed/script.py
```

### Tag cloud

```
☁️  Tag Cloud
★ python(15)  ◆ web(8)  ● documentation(5)  • config(3)  · backup(1)
```

### Tree view

```
└── 📁 projects/
    ├── 📁 backend/
    │   └── 📄 api.py 🏷️  [python, web, api, core]
    └── 📁 docs/
        └── 📄 README.md 🏷️  [docs, markdown]
```

---

## 🏗️ Architecture

```
filetagger/
├── cli.py                  # Typer CLI — all commands registered here
└── app/
    ├── add/                # ftag add
    ├── bulk/               # ftag bulk
    ├── filter/             # ftag filter
    ├── search/             # ftag search
    ├── stats/              # ftag stats
    ├── graph/              # ftag graph  (HTML generator, GEXF/GraphML export)
    ├── watch/              # ftag watch  (watchdog integration)
    ├── alias/              # ftag alias
    ├── preset/             # ftag preset
    ├── autotag/            # extension → tag mappings
    ├── move/               # ftag mv / ftag clean
    ├── visualization/      # tree, cloud, ASCII charts
    ├── config/             # ftag config
    └── helpers.py          # load_tags() / save_tags() — atomic JSON I/O
```

Storage: `~/file_tags.json` (path configurable). Plain JSON — easy to inspect, back up, or version-control.

---

## 🧪 Testing

```bash
pytest tests/ -v                           # full suite (406 tests)
pytest tests/ --cov=filetagger             # with coverage
pytest tests/test_graph_service.py -v      # graph module only
pytest tests/test_watch_service.py -v      # watch module only
```

406 tests across 21 test files. Watch mode integration tests require `pip install watchdog`.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Add tests
4. Open a PR

Bug reports and feature requests: [GitHub Issues](https://github.com/davidtbilisi/FileTagger/issues)

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**⭐ Star this repo if FileTagger helps you stay organized!**

Made by [David Chincharashvili](https://github.com/DavidTbilisi) • Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich)

</div>
