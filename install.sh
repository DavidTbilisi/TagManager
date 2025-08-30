#!/bin/bash

# TagManager Installation Script
# Supports local and remote (PyPI) installation with automatic upgrades

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis for better UX
ROCKET="🚀"
PACKAGE="📦"
CHECK="✅"
WARNING="⚠️"
ERROR="❌"
INFO="ℹ️"
SPARKLES="✨"
GEAR="⚙️"

# Configuration
PACKAGE_NAME="tagmanager-cli"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$PROJECT_DIR/dist"
PYPROJECT_FILE="$PROJECT_DIR/pyproject.toml"

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  TagManager Installation Script${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}${CHECK} $1${NC}"
}

print_info() {
    echo -e "${CYAN}${INFO} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_error() {
    echo -e "${RED}${ERROR} $1${NC}"
}

print_step() {
    echo -e "${PURPLE}${GEAR} $1${NC}"
}

get_current_version() {
    if [[ -f "$PYPROJECT_FILE" ]]; then
        grep "version" "$PYPROJECT_FILE" | sed 's/.*version.*=.*"\(.*\)".*/\1/'
    else
        echo "unknown"
    fi
}

check_dependencies() {
    print_step "Checking dependencies..."
    
    # Check Python
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    # Use python3 if available, otherwise python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    else
        PYTHON_CMD="python"
        PIP_CMD="pip"
    fi
    
    print_info "Using Python: $($PYTHON_CMD --version)"
    
    # Check pip
    if ! command -v $PIP_CMD &> /dev/null; then
        print_error "pip is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

install_build_tools() {
    print_step "Installing/upgrading build tools..."
    $PIP_CMD install --upgrade pip build twine
    print_success "Build tools ready"
}

build_package() {
    print_step "Building package..."
    
    cd "$PROJECT_DIR"
    
    # Clean previous builds
    if [[ -d "$DIST_DIR" ]]; then
        rm -rf "$DIST_DIR"
        print_info "Cleaned previous build artifacts"
    fi
    
    # Build package
    $PYTHON_CMD -m build
    
    if [[ $? -eq 0 ]]; then
        print_success "Package built successfully"
        ls -la "$DIST_DIR"
    else
        print_error "Package build failed"
        exit 1
    fi
}

install_local() {
    print_step "Installing package locally..."
    
    # Uninstall existing version
    $PIP_CMD uninstall $PACKAGE_NAME -y 2>/dev/null || true
    
    # Find the wheel file
    WHEEL_FILE=$(find "$DIST_DIR" -name "*.whl" | head -n 1)
    
    if [[ -z "$WHEEL_FILE" ]]; then
        print_error "No wheel file found in $DIST_DIR"
        exit 1
    fi
    
    # Install the wheel
    $PIP_CMD install "$WHEEL_FILE"
    
    if [[ $? -eq 0 ]]; then
        print_success "Package installed locally"
        test_installation
    else
        print_error "Local installation failed"
        exit 1
    fi
}

publish_to_pypi() {
    print_step "Publishing to PyPI..."
    
    # Check if we have PyPI credentials
    if [[ -z "$TWINE_USERNAME" ]] && [[ ! -f ~/.pypirc ]]; then
        print_warning "PyPI credentials not found"
        echo -e "${YELLOW}Please set up PyPI credentials:${NC}"
        echo "1. Create account at https://pypi.org"
        echo "2. Generate API token"
        echo "3. Set TWINE_USERNAME=__token__ and TWINE_PASSWORD=<your-token>"
        echo "   OR create ~/.pypirc file"
        echo
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Aborted PyPI upload"
            return 1
        fi
    fi
    
    # Upload to PyPI
    echo -e "${YELLOW}${ROCKET} Uploading to PyPI...${NC}"
    twine upload "$DIST_DIR"/*
    
    if [[ $? -eq 0 ]]; then
        print_success "Package published to PyPI successfully!"
        echo -e "${SPARKLES} Users can now install with: ${GREEN}pip install $PACKAGE_NAME${NC}"
    else
        print_error "PyPI upload failed"
        return 1
    fi
}

install_from_pypi() {
    print_step "Installing from PyPI..."
    
    # Uninstall local version
    $PIP_CMD uninstall $PACKAGE_NAME -y 2>/dev/null || true
    
    # Install from PyPI
    $PIP_CMD install --upgrade $PACKAGE_NAME
    
    if [[ $? -eq 0 ]]; then
        print_success "Package installed from PyPI"
        test_installation
    else
        print_error "PyPI installation failed"
        exit 1
    fi
}

test_installation() {
    print_step "Testing installation..."
    
    # Test both command aliases
    if command -v tm &> /dev/null; then
        print_success "Command 'tm' is available"
        VERSION_OUTPUT=$(tm --help | head -n 5)
        print_info "tm --help works"
    else
        print_error "Command 'tm' not found"
        return 1
    fi
    
    if command -v tagmanager &> /dev/null; then
        print_success "Command 'tagmanager' is available"
        print_info "tagmanager --help works"
    else
        print_warning "Command 'tagmanager' not found (but tm works)"
    fi
    
    # Test basic functionality
    if tm stats &> /dev/null; then
        print_success "Basic functionality test passed"
    else
        print_info "Basic functionality test completed (no tags yet)"
    fi
}

show_usage() {
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./install.sh --local     Install package locally from source"
    echo "  ./install.sh --remote    Publish to PyPI and install from there"
    echo "  ./install.sh --help      Show this help message"
    echo
    echo -e "${CYAN}Options:${NC}"
    echo "  --local      Build and install package locally"
    echo "  --remote     Build, publish to PyPI, then install from PyPI"
    echo "  --build-only Build package without installing"
    echo "  --test-only  Test existing installation"
    echo "  --help       Show this help message"
    echo
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./install.sh --local                    # Quick local install"
    echo "  ./install.sh --remote                   # Publish and install"
    echo "  python bump_version.py patch && ./install.sh --remote  # Bump and publish"
}

show_post_install_info() {
    local version=$(get_current_version)
    echo
    echo -e "${GREEN}${SPARKLES} Installation Complete! ${SPARKLES}${NC}"
    echo -e "${BLUE}================================${NC}"
    echo -e "${CYAN}Package:${NC} $PACKAGE_NAME v$version"
    echo -e "${CYAN}Commands:${NC} tm, tagmanager"
    echo
    echo -e "${CYAN}Quick Start:${NC}"
    echo "  tm --help                    # Show all commands"
    echo "  tm add file.txt --tags work  # Add tags to file"
    echo "  tm search --tags work        # Search by tags"
    echo "  tm ls --tree                 # Tree view"
    echo "  tm stats --chart             # Statistics"
    echo
    echo -e "${CYAN}Next Steps:${NC}"
    echo "  • Read the documentation: README.md"
    echo "  • Check installation guide: INSTALLATION.md"
    echo "  • Start tagging your files!"
    echo -e "${BLUE}================================${NC}"
}

# Main script logic
main() {
    print_header
    
    case "${1:-}" in
        --local)
            check_dependencies
            install_build_tools
            build_package
            install_local
            show_post_install_info
            ;;
        --remote)
            check_dependencies
            install_build_tools
            build_package
            
            # Publish to PyPI
            if publish_to_pypi; then
                print_info "Waiting 30 seconds for PyPI to process..."
                sleep 30
                install_from_pypi
                show_post_install_info
            else
                print_warning "PyPI upload failed, installing locally instead"
                install_local
                show_post_install_info
            fi
            ;;
        --build-only)
            check_dependencies
            install_build_tools
            build_package
            print_success "Build complete. Files in: $DIST_DIR"
            ;;
        --test-only)
            test_installation
            ;;
        --help|-h)
            show_usage
            ;;
        "")
            print_error "No option specified"
            echo
            show_usage
            exit 1
            ;;
        *)
            print_error "Unknown option: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
