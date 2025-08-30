#!/usr/bin/env python3
"""
TagManager Version Bumper

Automatically increments version numbers across all project files.
Supports semantic versioning (major.minor.patch).

Usage:
    python bump_version.py patch    # 1.0.0 -> 1.0.1
    python bump_version.py minor    # 1.0.0 -> 1.1.0
    python bump_version.py major    # 1.0.0 -> 2.0.0
    python bump_version.py --current # Show current version
"""

import re
import sys
import argparse
import os
from pathlib import Path
from typing import Tuple, List

# Fix encoding issues on Windows
if sys.platform.startswith('win'):
    # Try to set UTF-8 encoding for Windows
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        # Fallback: disable emojis on Windows if encoding fails
        os.environ['NO_EMOJIS'] = '1'

# Emoji fallbacks for Windows compatibility
def get_emoji(emoji, fallback):
    """Get emoji or fallback text based on platform support"""
    if os.getenv('NO_EMOJIS') or sys.platform.startswith('win'):
        return fallback
    return emoji


class VersionBumper:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.version_files = [
            "pyproject.toml",
            "tagmanager/__init__.py",
        ]
        
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml"""
        pyproject_path = self.project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            raise FileNotFoundError("pyproject.toml not found")
            
        content = pyproject_path.read_text(encoding='utf-8')
        
        # Find version in pyproject.toml
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if not version_match:
            raise ValueError("Version not found in pyproject.toml")
            
        return version_match.group(1)
    
    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string into major, minor, patch tuple"""
        try:
            parts = version.split('.')
            if len(parts) != 3:
                raise ValueError("Version must be in format major.minor.patch")
            return tuple(map(int, parts))
        except ValueError as e:
            raise ValueError(f"Invalid version format '{version}': {e}")
    
    def bump_version(self, current: str, bump_type: str) -> str:
        """Bump version based on type (major, minor, patch)"""
        major, minor, patch = self.parse_version(current)
        
        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        elif bump_type == "patch":
            return f"{major}.{minor}.{patch + 1}"
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")
    
    def update_file_version(self, file_path: Path, old_version: str, new_version: str) -> bool:
        """Update version in a specific file"""
        if not file_path.exists():
            print(f"{get_emoji('⚠️', '[WARNING]')} Warning: {file_path} not found, skipping...")
            return False
            
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Update version patterns
        patterns = [
            # pyproject.toml: version = "1.0.0"
            (r'version\s*=\s*"[^"]+"', f'version = "{new_version}"'),
            # __init__.py: __version__ = "1.0.0"
            (r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"'),
            # Any other exact version matches
            (old_version, new_version),
        ]
        
        for pattern, replacement in patterns:
            if isinstance(pattern, str):
                content = content.replace(pattern, replacement)
            else:
                content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"{get_emoji('✅', '[SUCCESS]')} Updated {file_path}")
            return True
        else:
            print(f"{get_emoji('ℹ️', '[INFO]')} No changes needed in {file_path}")
            return False
    
    def update_all_versions(self, old_version: str, new_version: str) -> List[str]:
        """Update version in all project files"""
        updated_files = []
        
        for file_name in self.version_files:
            file_path = self.project_root / file_name
            if self.update_file_version(file_path, old_version, new_version):
                updated_files.append(str(file_path))
        
        return updated_files
    
    def create_git_tag(self, version: str) -> bool:
        """Create git tag for the new version"""
        import subprocess
        
        try:
            # Check if git is available and we're in a git repo
            subprocess.run(['git', 'status'], 
                         capture_output=True, check=True, cwd=self.project_root)
            
            # Create and push tag
            tag_name = f"v{version}"
            subprocess.run(['git', 'add', '.'], cwd=self.project_root, check=True)
            subprocess.run(['git', 'commit', '-m', f'Bump version to {version}'], 
                         cwd=self.project_root, check=True)
            subprocess.run(['git', 'tag', tag_name], cwd=self.project_root, check=True)
            
            print(f"{get_emoji('🏷️', '[TAG]')} Created git tag: {tag_name}")
            print(f"{get_emoji('💡', '[INFO]')} To push: git push origin main && git push origin {tag_name}")
            return True
            
        except subprocess.CalledProcessError:
            print(f"{get_emoji('⚠️', '[WARNING]')} Git operations failed (not in git repo or git not available)")
            return False
        except FileNotFoundError:
            print(f"{get_emoji('⚠️', '[WARNING]')} Git not found, skipping git operations")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Bump TagManager version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bump_version.py patch     # 1.0.0 -> 1.0.1
  python bump_version.py minor     # 1.0.0 -> 1.1.0  
  python bump_version.py major     # 1.0.0 -> 2.0.0
  python bump_version.py --current # Show current version
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('bump_type', nargs='?', choices=['major', 'minor', 'patch'],
                      help='Type of version bump')
    group.add_argument('--current', action='store_true',
                      help='Show current version')
    
    parser.add_argument('--no-git', action='store_true',
                       help='Skip git operations')
    
    args = parser.parse_args()
    
    bumper = VersionBumper()
    
    try:
        current_version = bumper.get_current_version()
        
        if args.current:
            print(f"{get_emoji('📦', '[PACKAGE]')} Current version: {current_version}")
            return
        
        # Bump version
        new_version = bumper.bump_version(current_version, args.bump_type)
        
        print(f"{get_emoji('🚀', '[RELEASE]')} Bumping version: {current_version} -> {new_version}")
        print("=" * 50)
        
        # Update files
        updated_files = bumper.update_all_versions(current_version, new_version)
        
        if updated_files:
            print(f"\n{get_emoji('✅', '[SUCCESS]')} Successfully updated version to {new_version}")
            print(f"{get_emoji('📝', '[FILES]')} Updated files: {len(updated_files)}")
            
            # Git operations
            if not args.no_git:
                print(f"\n{get_emoji('🔄', '[GIT]')} Git operations:")
                bumper.create_git_tag(new_version)
            
            print(f"\n{get_emoji('🎉', '[COMPLETE]')} Version bump complete!")
            print(f"{get_emoji('💡', '[INFO]')} Next steps:")
            print(f"   1. Run: ./install.sh --local   (to test locally)")
            print(f"   2. Run: ./install.sh --remote  (to publish to PyPI)")
            
        else:
            print(f"{get_emoji('⚠️', '[WARNING]')} No files were updated")
            
    except Exception as e:
        print(f"{get_emoji('❌', '[ERROR]')} Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
