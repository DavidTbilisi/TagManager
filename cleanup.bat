@echo off
REM FileTagger Project Cleanup Script (Windows)
REM Removes unused files and folders to keep the project clean

echo 🧹 FileTagger Project Cleanup
echo =============================

echo.
echo 📁 Removing legacy files...

REM Legacy main CLI file
if exist "tm.py" (
    echo 🗑️  Removing: tm.py
    del "tm.py"
) else (
    echo ℹ️  Not found: tm.py
)

REM Legacy configuration files
if exist "config.ini" (
    echo 🗑️  Removing: config.ini
    del "config.ini"
) else (
    echo ℹ️  Not found: config.ini
)

if exist "configReader.py" (
    echo 🗑️  Removing: configReader.py
    del "configReader.py"
) else (
    echo ℹ️  Not found: configReader.py
)

if exist "configWriter.py" (
    echo 🗑️  Removing: configWriter.py
    del "configWriter.py"
) else (
    echo ℹ️  Not found: configWriter.py
)

REM Test configuration files
if exist "not_test_config.ini" (
    echo 🗑️  Removing: not_test_config.ini
    del "not_test_config.ini"
) else (
    echo ℹ️  Not found: not_test_config.ini
)

if exist "test_config.json" (
    echo 🗑️  Removing: test_config.json
    del "test_config.json"
) else (
    echo ℹ️  Not found: test_config.json
)

REM Old batch files
if exist "tm.bat" (
    echo 🗑️  Removing: tm.bat
    del "tm.bat"
) else (
    echo ℹ️  Not found: tm.bat
)

if exist "tm" (
    echo 🗑️  Removing: tm
    del "tm"
) else (
    echo ℹ️  Not found: tm
)

REM Test files
if exist "tests" (
    echo 🗑️  Removing: tests/
    rmdir /s /q "tests"
) else (
    echo ℹ️  Not found: tests/
)

if exist "tests.py" (
    echo 🗑️  Removing: tests.py
    del "tests.py"
) else (
    echo ℹ️  Not found: tests.py
)

echo.
echo 🏗️  Removing build artifacts...

REM Python cache directories
if exist "__pycache__" (
    echo 🗑️  Removing: __pycache__/
    rmdir /s /q "__pycache__"
) else (
    echo ℹ️  Not found: __pycache__/
)

if exist "filetagger\app\__pycache__" (
    echo 🗑️  Removing: filetagger\app\__pycache__/
    rmdir /s /q "filetagger\app\__pycache__"
) else (
    echo ℹ️  Not found: filetagger\app\__pycache__/
)

REM Remove all __pycache__ directories in filetagger/app subdirectories
for /d /r "filetagger\app" %%d in (__pycache__) do (
    if exist "%%d" (
        echo 🗑️  Removing: %%d
        rmdir /s /q "%%d"
    )
)

REM Build artifacts
if exist "filetagger_cli.egg-info" (
    echo 🗑️  Removing: filetagger_cli.egg-info/
    rmdir /s /q "filetagger_cli.egg-info"
) else (
    echo ℹ️  Not found: filetagger_cli.egg-info/
)

if exist "dist" (
    echo 🗑️  Removing: dist/
    rmdir /s /q "dist"
) else (
    echo ℹ️  Not found: dist/
)

if exist "build" (
    echo 🗑️  Removing: build/
    rmdir /s /q "build"
) else (
    echo ℹ️  Not found: build/
)

echo.
echo 🤔 Optional removals (you decide):
echo    • venv\ - Virtual environment (can be recreated)
echo    • .git\ - Git repository (only if you don't need version history)

echo.
echo ✅ Cleanup complete!
echo.
echo 📋 Remaining important files:
echo    • filetagger\ - Main package directory
echo    • pyproject.toml - Package configuration
echo    • requirements.txt - Dependencies
echo    • README.md - Documentation
echo    • LICENSE - License file
echo    • MANIFEST.in - Package manifest
echo    • *.md - Documentation files
echo    • *.sh, *.py - Automation scripts
echo.
echo 🚀 Your project is now clean and ready for distribution!
pause
