#!/bin/bash
# TagManager Project Cleanup Script
# Removes unused files and folders to keep the project clean

echo "🧹 TagManager Project Cleanup"
echo "============================="

# Function to safely remove files/directories
safe_remove() {
    if [ -e "$1" ]; then
        echo "🗑️  Removing: $1"
        rm -rf "$1"
    else
        echo "ℹ️  Not found: $1"
    fi
}

echo ""
echo "📁 Removing legacy files..."

# Legacy main CLI file
safe_remove "tm.py"

# Legacy configuration files
safe_remove "config.ini"
safe_remove "configReader.py" 
safe_remove "configWriter.py"

# Test configuration files
safe_remove "not_test_config.ini"
safe_remove "test_config.json"

# Old batch files
safe_remove "tm.bat"
safe_remove "tm"

# Legacy test files (keep new tests/ directory)
safe_remove "tests.py"

echo ""
echo "🏗️  Removing build artifacts..."

# Python cache directories
safe_remove "__pycache__"
safe_remove "tagmanager/app/__pycache__"
find tagmanager/app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Build artifacts
safe_remove "tagmanager_cli.egg-info"
safe_remove "dist"
safe_remove "build"

echo ""
echo "🤔 Optional removals (you decide):"
echo "   • venv/ - Virtual environment (can be recreated with 'python -m venv venv')"
echo "   • .git/ - Git repository (only if you don't need version history)"

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📋 Remaining important files:"
echo "   • tagmanager/ - Main package directory"
echo "   • pyproject.toml - Package configuration"
echo "   • requirements.txt - Dependencies"
echo "   • README.md - Documentation"
echo "   • LICENSE - License file"
echo "   • MANIFEST.in - Package manifest"
echo "   • *.md - Documentation files"
echo "   • *.sh, *.py - Automation scripts"
echo ""
echo "🚀 Your project is now clean and ready for distribution!"
