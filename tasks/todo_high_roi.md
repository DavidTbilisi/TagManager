# High-ROI backlog

Work through in order unless dependencies say otherwise. Check off when done.

## Reliability and trust

- [x] **Atomic tag DB writes** — `save_tags` already writes to `*.tmp` then `os.replace` (`tagmanager/app/helpers.py`). Revisit only if we learn of edge cases (e.g. network FS).
- [x] **`tm doctor`** — `tm doctor` / `tm doctor --json` / `--max-paths N`. See `tagmanager/app/doctor/service.py`.
- [x] **CI coverage gate** — GitHub Actions `.github/workflows/tests.yml` runs `pytest --cov=tagmanager --cov-fail-under=57` on push/PR to `master`/`main`. Raise threshold slowly as coverage improves.

## Composability and automation

- [ ] **`--json` parity** — Add machine-readable output to remaining high-traffic commands (`remove`, `export`, `config`, `watch`, etc.) consistent with `runtime.json_mode()` / `emit_json`.
- [x] **`--json` on `tm bulk`** — `bulk add` / `bulk remove` / `bulk retag` emit structured JSON when `tm --json bulk …` (or `TM_JSON=1`).
- [ ] **Automation recipes** — Short snippets in-repo (e.g. `tasks/recipes/`): pre-commit hook, GitHub Action step, `uvx tagmanager-cli` one-liners; link from README when stable.

## Windows shell

- [ ] **Context menu extras** — Optional verbs (e.g. dry-run recursive add, open terminal here) using same launcher pattern as `win_context_menu.py`.
- [ ] **`tm windows install-context-menu --dry-run`** — Print planned `.cmd` paths and registry values without writing.

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

## Suggested next pick

- [ ] **`--json` on `remove`** (or `export`) — same pattern as `bulk`.
