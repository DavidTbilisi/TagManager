# ⚙️ Configuration Management Guide

FileTagger includes a comprehensive configuration system that allows you to customize behavior, set defaults, and manage preferences across all features.

## 🚀 **Quick Start**

```bash
# View all available configuration options
filetagger config list --show-defaults

# Get configuration information
filetagger config info

# Set a configuration value
filetagger config set display.emojis false

# Get a specific configuration value
filetagger config get display.emojis

# List configurations by category
filetagger config list --category display
```

## 📋 **Available Commands**

### **Basic Operations**

```bash
# Get a configuration value
filetagger config get <key>

# Set a configuration value
filetagger config set <key> <value>

# Delete a configuration value (revert to default)
filetagger config delete <key>

# List all configuration values
filetagger config list

# List with default values shown
filetagger config list --show-defaults

# List by category
filetagger config list --category display
```

### **Management Operations**

```bash
# Reset specific key to default
filetagger config reset <key>

# Reset ALL configuration to defaults (use with caution!)
filetagger config reset

# Show configuration system information
filetagger config info

# Show available categories
filetagger config categories

# Validate current configuration
filetagger config validate
```

### **Import/Export**

```bash
# Export configuration to file
filetagger config export --file my_config.json

# Import configuration from file (merge with existing)
filetagger config import my_config.json

# Import configuration (replace existing)
filetagger config import my_config.json --replace
```

## 🎛️ **Configuration Categories**

### **🎨 Display Settings**

Control how FileTagger displays information:

| Key                  | Default | Description                        |
| -------------------- | ------- | ---------------------------------- |
| `display.emojis`     | `true`  | Enable emoji icons in output       |
| `display.colors`     | `true`  | Enable colored output              |
| `display.tree_icons` | `true`  | Show tree icons in tree view       |
| `display.max_items`  | `100`   | Maximum number of items to display |

**Examples:**

```bash
# Disable emojis for Windows compatibility
filetagger config set display.emojis false

# Increase display limit
filetagger config set display.max_items 200

# Disable colors for plain text output
filetagger config set display.colors false
```

### **🔍 Search Settings**

Configure search behavior:

| Key                          | Default | Description                                 |
| ---------------------------- | ------- | ------------------------------------------- |
| `search.fuzzy_threshold`     | `0.6`   | Fuzzy search similarity threshold (0.0-1.0) |
| `search.case_sensitive`      | `false` | Enable case-sensitive search by default     |
| `search.exact_match_default` | `false` | Use exact matching by default               |

**Examples:**

```bash
# Make search more strict
filetagger config set search.fuzzy_threshold 0.8

# Enable case-sensitive search by default
filetagger config set search.case_sensitive true
```

### **🏷️ Tag Settings**

Control tag behavior and validation:

| Key                 | Default | Description                           |
| ------------------- | ------- | ------------------------------------- |
| `tags.max_per_file` | `50`    | Maximum number of tags per file       |
| `tags.separator`    | `" "`   | Separator character for multiple tags |
| `tags.auto_create`  | `true`  | Automatically create new tags         |
| `tags.validation`   | `true`  | Enable tag name validation            |

**Examples:**

```bash
# Increase tag limit
filetagger config set tags.max_per_file 100

# Change tag separator
filetagger config set tags.separator ","
```

### **📁 File Settings**

Configure file processing behavior:

| Key                     | Default | Description                                 |
| ----------------------- | ------- | ------------------------------------------- |
| `files.follow_symlinks` | `false` | Follow symbolic links when processing files |
| `files.include_hidden`  | `false` | Include hidden files in operations          |
| `files.max_size_mb`     | `100`   | Maximum file size to process (MB)           |

**Examples:**

```bash
# Include hidden files
filetagger config set files.include_hidden true

# Increase file size limit
filetagger config set files.max_size_mb 500
```

### **📤 Output Settings**

Control output formatting:

| Key                  | Default             | Description                                    |
| -------------------- | ------------------- | ---------------------------------------------- |
| `output.format`      | `table`             | Default output format (table, json, csv, tree) |
| `output.date_format` | `%Y-%m-%d %H:%M:%S` | Date format string                             |
| `output.timezone`    | `local`             | Timezone for date display                      |

**Examples:**

```bash
# Default to JSON output
filetagger config set output.format json

# Use ISO date format
filetagger config set output.date_format "%Y-%m-%dT%H:%M:%S"
```

### **⚡ Performance Settings**

Optimize performance for your use case:

| Key                         | Default | Description                           |
| --------------------------- | ------- | ------------------------------------- |
| `performance.cache_enabled` | `true`  | Enable caching for better performance |
| `performance.cache_ttl`     | `3600`  | Cache time-to-live in seconds         |
| `performance.batch_size`    | `1000`  | Batch size for bulk operations        |

**Examples:**

```bash
# Disable caching for real-time accuracy
filetagger config set performance.cache_enabled false

# Increase batch size for large operations
filetagger config set performance.batch_size 5000
```

### **💾 Backup Settings**

Configure automatic backup behavior:

| Key                         | Default | Description                          |
| --------------------------- | ------- | ------------------------------------ |
| `backup.auto_backup`        | `true`  | Automatically backup tag database    |
| `backup.count`              | `5`     | Number of backup files to keep       |
| `backup.on_bulk_operations` | `true`  | Create backup before bulk operations |

**Examples:**

```bash
# Increase backup retention
filetagger config set backup.count 10

# Disable auto-backup for bulk operations
filetagger config set backup.on_bulk_operations false
```

### **🔧 Advanced Settings**

Developer and debugging options:

| Key                         | Default | Description                                           |
| --------------------------- | ------- | ----------------------------------------------------- |
| `advanced.debug_mode`       | `false` | Enable debug mode with verbose output                 |
| `advanced.log_level`        | `INFO`  | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `advanced.plugin_directory` | `""`    | Directory for FileTagger plugins                      |

**Examples:**

```bash
# Enable debug mode
filetagger config set advanced.debug_mode true

# Set verbose logging
filetagger config set advanced.log_level DEBUG
```

## 🏠 **Configuration Storage**

### **Location**

Configuration is stored in platform-specific locations:

- **Windows**: `%LOCALAPPDATA%\FileTagger\config.json`
- **macOS**: `~/.config/filetagger/config.json`
- **Linux**: `~/.config/filetagger/config.json`

### **Format**

Configuration is stored as JSON:

```json
{
  "display": {
    "emojis": false,
    "colors": true
  },
  "search": {
    "fuzzy_threshold": 0.8
  }
}
```

## 🔄 **Migration & Compatibility**

### **Legacy Configuration**

FileTagger automatically migrates from the old INI-based configuration:

- Old `config.ini` files are automatically converted
- Settings are mapped to the new hierarchical structure
- Original files are preserved

### **Version Compatibility**

- Configuration format is forward-compatible
- New settings get default values automatically
- Invalid settings are ignored with warnings

## 🛠️ **Advanced Usage**

### **Bulk Configuration**

```bash
# Export current config
filetagger config export --file production.json

# Set multiple values
filetagger config set display.emojis false
filetagger config set display.colors false
filetagger config set output.format json

# Validate all settings
filetagger config validate
```

### **Environment-Specific Configs**

```bash
# Development environment
filetagger config set advanced.debug_mode true
filetagger config set advanced.log_level DEBUG
filetagger config export --file dev_config.json

# Production environment
filetagger config set advanced.debug_mode false
filetagger config set performance.cache_enabled true
filetagger config export --file prod_config.json

# Switch environments
filetagger config import dev_config.json --replace
```

### **Team Configuration**

```bash
# Create team standard
filetagger config set display.emojis false  # Windows compatibility
filetagger config set output.format table
filetagger config set tags.max_per_file 25
filetagger config export --file team_standard.json

# Team members import
filetagger config import team_standard.json
```

## 🚨 **Troubleshooting**

### **Common Issues**

**Configuration not taking effect:**

```bash
# Check if value is set correctly
filetagger config get <key>

# Validate configuration
filetagger config validate

# Reset to defaults if corrupted
filetagger config reset
```

**Invalid values:**

```bash
# Validation will show errors
filetagger config validate

# Reset specific invalid key
filetagger config reset <key>
```

**Permission issues:**

```bash
# Check configuration info
filetagger config info

# Ensure config directory is writable
# Windows: Check %LOCALAPPDATA%\FileTagger permissions
# Unix: Check ~/.config/filetagger permissions
```

### **Recovery**

```bash
# Reset all configuration to defaults
filetagger config reset --yes

# Or manually delete config file and restart
# Windows: del "%LOCALAPPDATA%\FileTagger\config.json"
# Unix: rm ~/.config/filetagger/config.json
```

## 📚 **Integration Examples**

### **Script Integration**

```bash
#!/bin/bash
# Setup script for new users

# Configure for terminal use
filetagger config set display.emojis true
filetagger config set display.colors true

# Optimize for performance
filetagger config set performance.batch_size 2000
filetagger config set performance.cache_enabled true

# Set reasonable limits
filetagger config set tags.max_per_file 30
filetagger config set display.max_items 50

echo "FileTagger configured for optimal terminal use!"
```

### **CI/CD Integration**

```bash
# .github/workflows/filetagger.yml
- name: Configure FileTagger
  run: |
    filetagger config set display.emojis false
    filetagger config set display.colors false
    filetagger config set output.format json
    filetagger config set advanced.log_level ERROR
```

## 🎯 **Best Practices**

1. **🔧 Start with defaults** - Only change what you need
2. **📋 Document changes** - Export configs for team sharing
3. **✅ Validate regularly** - Run `config validate` after changes
4. **💾 Backup configs** - Export before major changes
5. **🔄 Use categories** - Organize related settings together
6. **🧪 Test changes** - Verify behavior after configuration changes

## 🎉 **Success!**

You now have complete control over FileTagger's behavior through the powerful configuration system. Customize it to match your workflow and preferences!

**Pro Tips:**

- Use `--show-defaults` to see all available options
- Export configurations for different environments
- Validate after making changes to catch errors early
- Reset individual keys rather than entire config when troubleshooting

---

**Configuration Categories**: Display • Search • Tags • Files • Output • Performance • Backup • Advanced
