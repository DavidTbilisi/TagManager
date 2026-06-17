# 🤖 FileTagger Automation Guide

Complete guide for automated version management, building, and publishing.

## 🚀 **Quick Start**

### **One-Command Release**

```bash
# Patch release (1.0.0 -> 1.0.1) and publish to PyPI
./release.sh patch

# Minor release (1.0.0 -> 1.1.0) locally only
./release.sh minor --local-only

# Major release (1.0.0 -> 2.0.0) dry run
./release.sh major --dry-run
```

### **Manual Steps**

```bash
# 1. Bump version
python bump_version.py patch

# 2. Install locally
./install.sh --local

# 3. Publish to PyPI
./install.sh --remote
```

## 🛠️ **Available Scripts**

### 1. **Version Bumper** (`bump_version.py`)

Automatically updates version numbers across all project files.

```bash
# Show current version
python bump_version.py --current

# Bump patch version (1.0.0 -> 1.0.1)
python bump_version.py patch

# Bump minor version (1.0.0 -> 1.1.0)
python bump_version.py minor

# Bump major version (1.0.0 -> 2.0.0)
python bump_version.py major

# Skip git operations
python bump_version.py patch --no-git
```

**What it updates:**

- `pyproject.toml` - Package version
- `filetagger/__init__.py` - Module version
- Creates git commit and tag (optional)

### 2. **Installation Script** (`install.sh` / `install.bat`)

Builds and installs the package locally or publishes to PyPI.

```bash
# Linux/macOS
./install.sh --local      # Build and install locally
./install.sh --remote     # Publish to PyPI and install
./install.sh --build-only # Build package only
./install.sh --test-only  # Test existing installation

# Windows
install.bat --local       # Build and install locally
install.bat --remote      # Publish to PyPI and install
```

**Features:**

- ✅ Automatic dependency management
- ✅ Clean builds (removes old artifacts)
- ✅ Installation verification
- ✅ Cross-platform support
- ✅ Colorful, informative output

### 3. **Release Workflow** (`release.sh`)

Complete automation for version bumping, building, and publishing.

```bash
# Full release workflow
./release.sh patch              # Patch release to PyPI
./release.sh minor --local-only # Minor release, local only
./release.sh major --dry-run    # Show what would happen

# Options
--local-only    # Skip PyPI, install locally only
--dry-run       # Show actions without executing
--skip-tests    # Skip running unit tests
--help          # Show usage information
```

**Workflow steps:**

1. 🔍 Check git status
2. 🧪 Run tests (optional)
3. 📈 Bump version
4. 📦 Build package
5. 🚀 Install/Publish
6. 🏷️ Create GitHub release (if publishing)

### 4. **PyPI Setup Helper** (`setup_pypi.py`)

Helps configure PyPI credentials for publishing.

```bash
python setup_pypi.py
```

**Options:**

- Create `.pypirc` file
- Set environment variables
- Test PyPI connection

## 🔧 **Configuration**

### **PyPI Credentials**

Choose one method:

#### **Method 1: API Token (Recommended)**

```bash
# Set environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=your-api-token

# Or use the setup helper
python setup_pypi.py
```

#### **Method 2: Username/Password**

```bash
# Set environment variables
export TWINE_USERNAME=your-username
export TWINE_PASSWORD=your-password

# Or create ~/.pypirc
python setup_pypi.py
```

### **Git Configuration**

For automatic git operations:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 📋 **Workflow Examples**

### **Development Workflow**

```bash
# 1. Make changes to code
# 2. Test changes
python -m unittest tests.py -v

# 3. Patch release for bug fixes
./release.sh patch --local-only

# 4. Test the installed package
tm --help
```

### **Production Release**

```bash
# 1. Ensure all tests pass
python -m unittest tests.py -v

# 2. Check what would happen
./release.sh minor --dry-run

# 3. Execute the release
./release.sh minor

# 4. Verify on PyPI
pip install --upgrade filetagger-cli
```

### **Hotfix Release**

```bash
# Quick patch for critical bugs
python bump_version.py patch && ./install.sh --remote
```

## 🎯 **Best Practices**

### **Version Numbering**

- **Patch** (1.0.0 → 1.0.1): Bug fixes, small improvements
- **Minor** (1.0.0 → 1.1.0): New features, backward compatible
- **Major** (1.0.0 → 2.0.0): Breaking changes

### **Release Checklist**

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if exists)
- [ ] Git working directory clean
- [ ] PyPI credentials configured

### **Testing Strategy**

```bash
# 1. Test locally first
./release.sh patch --local-only

# 2. Verify functionality
tm stats
tm add test.txt --tags test
tm search --tags test

# 3. If all good, publish
./install.sh --remote
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Build Fails**

```bash
# Check Python version
python --version  # Should be 3.7+

# Install build tools
pip install --upgrade pip build twine
```

#### **PyPI Upload Fails**

```bash
# Check credentials
python setup_pypi.py

# Test connection
twine check dist/*
```

#### **Git Operations Fail**

```bash
# Skip git operations
python bump_version.py patch --no-git
./release.sh patch --dry-run
```

#### **Permission Errors**

```bash
# Use user installation
pip install --user filetagger-cli

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### **Debug Mode**

```bash
# Verbose output
./install.sh --build-only  # Build only to check for issues
./release.sh patch --dry-run  # See what would happen
```

## 📊 **Monitoring**

### **Check Package Status**

```bash
# Current version
python bump_version.py --current

# PyPI status
pip show filetagger-cli

# Installation test
tm --help
```

### **Verify Release**

```bash
# Check PyPI page
# https://pypi.org/project/filetagger-cli/

# Test fresh installation
pip uninstall filetagger-cli -y
pip install filetagger-cli
tm --version
```

## 🎉 **Success Indicators**

After a successful release:

- ✅ Version bumped in all files
- ✅ Package builds without errors
- ✅ Installation works correctly
- ✅ All commands functional
- ✅ PyPI page updated (if published)
- ✅ GitHub release created (if published)

## 🔄 **Continuous Integration**

For automated releases, you can integrate these scripts into CI/CD:

```yaml
# Example GitHub Actions workflow
name: Release
on:
  push:
    tags: ["v*"]
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.8"
      - name: Install dependencies
        run: pip install build twine
      - name: Build and publish
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: ./install.sh --remote
```

## 📚 **Additional Resources**

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [Twine Documentation](https://twine.readthedocs.io/)

---

**🎯 Happy Automating!** These scripts make releasing FileTagger updates as simple as running one command. No more manual version bumping, building, or publishing! 🚀
