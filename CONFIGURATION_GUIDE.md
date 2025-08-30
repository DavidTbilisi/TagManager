# ⚙️ Configuration Management Guide

TagManager includes a comprehensive configuration system that allows you to customize behavior, set defaults, and manage preferences across all features.

## 🚀 **Quick Start**

```bash
# View all available configuration options
tagmanager config list --show-defaults

# Get configuration information
tagmanager config info

# Set a configuration value
tagmanager config set display.emojis false

# Get a specific configuration value
tagmanager config get display.emojis

# List configurations by category
tagmanager config list --category display
```

## 📋 **Available Commands**

### **Basic Operations**

```bash
# Get a configuration value
tagmanager config get <key>

# Set a configuration value
tagmanager config set <key> <value>

# Delete a configuration value (revert to default)
tagmanager config delete <key>

# List all configuration values
tagmanager config list

# List with default values shown
tagmanager config list --show-defaults

# List by category
tagmanager config list --category display
```

### **Management Operations**

```bash
# Reset specific key to default
tagmanager config reset <key>

# Reset ALL configuration to defaults (use with caution!)
tagmanager config reset

# Show configuration system information
tagmanager config info

# Show available categories
tagmanager config categories

# Validate current configuration
tagmanager config validate
```

### **Import/Export**

```bash
# Export configuration to file
tagmanager config export --file my_config.json

# Import configuration from file (merge with existing)
tagmanager config import my_config.json

# Import configuration (replace existing)
tagmanager config import my_config.json --replace
```

## 🎛️ **Configuration Categories**

### **🎨 Display Settings**

Control how TagManager displays information:

| Key                  | Default | Description                        |
| -------------------- | ------- | ---------------------------------- |
| `display.emojis`     | `true`  | Enable emoji icons in output       |
| `display.colors`     | `true`  | Enable colored output              |
| `display.tree_icons` | `true`  | Show tree icons in tree view       |
| `display.max_items`  | `100`   | Maximum number of items to display |

**Examples:**

```bash
# Disable emojis for Windows compatibility
tagmanager config set display.emojis false

# Increase display limit
tagmanager config set display.max_items 200

# Disable colors for plain text output
tagmanager config set display.colors false
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
tagmanager config set search.fuzzy_threshold 0.8

# Enable case-sensitive search by default
tagmanager config set search.case_sensitive true
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
tagmanager config set tags.max_per_file 100

# Change tag separator
tagmanager config set tags.separator ","
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
tagmanager config set files.include_hidden true

# Increase file size limit
tagmanager config set files.max_size_mb 500
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
tagmanager config set output.format json

# Use ISO date format
tagmanager config set output.date_format "%Y-%m-%dT%H:%M:%S"
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
tagmanager config set performance.cache_enabled false

# Increase batch size for large operations
tagmanager config set performance.batch_size 5000
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
tagmanager config set backup.count 10

# Disable auto-backup for bulk operations
tagmanager config set backup.on_bulk_operations false
```

### **🔧 Advanced Settings**

Developer and debugging options:

| Key                         | Default | Description                                           |
| --------------------------- | ------- | ----------------------------------------------------- |
| `advanced.debug_mode`       | `false` | Enable debug mode with verbose output                 |
| `advanced.log_level`        | `INFO`  | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `advanced.plugin_directory` | `""`    | Directory for TagManager plugins                      |

**Examples:**

```bash
# Enable debug mode
tagmanager config set advanced.debug_mode true

# Set verbose logging
tagmanager config set advanced.log_level DEBUG
```

## 🏠 **Configuration Storage**

### **Location**

Configuration is stored in platform-specific locations:

- **Windows**: `%LOCALAPPDATA%\TagManager\config.json`
- **macOS**: `~/.config/tagmanager/config.json`
- **Linux**: `~/.config/tagmanager/config.json`

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

TagManager automatically migrates from the old INI-based configuration:

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
tagmanager config export --file production.json

# Set multiple values
tagmanager config set display.emojis false
tagmanager config set display.colors false
tagmanager config set output.format json

# Validate all settings
tagmanager config validate
```

### **Environment-Specific Configs**

```bash
# Development environment
tagmanager config set advanced.debug_mode true
tagmanager config set advanced.log_level DEBUG
tagmanager config export --file dev_config.json

# Production environment
tagmanager config set advanced.debug_mode false
tagmanager config set performance.cache_enabled true
tagmanager config export --file prod_config.json

# Switch environments
tagmanager config import dev_config.json --replace
```

### **Team Configuration**

```bash
# Create team standard
tagmanager config set display.emojis false  # Windows compatibility
tagmanager config set output.format table
tagmanager config set tags.max_per_file 25
tagmanager config export --file team_standard.json

# Team members import
tagmanager config import team_standard.json
```

## 🚨 **Troubleshooting**

### **Common Issues**

**Configuration not taking effect:**

```bash
# Check if value is set correctly
tagmanager config get <key>

# Validate configuration
tagmanager config validate

# Reset to defaults if corrupted
tagmanager config reset
```

**Invalid values:**

```bash
# Validation will show errors
tagmanager config validate

# Reset specific invalid key
tagmanager config reset <key>
```

**Permission issues:**

```bash
# Check configuration info
tagmanager config info

# Ensure config directory is writable
# Windows: Check %LOCALAPPDATA%\TagManager permissions
# Unix: Check ~/.config/tagmanager permissions
```

### **Recovery**

```bash
# Reset all configuration to defaults
tagmanager config reset --yes

# Or manually delete config file and restart
# Windows: del "%LOCALAPPDATA%\TagManager\config.json"
# Unix: rm ~/.config/tagmanager/config.json
```

## 📚 **Integration Examples**

### **Script Integration**

```bash
#!/bin/bash
# Setup script for new users

# Configure for terminal use
tagmanager config set display.emojis true
tagmanager config set display.colors true

# Optimize for performance
tagmanager config set performance.batch_size 2000
tagmanager config set performance.cache_enabled true

# Set reasonable limits
tagmanager config set tags.max_per_file 30
tagmanager config set display.max_items 50

echo "TagManager configured for optimal terminal use!"
```

### **CI/CD Integration**

```bash
# .github/workflows/tagmanager.yml
- name: Configure TagManager
  run: |
    tagmanager config set display.emojis false
    tagmanager config set display.colors false
    tagmanager config set output.format json
    tagmanager config set advanced.log_level ERROR
```

## 🎯 **Best Practices**

1. **🔧 Start with defaults** - Only change what you need
2. **📋 Document changes** - Export configs for team sharing
3. **✅ Validate regularly** - Run `config validate` after changes
4. **💾 Backup configs** - Export before major changes
5. **🔄 Use categories** - Organize related settings together
6. **🧪 Test changes** - Verify behavior after configuration changes

## 🎉 **Success!**

You now have complete control over TagManager's behavior through the powerful configuration system. Customize it to match your workflow and preferences!

**Pro Tips:**

- Use `--show-defaults` to see all available options
- Export configurations for different environments
- Validate after making changes to catch errors early
- Reset individual keys rather than entire config when troubleshooting

---

**Configuration Categories**: Display • Search • Tags • Files • Output • Performance • Backup • Advanced
