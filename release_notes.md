# FileTagger v1.7.0

Release date: 2026-04-24

## Highlights

- **Thin browser GUI** — `ftag gui` serves a local HTML UI at `/gui` (default `127.0.0.1:8844`), same tag database as the CLI. Optional path restriction via `FILETAGGER_GUI_ROOT`. See README.
- **`ftag serve`** — Same server; discovery JSON lists `/gui` and GUI POST endpoints.
- **Windows** — `ftag windows install-context-menu --dry-run`, extra Explorer verbs (recursive dry-run add, open Command Prompt here).
- **Export** — `ftag export --relative-to` / `--strip-prefix` for portable JSON and CSV.
- **`ftag bulk retag`** — Writes a journal entry when the journal is enabled so `ftag undo` can roll back renames.
- **MCP** — `remove_path_from_tag_database` tool; project `.cursor/mcp.json` and README MCP sections (Cursor, Claude, ChatGPT, Codex).
- **`ftag watch` + `--json`** — NDJSON event stream for automation.
- **Fish completions** — `completions/ftag.fish`.
- **Recipes** — `tasks/recipes/` (CI, `uvx`, pre-commit sample).
- **High-ROI backlog** — Completed items archived under `tasks/archive/`; implemented BDD under `tasks/archive/bdd_implemented_2026-04/`; remaining backlog in `tasks/todo_bdd/README.md`.

## Install

```bash
pip install filetagger-cli==1.7.0
```

Optional extras unchanged: `[watch]`, `[mcp]`, `[test]`, `[dev]`.

## Upgrade notes

- The thin GUI binds to **loopback by default**. Do not expose on `0.0.0.0` without authentication on untrusted networks.
- PyPI package data uses quoted TOML keys for `filetagger.app` static assets (`thin_gui.html`).
