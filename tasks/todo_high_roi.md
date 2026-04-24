# High-ROI backlog

Completed work through **2026-04** is archived: [`archive/todo_high_roi_completed_2026-04.md`](archive/todo_high_roi_completed_2026-04.md).

## Active

- [ ] **Large-DB performance** — Deferred until real profiling: index or lazy path materialization for search when data shows need.

## Thin GUI

- [x] **Thin browser GUI** — `tm gui` (default `127.0.0.1:8844`), `/gui` + JSON API in `http_api.py` / `gui_handlers.py` / `thin_gui.html`. BDD (archived): [`archive/bdd_implemented_2026-04/thin_gui.feature`](archive/bdd_implemented_2026-04/thin_gui.feature), [`archive/bdd_implemented_2026-04/thin_gui_nonfunctional.feature`](archive/bdd_implemented_2026-04/thin_gui_nonfunctional.feature).

## Session log (optional)

| Date | Item | Notes |
|------|------|-------|
| 2026-04-24 | Thin browser GUI | `tm gui`, `gui_handlers.py`, `thin_gui.html`, `tests/test_gui_http.py` |

## Suggested next pick

- **Large-DB** after profiling, or extend GUI (presets, journal-aware undo button).
