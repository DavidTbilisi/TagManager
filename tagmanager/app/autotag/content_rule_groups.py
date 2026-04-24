"""
Built-in content / title / filename auto-tag rule groups.

``autotag.content_pattern_groups`` selects which groups apply when
``autotag.content_use_defaults`` is true. ``None`` or missing key = all groups.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Tuple

# Each group: stable id (for config), human title, list of rule dicts.
CONTENT_RULE_GROUPS: List[Dict[str, Any]] = [
    {
        "id": "python_web",
        "title": "Python web & servers",
        "rules": [
            {"contains": "django.", "tags": ["django", "web"]},
            {"contains": "from django", "tags": ["django", "web"]},
            {"contains": "from flask", "tags": ["flask", "web"]},
            {"contains": "import flask", "tags": ["flask", "web"]},
            {"contains": "fastapi", "tags": ["fastapi", "web"]},
            {"contains": "starlette", "tags": ["starlette", "web"]},
            {"contains": "uvicorn", "tags": ["uvicorn", "server"]},
            {"contains": "gunicorn", "tags": ["gunicorn", "server"]},
            {"contains": "tornado.", "tags": ["tornado", "web"]},
            {"contains": "sanic", "tags": ["sanic", "web"]},
        ],
    },
    {
        "id": "data_ml",
        "title": "Data science & ML",
        "rules": [
            {"contains": "import pandas", "tags": ["pandas", "data"]},
            {"contains": "import numpy", "tags": ["numpy", "data"]},
            {"pattern": r"\bimport\s+torch\b", "tags": ["pytorch", "ml"]},
            {"contains": "tensorflow", "tags": ["tensorflow", "ml"]},
            {"contains": "sklearn", "tags": ["scikit-learn", "ml"]},
            {"contains": "polars", "tags": ["polars", "data"]},
        ],
    },
    {
        "id": "orm_db",
        "title": "ORM & database tooling",
        "rules": [
            {"contains": "sqlalchemy", "tags": ["sqlalchemy", "database"]},
            {"contains": "pydantic", "tags": ["pydantic"]},
            {"contains": "prisma", "tags": ["prisma", "database"]},
        ],
    },
    {
        "id": "async_messaging",
        "title": "Async & messaging",
        "rules": [
            {"contains": "celery", "tags": ["celery", "async"]},
            {"contains": "kafka", "tags": ["kafka", "messaging"]},
            {"contains": "rabbitmq", "tags": ["rabbitmq", "messaging"]},
        ],
    },
    {
        "id": "testing",
        "title": "Testing frameworks",
        "rules": [
            {"contains": "pytest", "tags": ["pytest", "testing"]},
            {"pattern": r"\bjest\b", "tags": ["jest", "testing"]},
            {"contains": "mocha", "tags": ["mocha", "testing"]},
        ],
    },
    {
        "id": "cli_frameworks",
        "title": "CLI frameworks (Typer / Click)",
        "rules": [
            {"contains": "import typer", "tags": ["typer", "cli"]},
            {"contains": "import click", "tags": ["click", "cli"]},
        ],
    },
    {
        "id": "js_frontend",
        "title": "JavaScript / TypeScript UI",
        "rules": [
            {"contains": "from \"react\"", "tags": ["react", "frontend"]},
            {"contains": "from 'react'", "tags": ["react", "frontend"]},
            {"contains": "from \"vue\"", "tags": ["vue", "frontend"]},
            {"contains": "from 'vue'", "tags": ["vue", "frontend"]},
            {"pattern": r"@angular/", "tags": ["angular", "frontend"]},
            {"contains": "svelte", "tags": ["svelte", "frontend"]},
        ],
    },
    {
        "id": "bundlers",
        "title": "Bundlers & ESLint",
        "rules": [
            {"contains": "eslint", "tags": ["eslint", "lint"]},
            {"contains": "webpack", "tags": ["webpack", "bundler"]},
            {"pattern": r"\bvite\b", "tags": ["vite", "bundler"]},
            {"contains": "rollup", "tags": ["rollup", "bundler"]},
        ],
    },
    {
        "id": "rust",
        "title": "Rust (Tokio / Serde)",
        "rules": [
            {"contains": "tokio::", "tags": ["tokio", "async", "rust"]},
            {"contains": "serde::", "tags": ["serde", "rust"]},
        ],
    },
    {
        "id": "containers_infra",
        "title": "Docker & infrastructure",
        "rules": [
            {"pattern": r"(?m)^FROM\s+\S+", "tags": ["docker", "container"]},
            {"contains": "terraform", "tags": ["terraform", "infra"]},
            {"contains": "kubernetes", "tags": ["kubernetes", "infra"]},
            {"contains": "helm", "tags": ["helm", "kubernetes", "infra"]},
        ],
    },
    {
        "id": "books_docs",
        "title": "Books & academic / long-form",
        "rules": [
            {"contains": "Project Gutenberg", "tags": ["gutenberg", "ebook", "public-domain"]},
            {"contains": "*** START OF THE PROJECT GUTENBERG", "tags": ["gutenberg", "ebook"]},
            {"contains": "Creative Commons", "tags": ["creative-commons", "license"]},
            {
                "pattern": r"(?i)\bISBN(?:[- ]?(?:13|10))?\s*[:\s]?\d",
                "tags": ["isbn", "book", "document"],
            },
            {"contains": "Table of Contents", "tags": ["toc", "book", "document"]},
            {"pattern": r"(?i)\bchapter\s+\d+\b", "tags": ["chaptered", "book", "document"]},
            {"contains": "Bibliography", "tags": ["bibliography", "academic", "document"]},
            {"contains": "## Abstract", "tags": ["abstract", "academic", "document"]},
            {"contains": "DOI:", "tags": ["doi", "academic", "document"]},
            {"contains": "doi.org/", "tags": ["doi", "academic", "document"]},
            {"contains": "All rights reserved", "tags": ["copyright", "document"]},
            {"contains": "urn:uuid:", "tags": ["uuid", "metadata"]},
            {
                "pattern": r"(?i)<package[^>]+xmlns=\s*[\"']http://www\.idpf\.org/2007/opf",
                "tags": ["epub", "ebook", "document"],
            },
            {"contains": "application/epub+zip", "tags": ["epub", "ebook"]},
        ],
    },
    {
        "id": "filename_signals",
        "title": "Filename signals (README, lockfiles, …)",
        "rules": [
            {"filename_pattern": r"(?i)readme", "tags": ["readme", "docs"]},
            {"filename_pattern": r"(?i)license|copying|unlicense", "tags": ["license", "legal"]},
            {"filename_pattern": r"(?i)changelog|history|changes", "tags": ["changelog", "docs"]},
            {"filename_pattern": r"(?i)contributing", "tags": ["contributing", "docs"]},
            {"filename_pattern": r"(?i)codeowners", "tags": ["codeowners", "github"]},
            {"filename_pattern": r"(?i)^security(\.|$)", "tags": ["security-policy", "docs"]},
            {"filename_pattern": r"(?i)^authors(\.|$)", "tags": ["authors", "docs"]},
            {"filename_pattern": r"(?i)^notice(\.|$)", "tags": ["notice", "legal"]},
            {"filename_pattern": r"(?i)^dockerfile$", "tags": ["docker", "container"]},
            {"filename_pattern": r"(?i)^makefile$", "tags": ["make", "build"]},
            {"filename_pattern": r"(?i)\.gitignore$", "tags": ["git", "ignore"]},
            {"filename_pattern": r"(?i)\.editorconfig$", "tags": ["editorconfig"]},
            {"filename_pattern": r"(?i)\.pre-commit-config\.ya?ml$", "tags": ["pre-commit", "lint"]},
            {"filename_pattern": r"(?i)dependabot\.ya?ml$", "tags": ["dependabot", "github"]},
            {"filename_pattern": r"(?i)renovate\.json$", "tags": ["renovate", "deps"]},
            {"filename_pattern": r"(?i)^pyproject\.toml$", "tags": ["pyproject", "python", "config"]},
            {"filename_pattern": r"(?i)^setup\.cfg$", "tags": ["setuptools", "python", "config"]},
            {"filename_pattern": r"(?i)^tox\.ini$", "tags": ["tox", "python", "testing"]},
            {"filename_pattern": r"(?i)^jest\.config\.(js|cjs|mjs|ts)$", "tags": ["jest", "testing"]},
            {"filename_pattern": r"(?i)^vite\.config\.(js|ts|mjs|cjs)$", "tags": ["vite", "bundler"]},
            {"filename_pattern": r"(?i)^webpack\.config\.js$", "tags": ["webpack", "bundler"]},
            {"filename_pattern": r"(?i)^rollup\.config\.(js|mjs|cjs|ts)$", "tags": ["rollup", "bundler"]},
            {"filename_pattern": r"(?i)^Cargo\.toml$", "tags": ["cargo", "rust"]},
            {"filename_pattern": r"(?i)^go\.mod$", "tags": ["go-modules", "golang"]},
            {"filename_pattern": r"(?i)^package(-lock)?\.json$", "tags": ["npm", "nodejs"]},
            {"filename_pattern": r"(?i)^pnpm-lock\.ya?ml$", "tags": ["pnpm", "nodejs"]},
            {"filename_pattern": r"(?i)^yarn\.lock$", "tags": ["yarn", "nodejs"]},
            {"filename_pattern": r"(?i)^requirements\.txt$", "tags": ["pip", "python", "deps"]},
            {"filename_pattern": r"(?i)^poetry\.lock$", "tags": ["poetry", "python", "deps"]},
            {"filename_pattern": r"(?i)^Pipfile(\.lock)?$", "tags": ["pipenv", "python"]},
            {"filename_pattern": r"(?i)^Gemfile(\.lock)?$", "tags": ["bundler", "ruby"]},
            {"filename_pattern": r"(?i)^composer\.(json|lock)$", "tags": ["composer", "php"]},
        ],
    },
    {
        "id": "title_patterns",
        "title": "Title / stem patterns (RFC, edition, …)",
        "rules": [
            {"title_pattern": r"(?i)\bedition\b", "tags": ["edition", "book"]},
            {"title_pattern": r"(?i)\bvol\.?\s*\d", "tags": ["volume", "book", "series"]},
            {"title_pattern": r"(?i)\b(part|pt)\s*\d", "tags": ["serial", "book"]},
            {"title_pattern": r"(?i)\bseries\b", "tags": ["series", "book"]},
            {
                "title_pattern": r"(?i)\b(omnibus|anthology|collection)\b",
                "tags": ["collection", "book"],
            },
            {
                "title_pattern": r"(?i)\b(definitive|revised|expanded)\s+guide\b",
                "tags": ["technical-book", "book"],
            },
            {"title_pattern": r"(?i)\bRFC[\s_]*\d+", "tags": ["rfc", "spec", "docs"]},
            {"title_pattern": r"(?i)\bWIP\b|\bdraft\b", "tags": ["draft", "wip"]},
            {"title_pattern": r"(?i)\bfinal\b", "tags": ["final", "version"]},
            {"title_pattern": r"(?i)_v\d+\.\d+", "tags": ["semver-title", "version"]},
            {
                "title_pattern": r"(?i)[\s._-]v?\d{4}[\s._-]\d{2}[\s._-]\d{2}",
                "tags": ["dated", "version"],
            },
        ],
    },
]

DEFAULT_CONTENT_RULES: List[Dict[str, Any]] = [
    rule for group in CONTENT_RULE_GROUPS for rule in group["rules"]
]

ALL_GROUP_IDS: FrozenSet[str] = frozenset(str(g["id"]) for g in CONTENT_RULE_GROUPS)


def content_rule_group_ids() -> Tuple[str, ...]:
    """Stable group ids (for ``autotag.content_pattern_groups``)."""
    return tuple(str(g["id"]) for g in CONTENT_RULE_GROUPS)
