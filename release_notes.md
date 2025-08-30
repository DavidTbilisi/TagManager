# TagManager v1.1.0 - Configuration & Storage Management

## 🎯 What's New

### ⚙️ **Configuration Management System**

- **Complete config system** with 27+ settings across 9 categories
- **CLI commands**: `tm config get/set/list/reset/export/import`
- **Show defaults**: `tm config list --show-defaults` to see all available options
- **Reset to defaults**: `tm config reset` for individual keys or full reset
- **Categories**: display, search, tags, files, output, performance, backup, storage, advanced

### 🗂️ **Configurable Tag Storage Location**

- **Custom storage paths**: `tm config set storage.tag_file_path "~/my_tags.json"`
- **Cloud sync support**: Store tags in Dropbox, OneDrive, Google Drive folders
- **Project-specific**: Different tag databases for different projects
- **Cross-platform**: Works on Windows, macOS, Linux with `~` expansion

### 🏷️ **Enhanced Multi-Tag Input**

- **Flexible tag syntax**: Comma-separated tags with automatic whitespace handling
- **Multiple methods**: `--tags python,web,demo` or `--tags python --tags web`
- **Improved parsing**: Better handling of mixed tag input formats
- **Consistent behavior**: Same logic across `add` and `bulk add` commands

### 🔧 **Technical Improvements**

- **Backward compatibility**: Seamless migration from old config system
- **Validation**: Type checking and error handling for all config values
- **Documentation**: Comprehensive guides and help text
- **Cross-platform fixes**: Windows Unicode and emoji compatibility

## 🚀 **Quick Start**

```bash
# Configure your setup
tm config list --show-defaults
tm config set storage.tag_file_path "~/Documents/my_tags.json"

# Add multiple tags easily
tm add myfile.py --tags python,web,demo
tm bulk add "*.py" --tags python,code,project

# Manage configuration
tm config reset storage.tag_file_path  # Reset to default
tm config export backup.json           # Backup settings
```

## 📋 **Migration Notes**

- Existing installations continue working without changes
- New configuration system automatically migrates from legacy `config.ini`
- All previous commands and functionality remain unchanged
