# High-ROI backlog

Work through in order unless dependencies say otherwise. Check off when done.

## Reliability and trust

- [x] **Atomic tag DB writes** — `save_tags` already writes to `*.tmp` then `os.replace` (`tagmanager/app/helpers.py`). Revisit only if we learn of edge cases (e.g. network FS).
- [x] **`tm doctor`** — `tm doctor` / `tm doctor --json` / `--max-paths N`. See `tagmanager/app/doctor/service.py`.
- [ ] **CI coverage gate** — `pytest` + `pytest-cov` with `--cov-fail-under` (start near current %, raise slowly).

## Composability and automation

- [ ] **`--json` parity** — Add machine-readable output to remaining high-traffic commands (`bulk`, `remove`, `export`, `config`, `watch`, etc.) consistent with `runtime.json_mode()` / `emit_json`.
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
