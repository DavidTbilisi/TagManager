# 📦 FileTagger Installation Guide

## 🚀 Quick Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install filetagger-cli
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/davidtbilisi/FileTagger.git
cd FileTagger

# Install directly
pip install .

# Or build and install
pip install build
python -m build
pip install dist/filetagger_cli-1.0.0-py3-none-any.whl
```

### Option 3: Development Installation

```bash
# Clone and install in development mode
git clone https://github.com/davidtbilisi/FileTagger.git
cd FileTagger
pip install -e .
```

## 📋 Requirements

- **Python 3.7+** (Python 3.8+ recommended)
- **UTF-8 compatible terminal** (most modern terminals)

### Dependencies

FileTagger automatically installs these dependencies:

- `typer>=0.9.0` - Modern CLI framework
- `rich>=10.0.0` - Beautiful terminal output

## 🎯 Verify Installation

After installation, verify FileTagger is working:

```bash
# Test the main command
tm --help

# Or use the full name
filetagger --help

# Test basic functionality
tm stats
```

You should see the FileTagger help menu with all available commands.

## 🔧 Command Aliases

FileTagger provides two command aliases:

- `tm` - Short and convenient for daily use
- `filetagger` - Full name for clarity

Both commands are identical in functionality.

## 🏠 Configuration

FileTagger creates its configuration automatically on first run:

- **Config file**: `~/.filetagger/config.ini`
- **Tag database**: `~/.filetagger/file_tags.json`

## 🚀 Quick Start

```bash
# Add tags to a file
tm add document.pdf --tags work important project-x

# Search for files
tm search --tags work

# View all files in a tree
tm ls --tree

# Get statistics
tm stats --chart

# Bulk operations
tm bulk add "*.py" --tags python code

# Smart filtering
tm filter duplicates
```

## 🔄 Updating

To update FileTagger to the latest version:

```bash
pip install --upgrade filetagger-cli
```

## 🗑️ Uninstallation

To remove FileTagger:

```bash
pip uninstall filetagger-cli
```

Note: This will not remove your tag database or configuration files. To completely remove all data:

```bash
# Remove the package
pip uninstall filetagger-cli

# Remove data (optional)
rm -rf ~/.filetagger/  # Linux/macOS
rmdir /s %USERPROFILE%\.filetagger  # Windows
```

## 🐛 Troubleshooting

### Common Issues

1. **Command not found**: Ensure Python's Scripts directory is in your PATH
2. **Permission errors**: Use `pip install --user filetagger-cli` for user installation
3. **Import errors**: Ensure you have Python 3.7+ and all dependencies installed

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/davidtbilisi/FileTagger/issues)
2. Run `tm --help` for command documentation
3. Create a new issue with your error details

## 🎉 Next Steps

After installation, check out:

- [README.md](README.md) - Full feature documentation
- [Examples](README.md#-examples) - Real-world usage examples
- [Advanced Features](README.md#-advanced-operations) - Power user features

Happy tagging! 🏷️
