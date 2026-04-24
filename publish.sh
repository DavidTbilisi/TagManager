#!/usr/bin/env bash
# Create a GitHub release (and v* tag) from the current repo state — triggers PyPI via Actions.
# Requires: gh (https://cli.github.com/), release_notes.md, version in pyproject.toml.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYPROJECT="$ROOT/pyproject.toml"
NOTES="$ROOT/release_notes.md"

usage() {
  echo "Usage: $0 release [--draft] [--dry-run]"
  echo ""
  echo "  Reads version from pyproject.toml, runs:"
  echo "    gh release create v<version> --title ... --notes-file release_notes.md"
  echo "  Pushing tag v* starts .github/workflows/release.yml (PyPI trusted publishing)."
  exit "${1:-0}"
}

version_from_pyproject() {
  if [[ ! -f "$PYPROJECT" ]]; then
    echo "error: pyproject.toml not found at $PYPROJECT" >&2
    exit 1
  fi
  grep -E '^version[[:space:]]*=' "$PYPROJECT" | head -1 | sed -E 's/^version[[:space:]]*=[[:space:]]*["'\'']([^"'\'']+).*/\1/'
}

cmd_release() {
  local draft=() dry_run=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --draft) draft=(--draft); shift ;;
      --dry-run) dry_run=true; shift ;;
      -h|--help) usage 0 ;;
      *)
        echo "error: unknown option: $1" >&2
        usage 1
        ;;
    esac
  done

  local version tag
  version="$(version_from_pyproject)"
  if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "error: expected major.minor.patch in pyproject.toml (got: '${version:-empty}')" >&2
    exit 1
  fi
  tag="v${version}"

  if ! command -v gh >/dev/null 2>&1; then
    echo "error: gh (GitHub CLI) not in PATH — https://cli.github.com/" >&2
    exit 1
  fi

  if [[ ! -f "$NOTES" ]]; then
    echo "error: missing $NOTES" >&2
    exit 1
  fi

  if gh release view "$tag" >/dev/null 2>&1; then
    echo "error: GitHub release $tag already exists" >&2
    exit 1
  fi

  local cmd=(gh release create "$tag" --title "TagManager $tag" --notes-file "$NOTES")
  if [[ ${#draft[@]} -gt 0 ]]; then
    cmd+=("${draft[@]}")
  fi

  if [[ "$dry_run" == true ]]; then
    printf 'dry-run:'
    printf ' %q' "${cmd[@]}"
    printf '\n'
    exit 0
  fi

  (cd "$ROOT" && exec "${cmd[@]}")
}

main() {
  case "${1:-}" in
    release) shift; cmd_release "$@" ;;
    ""|-h|--help) usage 0 ;;
    *)
      echo "error: unknown command '${1:-}' (expected: release)" >&2
      usage 1
      ;;
  esac
}

main "$@"
