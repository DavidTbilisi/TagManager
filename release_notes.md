# TagManager v1.7.0

Release date: 2026-04-24

## Highlights

- **Thin browser GUI** — `tm gui` serves a local HTML UI at `/gui` (default `127.0.0.1:8844`), same tag database as the CLI. Optional path restriction via `TAGMANAGER_GUI_ROOT`. See README.
- **`tm serve`** — Same server; discovery JSON lists `/gui` and GUI POST endpoints.
- **Windows** — `tm windows install-context-menu --dry-run`, extra Explorer verbs (recursive dry-run add, open Command Prompt here).
- **Export** — `tm export --relative-to` / `--strip-prefix` for portable JSON and CSV.
- **`tm bulk retag`** — Writes a journal entry when the journal is enabled so `tm undo` can roll back renames.
- **MCP** — `remove_path_from_tag_database` tool; project `.cursor/mcp.json` and README MCP sections (Cursor, Claude, ChatGPT, Codex).
- **`tm watch` + `--json`** — NDJSON event stream for automation.
- **Fish completions** — `completions/tm.fish`.
- **Recipes** — `tasks/recipes/` (CI, `uvx`, pre-commit sample).
- **High-ROI backlog** — Completed items archived under `tasks/archive/`; BDD specs for thin GUI under `tasks/todo_bdd/`.

## Install

```bash
pip install tagmanager-cli==1.7.0
```

Optional extras unchanged: `[watch]`, `[mcp]`, `[test]`, `[dev]`.

## Upgrade notes

- The thin GUI binds to **loopback by default**. Do not expose on `0.0.0.0` without authentication on untrusted networks.
- PyPI package data uses quoted TOML keys for `tagmanager.app` static assets (`thin_gui.html`).
