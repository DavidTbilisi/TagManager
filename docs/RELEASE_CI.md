# Automated PyPI releases (GitHub Actions)

Pushing a **git tag** matching `v*` (for example `v1.7.0`) runs [`.github/workflows/release.yml`](../.github/workflows/release.yml): it builds with `python -m build` and uploads to PyPI using [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish).

## One-time setup (trusted publishing)

The workflow uses **OIDC** (no `PYPI_API_TOKEN` in the repo).

1. PyPI → **tagmanager-cli** → **Publishing** → trusted publisher **GitHub**: this repository, workflow **`release.yml`**, environment *(leave blank unless you use a GitHub Environment)*.
2. Workflow must keep `permissions: id-token: write` (already set).

Official guide: [Adding a trusted publisher to your PyPI project](https://docs.pypi.org/trusted-publishers/adding-a-publishing-source/).

### Optional — API token instead

If you cannot use trusted publishing, add a `with` block on the publish step:

```yaml
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

Create the token at [PyPI account tokens](https://pypi.org/manage/account/token/) and add **`PYPI_API_TOKEN`** under repo **Settings → Secrets and variables → Actions**.

## Release checklist (maintainer)

Requires [GitHub CLI](https://cli.github.com/) (`gh`) authenticated for this repo (`gh auth login`).

1. Bump version (`python bump_version.py patch|minor|major --no-git` or edit `pyproject.toml` + `tagmanager/__init__.py`).
2. Update `release_notes.md` and merge to the default branch (`main` / `master`).
3. On that branch at the release commit, create the GitHub release (this **creates and pushes** the `v*` tag, which starts the PyPI workflow):

   ```bash
   ./publish.sh release
   ```

   Same as `gh release create vX.Y.Z --title "TagManager vX.Y.Z" --notes-file release_notes.md` with `vX.Y.Z` taken from `pyproject.toml`. Flags: `./publish.sh release --draft`, `./publish.sh release --dry-run`.

   Manual alternative: `gh release create …` with `--generate-notes` instead of `--notes-file`.

4. Confirm the **release** workflow run on the **Actions** tab succeeded (PyPI upload).

Local dry-run build (no upload): `./install.sh --build-only` or `python -m build`.
