#!/bin/bash

# TagManager Release Workflow
# Complete automation for version bumping, building, and publishing

set -e

# Colors and emojis
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

ROCKET="🚀"
PACKAGE="📦"
CHECK="✅"
WARNING="⚠️"
ERROR="❌"
INFO="ℹ️"
SPARKLES="✨"
GEAR="⚙️"
TAG="🏷️"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  TagManager Release Workflow${NC}"
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

show_usage() {
    echo -e "${CYAN}Usage:${NC}"
    echo "  ./release.sh <bump_type> [options]"
    echo
    echo -e "${CYAN}Bump Types:${NC}"
    echo "  patch    Increment patch version (1.0.0 -> 1.0.1)"
    echo "  minor    Increment minor version (1.0.0 -> 1.1.0)"
    echo "  major    Increment major version (1.0.0 -> 2.0.0)"
    echo
    echo -e "${CYAN}Options:${NC}"
    echo "  --local-only    Only install locally (skip PyPI)"
    echo "  --dry-run       Show what would be done without executing"
    echo "  --skip-tests    Skip running tests"
    echo "  --help          Show this help message"
    echo
    echo -e "${CYAN}Examples:${NC}"
    echo "  ./release.sh patch              # Patch release to PyPI"
    echo "  ./release.sh minor --local-only # Minor release, local only"
    echo "  ./release.sh major --dry-run    # Show what major release would do"
}

run_tests() {
    print_step "Running tests..."
    
    if [[ -f "tests.py" ]]; then
        python -m unittest tests.py -v
        if [[ $? -eq 0 ]]; then
            print_success "All tests passed"
        else
            print_error "Tests failed"
            exit 1
        fi
    else
        print_info "No tests.py found, skipping tests"
    fi
}

check_git_status() {
    print_step "Checking git status..."
    
    if ! git status &>/dev/null; then
        print_warning "Not in a git repository"
        return 0
    fi
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_warning "You have uncommitted changes:"
        git status --porcelain
        echo
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Aborted. Please commit your changes first."
            exit 1
        fi
    else
        print_success "Working directory is clean"
    fi
}

bump_version() {
    local bump_type=$1
    local dry_run=$2
    
    print_step "Bumping version ($bump_type)..."
    
    if [[ "$dry_run" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would run: python bump_version.py $bump_type"
        return 0
    fi
    
    python bump_version.py "$bump_type"
    
    if [[ $? -eq 0 ]]; then
        NEW_VERSION=$(python bump_version.py --current)
        print_success "Version bumped to $NEW_VERSION"
        echo "NEW_VERSION=$NEW_VERSION" > .release_version
    else
        print_error "Version bump failed"
        exit 1
    fi
}

install_package() {
    local install_type=$1
    local dry_run=$2
    
    if [[ "$dry_run" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would run: ./install.sh $install_type"
        return 0
    fi
    
    ./install.sh "$install_type"
}

create_github_release() {
    local version=$1
    local dry_run=$2
    
    print_step "Creating GitHub release..."
    
    if [[ "$dry_run" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would create GitHub release for v$version"
        return 0
    fi
    
    if command -v gh &> /dev/null; then
        # Create release notes
        cat > release_notes.md << EOF
# TagManager v$version

## What's New
- Version $version release
- See CHANGELOG.md for detailed changes

## Installation
\`\`\`bash
pip install tagmanager-cli
\`\`\`

## Quick Start
\`\`\`bash
tm add file.txt --tags work important
tm search --tags work
tm ls --tree
\`\`\`
EOF
        
        gh release create "v$version" \
            --title "TagManager v$version" \
            --notes-file release_notes.md \
            dist/*
        
        rm release_notes.md
        print_success "GitHub release created"
    else
        print_info "GitHub CLI not found, skipping GitHub release"
        print_info "You can create a release manually at: https://github.com/davidtbilisi/TagManager/releases"
    fi
}

main() {
    print_header
    
    # Parse arguments
    BUMP_TYPE=""
    LOCAL_ONLY=false
    DRY_RUN=false
    SKIP_TESTS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            patch|minor|major)
                BUMP_TYPE=$1
                shift
                ;;
            --local-only)
                LOCAL_ONLY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Validate bump type
    if [[ -z "$BUMP_TYPE" ]]; then
        print_error "Bump type required (patch, minor, or major)"
        show_usage
        exit 1
    fi
    
    # Show what we're going to do
    echo -e "${CYAN}Release Plan:${NC}"
    echo "  Bump Type: $BUMP_TYPE"
    echo "  Target: $([ "$LOCAL_ONLY" = true ] && echo "Local only" || echo "PyPI + Local")"
    echo "  Mode: $([ "$DRY_RUN" = true ] && echo "Dry run" || echo "Execute")"
    echo "  Tests: $([ "$SKIP_TESTS" = true ] && echo "Skip" || echo "Run")"
    echo
    
    if [[ "$DRY_RUN" = false ]]; then
        read -p "Continue with release? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            print_info "Release cancelled"
            exit 0
        fi
    fi
    
    echo -e "${ROCKET} Starting release process..."
    echo
    
    # Step 1: Check git status
    if [[ "$DRY_RUN" = false ]]; then
        check_git_status
    fi
    
    # Step 2: Run tests
    if [[ "$SKIP_TESTS" = false && "$DRY_RUN" = false ]]; then
        run_tests
    fi
    
    # Step 3: Bump version
    bump_version "$BUMP_TYPE" "$DRY_RUN"
    
    # Get version for later steps
    if [[ -f ".release_version" ]]; then
        source .release_version
        rm .release_version
    else
        NEW_VERSION="unknown"
    fi
    
    # Step 4: Install package
    if [[ "$LOCAL_ONLY" = true ]]; then
        install_package "--local" "$DRY_RUN"
    else
        install_package "--remote" "$DRY_RUN"
    fi
    
    # Step 5: Create GitHub release (if publishing to PyPI)
    if [[ "$LOCAL_ONLY" = false ]]; then
        create_github_release "$NEW_VERSION" "$DRY_RUN"
    fi
    
    # Success message
    echo
    echo -e "${GREEN}${SPARKLES} Release Complete! ${SPARKLES}${NC}"
    echo -e "${BLUE}================================${NC}"
    
    if [[ "$DRY_RUN" = false ]]; then
        echo -e "${CYAN}Version:${NC} $NEW_VERSION"
        echo -e "${CYAN}Status:${NC} $([ "$LOCAL_ONLY" = true ] && echo "Local installation" || echo "Published to PyPI")"
        echo
        echo -e "${CYAN}Next Steps:${NC}"
        if [[ "$LOCAL_ONLY" = false ]]; then
            echo "  • Check PyPI: https://pypi.org/project/tagmanager-cli/"
            echo "  • Verify installation: pip install --upgrade tagmanager-cli"
        fi
        echo "  • Test the release: tm --help"
        echo "  • Update documentation if needed"
    else
        echo "This was a dry run. No changes were made."
    fi
    
    echo -e "${BLUE}================================${NC}"
}

# Run main function
main "$@"
