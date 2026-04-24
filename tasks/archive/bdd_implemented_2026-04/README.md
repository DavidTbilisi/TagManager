# Archived BDD specs (implemented in product)

These `.feature` files described behaviour that now exists in **tagmanager-cli**. They are kept here so `tasks/todo_bdd/` only lists **remaining** work.

| Feature | Implementation notes |
|---------|----------------------|
| `removing_all_tags_from_file` | `tm remove --path … --all-tags`; idempotent when path missing or tags already empty. |
| `searching_files_by_tag_combinations` | `tm search` with `--match-all` (AND), default OR across tags, `--exclude` / `--exclude-tags` (NOT). |
| `thin_gui` | `tm gui` / `tm serve`, `thin_gui.html`, same DB as CLI. |
| `thin_gui_nonfunctional` | Loopback default, stdlib HTTP, quiet `log_message`, README, Ctrl+C ends server. |
| `exporting_importing_tag_data` | `tm export` / `tm import` (JSON & CSV). |
| `api_for_automation` | Local HTTP: `GET /api/v1/files/tags`, `GET /api/v1/gui/path-tags`, `POST` GUI add/remove, JSON-RPC `tags.list` / `search.files`. |
| `automated_backup_restore` | `tm backup` / `tm restore` (default `file_tags.backup.json` beside the tag DB; same merge rules as import). |

Global CLI: **`--json`**, **`--quiet`**, **`--silent`** (alias for `--quiet`).
