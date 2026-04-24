# BDD backlog (not yet fully covered)

Feature files here are **aspirational or partial** — behaviour not fully implemented or not exhaustively specified in tests.

**Implemented specs** (frozen copies) live under [`../archive/bdd_implemented_2026-04/`](../archive/bdd_implemented_2026-04/).

## Remaining files

| File | Gap (short) |
|------|----------------|
| `composability_unix_philosophy.feature` | Stdin-driven pipelines for arbitrary commands; deterministic ordering guarantees. |
| `dry_run_undo.feature` | Dry-run + undo for every destructive command; unified operation journal UX. |
| `error_handling_and_logging.feature` | Structured per-file batch logs + `tm`-level operation log viewer. |
| `mcp_ai_support.feature` | In-core AI tagging / semantic search (MCP today is tool-based, not embedded models). |
| `mcp_cli_wrapper.feature` | Separate AI wrapper process that shells out to `tm` (distinct from `mcp_stdio`). |
| `plugin_hook_system.feature` | User hooks on events (e.g. tag changed). |
| `plugin_system.feature` | `tm plugin install|list|…` extensibility. |
