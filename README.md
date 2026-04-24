# 🏷️ TagManager

<div align="center">

**The Ultimate Command-Line File Tagging System**

_Transform chaos into order with intelligent file organization_

[![PyPI](https://img.shields.io/pypi/v/tagmanager-cli.svg)](https://pypi.org/project/tagmanager-cli/)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](README.md)
[![Tests](https://img.shields.io/badge/Tests-471%20passed-brightgreen.svg)](tests/)

[Features](#-features) • [Installation](#-installation) • [MCP clients](#mcp-cursor-claude-chatgpt-and-codex) • [Quick Start](#-quick-start) • [Commands](#-commands) • [Examples](#-examples)

</div>

---

## 🌟 Why TagManager?

Folder hierarchies force you to put a file in one place. Tags let a file belong to everything it actually is.

```bash
# One command to tag — one command to find
tm add report.pdf --tags work client-a q1 2024 final
tm search --tags work q1        # instantly surface it
```

TagManager stores tags in a lightweight JSON sidecar (`~/file_tags.json`) — no database, no daemon required — and ships a full command set for search, bulk operations, smart filtering, an interactive network graph, and a file-system watcher that tags new files automatically.

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
| **Move tracking** | `tm mv` keeps tag records in sync when you rename files |
| **Config** | Full dot-notation config system with export/import |
| **Thin GUI** | `tm gui` — local browser UI for tags + search (`/gui`, same DB as CLI) |
| **Shell completion** | Typer/bash/zsh tab-complete tags, presets, aliases; **Fish:** [completions/tm.fish](completions/tm.fish) |

---

## 🚀 Installation

```bash
pip install tagmanager-cli
```

Commands are available as both `tm` (short) and `tagmanager` (long form).

### Optional: Watch mode

Watch mode requires [watchdog](https://pypi.org/project/watchdog/):

```bash
pip install tagmanager-cli[watch]
# or separately
pip install watchdog
```

### Install from source

```bash
git clone https://github.com/davidtbilisi/TagManager.git
cd TagManager
pip install -e .
```

### Optional: MCP (AI assistants)

To expose TagManager to **Cursor**, **Claude Desktop**, **ChatGPT** (where local stdio is supported), **OpenAI Codex**, or any MCP client over stdio, install the optional SDK:

```bash
pip install "tagmanager-cli[mcp]"
# or, from a clone:
pip install -e ".[mcp]"
```

See [MCP clients](#mcp-cursor-claude-chatgpt-and-codex) for wiring it into your tools.

### Automation snippets

CI and hook examples (GitHub Actions, `uvx`, sample pre-commit): [tasks/recipes/README.md](tasks/recipes/README.md).

**PyPI releases:** a `v*` tag triggers [`.github/workflows/release.yml`](.github/workflows/release.yml) (build + publish). After bumping version and `release_notes.md`, run **`./publish.sh release`** ([`gh`](https://cli.github.com/) under the hood) — see [docs/RELEASE_CI.md](docs/RELEASE_CI.md).

---

## MCP: Cursor, Claude, ChatGPT, and Codex

TagManager ships a **Model Context Protocol** server (`tagmanager/mcp_stdio.py`) that exposes tools such as listing tags, searching files by tag, reading tags for a path, and adding tags (default **dry run**). You can run it manually as:

```bash
tm-mcp          # console script, if installed
# or
tm mcp          # same server via the main CLI
```

### Cursor

1. Install the MCP extra (see [Optional: MCP](#optional-mcp-ai-assistants)).
2. Open the **TagManager repository folder** as your workspace in Cursor (the config below relies on `${workspaceFolder}`).
3. This repo includes **`.cursor/mcp.json`**, which registers a server named **`tagmanager`** using:
   - `python -m tagmanager.mcp_stdio`
   - `PYTHONPATH=${workspaceFolder}` so a local clone works without a separate `pip install` of the package into that interpreter.
4. In Cursor, open **Settings → MCP** (or the MCP panel), then **refresh** or restart Cursor so the project server is loaded.
5. If the server fails to start, point **`command`** in `.cursor/mcp.json` at the same Python executable you used for `pip install` (on Windows you can use `py` with `args` like `["-3", "-m", "tagmanager.mcp_stdio"]`).

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
    "tagmanager": {
      "command": "python",
      "args": ["-m", "tagmanager.mcp_stdio"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/TagManager"
      }
    }
  }
}
```

If `tagmanager-cli[mcp]` is installed in that Python environment and imports resolve globally, you can omit `env` and use only `"command": "python"` and `"args": ["-m", "tagmanager.mcp_stdio"]`. Alternatively, if the `tm-mcp` script is on `PATH` for the same environment:

```json
{
  "mcpServers": {
    "tagmanager": {
      "command": "tm-mcp",
      "args": []
    }
  }
}
```

4. Save the file and start Claude Desktop again; enable the **tagmanager** MCP server in the app if prompted. Use the developer **logs** or the tools / hammer control in the chat UI to confirm the server loaded.

### ChatGPT and OpenAI

TagManager’s MCP server speaks **stdio** (a local subprocess). How that maps to ChatGPT depends on which product you use.

#### ChatGPT in the browser (Developer mode / custom apps)

ChatGPT **custom apps** (developer mode) connect to an MCP server over a **remote URL** (for example **SSE** or **streamable HTTP**), not by spawning your local `python -m tagmanager.mcp_stdio` directly. This repository does not ship an HTTP MCP bridge.

To use TagManager from **web** ChatGPT you would need a **trusted** network path from OpenAI’s infrastructure to your tools (for example a small **stdio → HTTP** gateway you control, or a hosted deployment), then register that URL under **Settings → Apps** per your workspace rules. Plan and admin requirements change over time; start from OpenAI’s docs: [Developer mode and MCP apps](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt-beta), [ChatGPT developer mode](https://developers.openai.com/api/docs/guides/developer-mode).

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
[mcp_servers.tagmanager]
command = "python"
args = ["-m", "tagmanager.mcp_stdio"]

[mcp_servers.tagmanager.env]
PYTHONPATH = "/absolute/path/to/TagManager"
```

Use the same Python you used for `pip install "tagmanager-cli[mcp]"`. Then use Codex’s MCP UI or `codex mcp` to verify the server starts.

Further reading: [Cursor MCP](https://cursor.com/docs/mcp), [Connecting local MCP servers (Claude Desktop)](https://modelcontextprotocol.io/docs/develop/connect-local-servers), [OpenAI Codex MCP](https://developers.openai.com/codex/mcp).

---

## ⚡ Quick Start

```bash
# Tag a file (auto-tags by extension too)
tm add main.py --tags backend core

# Tag everything matching a glob
tm bulk add "src/**/*.py" --tags python

# Find files
tm search --tags backend core     # either tag
tm search --tags backend --match-all core  # both tags

# Visual overview
tm ls --tree
tm tags --cloud
tm stats --chart

# Interactive network graph (opens in browser)
tm graph

# Watch a directory — auto-tag as files arrive
tm watch ~/Downloads --tags inbox

# Portable export (paths relative to project root)
tm export -o tags.json --relative-to .

# Thin browser GUI (localhost; opens browser — same tag DB as CLI)
tm gui
# tm gui --no-browser --port 8844
# Optional path jail: TAGMANAGER_GUI_ROOT=C:\your\project
```

### Thin browser GUI (`tm gui`)

- Serves a small HTML UI at **`/gui`** on the same stdlib HTTP stack as **`tm serve`** (default **`127.0.0.1:8844`** for `tm gui`). For JSON only (no `/gui`), use **`tm serve`** (default port **8765**); **`tm server`** is the same command.
- Mutations use **`add_tags`**, **`remove_path`**, **`remove_all_tags`**, and the same **`load_tags` / `save_tags`** as the CLI (see `tagmanager/app/gui_handlers.py`).
- Set **`TAGMANAGER_GUI_ROOT`** to an absolute directory to reject paths outside that tree (optional safety rail).
- Do not bind on **`0.0.0.0`** on untrusted networks; there is **no authentication**.

---

## 📖 Commands

### `tm add` — Tag files

```bash
tm add <file> --tags <tag> [<tag>...]   # basic
tm add <file> --tags python --preset webproject  # combine with preset
tm add <file> --no-auto                 # skip extension-based auto-tags
tm add <file> --no-aliases              # skip alias resolution
```

### `tm search` — Find files

```bash
tm search --tags python web            # files with EITHER tag
tm search --tags python --match-all    # files with ALL listed tags
tm search --path /projects/            # by path fragment
tm search --tags python --exact        # exact tag match (no fuzzy)
```

### `tm ls` — List tagged files

```bash
tm ls           # flat table
tm ls --tree    # directory tree with inline tags
```

### `tm tags` — Explore tags

```bash
tm tags                  # list all tags
tm tags --search py      # filter tags by name
tm tags --cloud          # frequency cloud
tm tags --where python   # which files carry this tag
```

### `tm stats` — Analytics

```bash
tm stats              # summary
tm stats --chart      # ASCII bar charts
tm stats --tag python # deep-dive on one tag (co-occurrence, file types)
```

### `tm graph` — Interactive network visualizer

Opens a self-contained HTML graph in your default browser.

```bash
tm graph                        # tag co-occurrence graph, 2D
tm graph --3d                   # start in 3D (toggle button in UI too)
tm graph --mode file            # file similarity graph (Jaccard)
tm graph --mode mixed           # bipartite file↔tag graph
tm graph --export gexf          # also export tag_network.gexf (Gephi)
tm graph --export graphml       # for Cytoscape / yEd
tm graph --min-weight 2         # only show edges with ≥2 co-occurrences
tm graph --output ~/graph.html  # save to a specific path
```

**In the browser UI:**
- Sidebar with 10 live filters (search, tag/extension multi-select, weight & degree sliders, cluster highlight, color-by)
- 2D / 3D toggle — WebGL via Three.js, handles thousands of nodes
- Click any file node → opens it in your OS file explorer
- Download GEXF / GraphML buttons (embedded, no server needed)

### `tm watch` — Auto-tag new files

Monitors a directory with [watchdog](https://pypi.org/project/watchdog/) and tags files as they arrive.

```bash
tm watch                         # watch current dir
tm watch ~/Downloads             # watch a specific dir
tm watch . --tags inbox          # always add "inbox" to every new file
tm watch . --preset webproject   # apply a saved preset
tm watch . --no-auto             # skip extension auto-tagging
tm watch . --clean-on-delete     # remove tag entry when file is deleted
tm watch . --no-recursive        # top-level only
tm watch . --ignore "*.log"      # extra ignore patterns
tm watch . --plain               # plain text output (no Rich live display)
```

Rich live display shows a colour-coded event log (`✚ created`, `→ moved`, `✖ deleted`) with resolved tags. Press **Ctrl+C** to stop.

### `tm filter` — Smart analysis

```bash
tm filter duplicates             # files with identical tag sets
tm filter orphans                # files with no tags
tm filter similar <file>         # files similar to this one (Jaccard)
tm filter clusters               # group files by shared tag
tm filter isolated               # files that share few tags with others
```

### `tm bulk` — Mass operations

```bash
tm bulk add "*.py" --tags python          # tag by glob
tm bulk remove --tag deprecated           # remove a tag from all files
tm bulk retag --from js --to javascript   # rename a tag everywhere
# All bulk commands support --dry-run
# With journal on (TAGMANAGER_JOURNAL=1 or journal.enabled), retag is undoable: tm undo
# Aliases (tm alias) normalize names at tag time; retag rewrites stored tags in the DB
```

### Aliases, Presets, Move tracking

```bash
# Aliases — normalize tag variants
tm alias add py python
tm alias list
tm alias remove py

# Presets — named tag bundles
tm preset save webproject --tags python django web
tm preset apply webproject app.py
tm preset list

# Move tracking — keep the DB in sync
tm mv old/path.py new/path.py
tm clean             # remove entries for deleted files
tm clean --dry-run   # preview
```

### Config

```bash
tm config list                         # all settings
tm config set display.emojis false
tm config set search.fuzzy_threshold 0.8
tm config export --file settings.json
tm config import team_settings.json
tm config reset                        # back to defaults
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
tagmanager/
├── cli.py                  # Typer CLI — all commands registered here
└── app/
    ├── add/                # tm add
    ├── bulk/               # tm bulk
    ├── filter/             # tm filter
    ├── search/             # tm search
    ├── stats/              # tm stats
    ├── graph/              # tm graph  (HTML generator, GEXF/GraphML export)
    ├── watch/              # tm watch  (watchdog integration)
    ├── alias/              # tm alias
    ├── preset/             # tm preset
    ├── autotag/            # extension → tag mappings
    ├── move/               # tm mv / tm clean
    ├── visualization/      # tree, cloud, ASCII charts
    ├── config/             # tm config
    └── helpers.py          # load_tags() / save_tags() — atomic JSON I/O
```

Storage: `~/file_tags.json` (path configurable). Plain JSON — easy to inspect, back up, or version-control.

---

## 🧪 Testing

```bash
pytest tests/ -v                           # full suite (406 tests)
pytest tests/ --cov=tagmanager             # with coverage
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

Bug reports and feature requests: [GitHub Issues](https://github.com/davidtbilisi/TagManager/issues)

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

**⭐ Star this repo if TagManager helps you stay organized!**

Made by [David Chincharashvili](https://github.com/DavidTbilisi) • Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://github.com/Textualize/rich)

</div>
