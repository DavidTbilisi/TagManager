#!/usr/bin/env python3
"""
PyPI Setup Helper for TagManager

This script helps set up PyPI credentials and configuration for publishing.
"""

import os
import sys
import getpass
from pathlib import Path


def create_pypirc():
    """Create .pypirc file for PyPI authentication"""
    home_dir = Path.home()
    pypirc_path = home_dir / ".pypirc"
    
    print("🔐 PyPI Configuration Setup")
    print("=" * 30)
    print()
    
    if pypirc_path.exists():
        print(f"⚠️  .pypirc already exists at {pypirc_path}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return False
    
    print("Please provide your PyPI credentials:")
    print("(You can get an API token from https://pypi.org/manage/account/token/)")
    print()
    
    # Get credentials
    use_token = input("Use API token? (recommended) (Y/n): ").strip().lower()
    use_token = use_token != 'n'
    
    if use_token:
        username = "__token__"
        password = getpass.getpass("API Token: ").strip()
        if not password:
            print("❌ No token provided")
            return False
    else:
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()
        if not username or not password:
            print("❌ Username and password required")
            return False
    
    # Create .pypirc content
    pypirc_content = f"""[distutils]
index-servers = pypi

[pypi]
username = {username}
password = {password}
"""
    
    try:
        pypirc_path.write_text(pypirc_content)
        # Set secure permissions (Unix-like systems)
        if hasattr(os, 'chmod'):
            os.chmod(pypirc_path, 0o600)
        
        print(f"✅ Created .pypirc at {pypirc_path}")
        print("🔒 File permissions set to 600 (owner read/write only)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .pypirc: {e}")
        return False


def setup_environment_variables():
    """Guide user to set up environment variables"""
    print("\n🌍 Environment Variables Setup")
    print("=" * 30)
    print()
    print("Alternative to .pypirc: Set environment variables")
    print()
    
    use_token = input("Use API token? (recommended) (Y/n): ").strip().lower()
    use_token = use_token != 'n'
    
    if use_token:
        token = getpass.getpass("API Token: ").strip()
        if token:
            print("\n📋 Add these to your shell profile (.bashrc, .zshrc, etc.):")
            print(f"export TWINE_USERNAME=__token__")
            print(f"export TWINE_PASSWORD={token}")
            print()
            print("Or set them temporarily:")
            print(f"TWINE_USERNAME=__token__ TWINE_PASSWORD={token} ./install.sh --remote")
    else:
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()
        if username and password:
            print("\n📋 Add these to your shell profile (.bashrc, .zshrc, etc.):")
            print(f"export TWINE_USERNAME={username}")
            print(f"export TWINE_PASSWORD={password}")


def check_existing_config():
    """Check for existing PyPI configuration"""
    print("🔍 Checking existing PyPI configuration...")
    print()
    
    # Check .pypirc
    pypirc_path = Path.home() / ".pypirc"
    if pypirc_path.exists():
        print(f"✅ Found .pypirc at {pypirc_path}")
        return True
    
    # Check environment variables
    if os.getenv('TWINE_USERNAME') and os.getenv('TWINE_PASSWORD'):
        print("✅ Found TWINE_USERNAME and TWINE_PASSWORD environment variables")
        return True
    
    print("❌ No PyPI configuration found")
    return False


def test_pypi_connection():
    """Test PyPI connection"""
    print("\n🧪 Testing PyPI Connection")
    print("=" * 25)
    
    try:
        import subprocess
        result = subprocess.run(['twine', 'check', '--help'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Twine is available")
        else:
            print("❌ Twine not found. Install with: pip install twine")
            return False
    except FileNotFoundError:
        print("❌ Twine not found. Install with: pip install twine")
        return False
    
    return True


def main():
    print("🚀 TagManager PyPI Setup Helper")
    print("=" * 35)
    print()
    
    # Check if configuration already exists
    if check_existing_config():
        print("\n✅ PyPI configuration already exists!")
        response = input("Reconfigure anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup complete. You can now use ./install.sh --remote")
            return
    
    print("\nChoose configuration method:")
    print("1. Create .pypirc file (recommended)")
    print("2. Set environment variables")
    print("3. Skip configuration")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == '1':
        if create_pypirc():
            print("\n✅ PyPI configuration complete!")
        else:
            print("\n❌ Configuration failed")
            sys.exit(1)
    elif choice == '2':
        setup_environment_variables()
    elif choice == '3':
        print("Skipped configuration.")
    else:
        print("Invalid choice.")
        sys.exit(1)
    
    # Test connection
    if test_pypi_connection():
        print("\n🎉 Setup complete!")
        print("\nNext steps:")
        print("1. Bump version: python bump_version.py patch")
        print("2. Publish: ./install.sh --remote")
    else:
        print("\n⚠️  Setup incomplete. Install twine first.")


if __name__ == "__main__":
    main()
