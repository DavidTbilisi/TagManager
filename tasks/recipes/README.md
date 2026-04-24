# Automation recipes

Small, copy-paste friendly snippets for CI and local workflows using TagManager.

| File | Purpose |
|------|---------|
| [pre-commit-hook.sample](pre-commit-hook.sample) | Run `tm` before commit (e.g. validate tags or search). |
| [github-actions-example.yml](github-actions-example.yml) | Install CLI and run a tagged search in GitHub Actions. |
| [../../.github/workflows/release.yml](../../.github/workflows/release.yml) | Tag `v*` → build + PyPI (see [docs/RELEASE_CI.md](../../docs/RELEASE_CI.md)). |
| [uvx-oneliners.md](uvx-oneliners.md) | One-off runs with `uvx` without a global install. |

**Fish completions:** copy [../completions/tm.fish](../completions/tm.fish) to `~/.config/fish/completions/tm.fish`.

Adjust paths, Python version, and secrets to match your repository.
