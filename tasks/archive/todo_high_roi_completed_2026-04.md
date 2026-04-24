# High-ROI backlog (archived snapshot — completed through 2026-04)

This file is a frozen copy of `tasks/todo_high_roi.md` when the bulk of items were done. The live backlog is `../todo_high_roi.md`.

---

# High-ROI backlog

Work through in order unless dependencies say otherwise. Check off when done.

## Reliability and trust

- [x] **Atomic tag DB writes** — `save_tags` already writes to `*.tmp` then `os.replace` (`tagmanager/app/helpers.py`). Revisit only if we learn of edge cases (e.g. network FS).
- [x] **`tm doctor`** — `tm doctor` / `tm doctor --json` / `--max-paths N`. See `tagmanager/app/doctor/service.py`.
- [x] **CI coverage gate** — GitHub Actions `.github/workflows/tests.yml` runs `pytest --cov=tagmanager --cov-fail-under=57` on push/PR to `master`/`main`. Raise threshold slowly as coverage improves.

## Composability and automation

- [x] **`--json` parity** — `watch` emits NDJSON (`watch_started`, per-file `watch_file`, `watch_stopped`). Other commands covered earlier.
- [x] **`--json` on `tm export`** — Emits full result dict (`success`, `path`, `file_count`, `message`).
- [x] **`--json` on `tm bulk`** — `bulk add` / `bulk remove` / `bulk retag` emit structured JSON when `tm --json bulk …` (or `TM_JSON=1`).
- [x] **`--json` on `tm remove`** — `remove_path` / `remove_invalid_paths` return dicts; `tm --json remove …` emits JSON; exit code 1 when remove-by-path fails.
- [x] **`--json` on `tm config`** — `tagmanager/app/config/handler.py` + `tests/test_cli_config_json.py`.
- [x] **`--json` on `tm watch`** — `tagmanager/app/watch/handler.py` + `tests/test_cli_watch_json.py`.
- [x] **Automation recipes** — `tasks/recipes/` (pre-commit sample, GitHub Actions example, `uvx`); linked from README.

## Windows shell

- [x] **Context menu extras** — Recursive dry-run + “Open Command Prompt here” verbs on directories (`win_context_menu.py`).
- [x] **`tm windows install-context-menu --dry-run`** — `format_install_plan()` + `install_context_menu(dry_run=…)`; works on any OS to preview HKCU layout.

## Data and power users

- [x] **Global tag rename** — `tm bulk retag --from … --to …`; journal entry `bulk_retag` when `journal.enabled` / `TAGMANAGER_JOURNAL=1` (undo via `tm undo`). README clarifies vs `tm alias`.
- [x] **Export relative paths** — `tm export --relative-to DIR` / `--strip-prefix PATH` (`exportdata/service.py`).

## MCP / HTTP

- [x] **More MCP tools** — `remove_path_from_tag_database` in `mcp_stdio.py`; richer search / `undo` via MCP deferred (use CLI `tm undo`).

## Optional / lower priority

- [x] **Shell completion** — Fish: `completions/tm.fish` + README / recipes link. Typer still provides bash/zsh install.
- [ ] **Large-DB performance** — Deferred until real profiling: possible index or lazy path materialization for search.

---

## Session log (optional)

| Date | Item | Notes |
|------|------|-------|
| 2026-04-21 | `tm doctor` | `run_doctor()`, tests in `tests/test_doctor_service.py` |
| 2026-04-21 | CI coverage gate | `.github/workflows/tests.yml`, `--cov-fail-under=57` |
| 2026-04-21 | `--json` on `tm bulk` | `handler._emit_bulk_result` + tests |
| 2026-04-21 | `--json` on `tm remove` | `remove/service.py` dict returns, `cli.remove`, `tests/test_cli_remove_json.py` |
| 2026-04-21 | `--json` on `tm export` | `cli.export_data`, `tests/test_cli_export_json.py` |
| 2026-04-21 | `--json` on `tm config` | `config/handler.py`, `tests/test_cli_config_json.py` |
| 2026-04-21 | `--json` on `tm watch` | `watch/handler.py` NDJSON stream, `tests/test_cli_watch_json.py` |
| 2026-04-21 | Automation recipes | `tasks/recipes/`, README link |
| 2026-04-21 | `install-context-menu --dry-run` | `win_context_menu.format_install_plan`, CLI flag |
| 2026-04-21 | Context menu extras | dry-run recursive add, open cmd here |
| 2026-04-24 | Export relative paths | `--relative-to`, `--strip-prefix`, `tests/test_exportdata_service.py` |
| 2026-04-24 | `bulk_retag` + journal | `append_entry("bulk_retag", …)` for `tm undo` |
| 2026-04-24 | MCP remove path tool | `remove_path_from_tag_database` |
| 2026-04-24 | Fish completions | `completions/tm.fish` |

## Suggested next pick

- [ ] **Large-DB performance** (after profiling) or **HTTP/MCP parity** for `undo` / advanced search.
