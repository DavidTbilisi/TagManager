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

- [ ] **Context menu extras** — Optional verbs (e.g. dry-run recursive add, open terminal here) using same launcher pattern as `win_context_menu.py`.
- [x] **`tm windows install-context-menu --dry-run`** — `format_install_plan()` + `install_context_menu(dry_run=…)`; works on any OS to preview HKCU layout.

## Data and power users

- [ ] **Global tag rename** — Rename a tag string across all paths in the DB (with journal inverse if journal on); clarify interaction with `alias`.
- [ ] **Export relative paths** — Option to export paths relative to a given root (or strip a prefix) for portable CSV/JSON.

## MCP / HTTP

- [ ] **More MCP tools** — e.g. `remove_path`, richer `search`, `undo` when journal enabled; align shapes with HTTP RPC where sensible.

## Optional / lower priority

- [ ] **Shell completion** — Fish (and zsh if gaps) parity with existing completion.
- [ ] **Large-DB performance** — Only if real profiles show need: index or lazy paths for search.

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

## Suggested next pick

- [ ] **Context menu extras** (optional Explorer verbs).
