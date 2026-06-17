# uvx one-liners

Run the published CLI in an isolated environment (requires [uv](https://github.com/astral-sh/uv)).

```bash
# Show help
uvx filetagger-cli --help

# Search without installing globally
uvx filetagger-cli search --tags python

# JSON output (any subcommand that supports it)
uvx filetagger-cli --json search --tags docs
```

Watch mode needs the optional extra:

```bash
uvx --with watchdog filetagger-cli watch . --tags inbox
```

MCP server:

```bash
uvx --with mcp filetagger-cli mcp
```
