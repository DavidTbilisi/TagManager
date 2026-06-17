@echo off
REM FileTagger Installation Script for Windows
REM Supports local and remote (PyPI) installation with automatic upgrades

setlocal enabledelayedexpansion

REM Configuration
set PACKAGE_NAME=filetagger-cli
set PROJECT_DIR=%~dp0
set DIST_DIR=%PROJECT_DIR%dist
set PYPROJECT_FILE=%PROJECT_DIR%pyproject.toml

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    exit /b 1
)

REM Main logic
if "%1"=="--local" goto local_install
if "%1"=="--remote" goto remote_install
if "%1"=="--help" goto show_help
if "%1"=="-h" goto show_help
if "%1"=="--build-only" goto build_only
if "%1"=="--test-only" goto test_only

echo ❌ No option specified
echo.
goto show_help

:local_install
echo 🚀 FileTagger Local Installation
echo ================================
echo.
echo ⚙️ Installing build tools...
python -m pip install --upgrade pip build twine
echo.
echo ⚙️ Building package...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
python -m build
if %errorlevel% neq 0 (
    echo ❌ Package build failed
    exit /b 1
)
echo.
echo ⚙️ Installing package locally...
python -m pip uninstall %PACKAGE_NAME% -y >nul 2>&1
for %%f in ("%DIST_DIR%\*.whl") do (
    python -m pip install "%%f"
    if !errorlevel! equ 0 (
        echo ✅ Package installed locally
        goto test_install
    ) else (
        echo ❌ Local installation failed
        exit /b 1
    )
)
echo ❌ No wheel file found
exit /b 1

:remote_install
echo 🚀 FileTagger Remote Installation (PyPI)
echo ========================================
echo.
echo ⚙️ Installing build tools...
python -m pip install --upgrade pip build twine
echo.
echo ⚙️ Building package...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
python -m build
if %errorlevel% neq 0 (
    echo ❌ Package build failed
    exit /b 1
)
echo.
echo ⚙️ Publishing to PyPI...
echo ⚠️ Make sure you have PyPI credentials configured
twine upload "%DIST_DIR%\*"
if %errorlevel% neq 0 (
    echo ⚠️ PyPI upload failed, installing locally instead
    goto local_install_fallback
)
echo.
echo ⚙️ Waiting for PyPI to process...
timeout /t 30 /nobreak >nul
echo.
echo ⚙️ Installing from PyPI...
python -m pip uninstall %PACKAGE_NAME% -y >nul 2>&1
python -m pip install --upgrade %PACKAGE_NAME%
if %errorlevel% equ 0 (
    echo ✅ Package installed from PyPI
    goto test_install
) else (
    echo ❌ PyPI installation failed
    exit /b 1
)

:local_install_fallback
echo ⚙️ Installing package locally (fallback)...
python -m pip uninstall %PACKAGE_NAME% -y >nul 2>&1
for %%f in ("%DIST_DIR%\*.whl") do (
    python -m pip install "%%f"
    goto test_install
)

:build_only
echo 🚀 FileTagger Build Only
echo =======================
echo.
echo ⚙️ Installing build tools...
python -m pip install --upgrade pip build twine
echo.
echo ⚙️ Building package...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
python -m build
if %errorlevel% equ 0 (
    echo ✅ Build complete. Files in: %DIST_DIR%
    dir "%DIST_DIR%"
) else (
    echo ❌ Package build failed
    exit /b 1
)
goto end

:test_only
goto test_install

:test_install
echo.
echo ⚙️ Testing installation...
tm --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Command 'tm' is available
) else (
    echo ❌ Command 'tm' not found
    exit /b 1
)

filetagger --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Command 'filetagger' is available
) else (
    echo ⚠️ Command 'filetagger' not found (but tm works)
)

echo.
echo ✨ Installation Complete! ✨
echo ================================
echo Package: %PACKAGE_NAME%
echo Commands: tm, filetagger
echo.
echo Quick Start:
echo   tm --help                    # Show all commands
echo   tm add file.txt --tags work  # Add tags to file
echo   tm search --tags work        # Search by tags
echo   tm ls --tree                 # Tree view
echo   tm stats --chart             # Statistics
echo.
echo Next Steps:
echo   • Read the documentation: README.md
echo   • Check installation guide: INSTALLATION.md
echo   • Start tagging your files!
echo ================================
goto end

:show_help
echo Usage:
echo   install.bat --local     Install package locally from source
echo   install.bat --remote    Publish to PyPI and install from there
echo   install.bat --help      Show this help message
echo.
echo Options:
echo   --local      Build and install package locally
echo   --remote     Build, publish to PyPI, then install from PyPI
echo   --build-only Build package without installing
echo   --test-only  Test existing installation
echo   --help       Show this help message
echo.
echo Examples:
echo   install.bat --local                                      # Quick local install
echo   install.bat --remote                                     # Publish and install
echo   python bump_version.py patch ^&^& install.bat --remote   # Bump and publish

:end
pause
