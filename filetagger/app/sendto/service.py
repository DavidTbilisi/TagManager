"""Windows 'Send to' menu integration for FileTagger.

Drops a .lnk shortcut into %APPDATA%\\Microsoft\\Windows\\SendTo so the user
can right-click any file or folder in Explorer and pick
  Send to -> Tag with FileTagger.

This uses the SendTo mechanism that Windows itself owns; Win11's shell-extension
filters do not apply to it, so this works on every Windows 7+ build without a
DLL, MSIX package, or admin elevation.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict

SHORTCUT_NAME = "Tag with FileTagger.lnk"


def _sendto_dir() -> Path:
    """Return %APPDATA%\\Microsoft\\Windows\\SendTo."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA env var is not set; cannot locate SendTo folder.")
    return Path(appdata) / "Microsoft" / "Windows" / "SendTo"


def _resolve_pythonw() -> str:
    """Best-effort path to a pythonw.exe that owns the filetagger package."""
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = exe[:-len("python.exe")] + "pythonw.exe"
        if os.path.isfile(candidate):
            return candidate
    return exe


def shortcut_path() -> Path:
    return _sendto_dir() / SHORTCUT_NAME


def _icon_path() -> str:
    """Pick a sensible icon — use python.exe so the menu entry gets a snake."""
    icon = sys.executable
    if icon.lower().endswith("pythonw.exe"):
        candidate = icon[:-len("pythonw.exe")] + "python.exe"
        if os.path.isfile(candidate):
            return candidate
    return icon


def _create_shortcut(target_lnk: Path, target_exe: str, args: str, icon: str) -> None:
    """Drive WScript.Shell from PowerShell to create the .lnk.

    Using PowerShell avoids adding pywin32/comtypes as a runtime dependency.
    """
    ps_script = (
        "$WScriptShell = New-Object -ComObject WScript.Shell; "
        f"$lnk = $WScriptShell.CreateShortcut('{target_lnk}'); "
        f"$lnk.TargetPath = '{target_exe}'; "
        f"$lnk.Arguments  = '{args}'; "
        f"$lnk.IconLocation = '{icon}'; "
        "$lnk.WorkingDirectory = ''; "
        "$lnk.Description = 'Add tags to the selected file with FileTagger'; "
        "$lnk.Save();"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        check=True,
        capture_output=True,
        text=True,
    )


def install() -> Dict[str, object]:
    """Create the Send to shortcut."""
    if not sys.platform.startswith("win"):
        return {"success": False, "message": "Send to integration is only available on Windows."}

    try:
        sendto = _sendto_dir()
        sendto.mkdir(parents=True, exist_ok=True)
    except (OSError, RuntimeError) as exc:
        return {"success": False, "message": f"Cannot access SendTo folder: {exc}"}

    target = shortcut_path()
    pythonw = _resolve_pythonw()
    args = "-m filetagger shell tag"

    try:
        _create_shortcut(target, pythonw, args, _icon_path())
    except subprocess.CalledProcessError as exc:
        return {
            "success": False,
            "message": f"PowerShell failed to create shortcut: {exc.stderr or exc.stdout}",
        }
    except OSError as exc:
        return {"success": False, "message": f"Failed to write shortcut: {exc}"}

    return {
        "success": True,
        "message": (
            f"Installed Send to entry:\n  {target}\n"
            f"Right-click a file in Explorer -> Send to -> Tag with FileTagger."
        ),
        "shortcut": str(target),
    }


def uninstall() -> Dict[str, object]:
    """Remove the Send to shortcut."""
    if not sys.platform.startswith("win"):
        return {"success": False, "message": "Send to integration is only available on Windows."}

    target = shortcut_path()
    if not target.exists():
        return {"success": True, "message": "Send to entry was not installed."}
    try:
        target.unlink()
    except OSError as exc:
        return {"success": False, "message": f"Failed to remove {target}: {exc}"}
    return {"success": True, "message": f"Removed {target}."}


def status() -> Dict[str, object]:
    """Report whether the Send to shortcut is in place."""
    if not sys.platform.startswith("win"):
        return {"installed": False, "platform_supported": False}
    target = shortcut_path()
    return {
        "installed": target.exists(),
        "platform_supported": True,
        "shortcut": str(target),
    }
