# uvx one-liners

Run the published CLI in an isolated environment (requires [uv](https://github.com/astral-sh/uv)).

```bash
# Show help
uvx tagmanager-cli --help

# Search without installing globally
uvx tagmanager-cli search --tags python

# JSON output (any subcommand that supports it)
uvx tagmanager-cli --json search --tags docs
```

Watch mode needs the optional extra:

```bash
uvx --with watchdog tagmanager-cli watch . --tags inbox
```

MCP server:

```bash
uvx --with mcp tagmanager-cli mcp
```
