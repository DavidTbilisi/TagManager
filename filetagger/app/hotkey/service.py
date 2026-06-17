"""Global hotkey daemon for FileTagger.

`ftag hotkey run` starts a background process that registers Ctrl+Alt+T as a
system-wide hotkey via Win32 RegisterHotKey. When triggered, it opens a Tk file
picker, then pops the standard tag dialog for each picked file.

`ftag hotkey install` drops a .lnk into the user's Startup folder so the daemon
launches at logon. `ftag hotkey uninstall` removes it.

Implementation notes:
- Uses pure ctypes -> user32.dll. No new third-party deps.
- The message loop runs on the main thread; the file picker and tag dialog
  run on the same thread because Tk is single-threaded.
- The daemon does not lock the keyboard or interfere with games / other
  hotkey owners: RegisterHotKey returns failure if the chord is taken, in
  which case we log and exit cleanly.
"""

import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

HOTKEY_ID = 0x4253  # arbitrary, just needs to be unique within this process
DEFAULT_MOD = "ctrl+alt"
DEFAULT_KEY = "t"

# Modifier flags accepted by RegisterHotKey
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_HOTKEY = 0x0312

SHORTCUT_NAME = "FileTagger Hotkey.lnk"


def _resolve_pythonw() -> str:
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = exe[:-len("python.exe")] + "pythonw.exe"
        if os.path.isfile(candidate):
            return candidate
    return exe


def _parse_modifiers(spec: str) -> int:
    mods = 0
    for part in spec.lower().replace(" ", "").split("+"):
        if part in ("ctrl", "control"):
            mods |= MOD_CONTROL
        elif part == "alt":
            mods |= MOD_ALT
        elif part == "shift":
            mods |= MOD_SHIFT
        elif part in ("win", "super", "meta"):
            mods |= MOD_WIN
        elif part:
            raise ValueError(f"Unknown modifier: {part}")
    return mods


def _vk_for(key: str) -> int:
    """Map a single-character key spec to a Win32 virtual-key code."""
    key = key.strip()
    if len(key) != 1:
        raise ValueError(f"Hotkey key must be a single character, got {key!r}")
    return ord(key.upper())


def _pick_files() -> List[str]:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except tk.TclError:
        pass
    try:
        paths = filedialog.askopenfilenames(
            title="FileTagger — pick files to tag",
        )
    finally:
        root.destroy()
    return list(paths or [])


def _tag_each(paths: List[str]) -> None:
    from ..shell.service import tag_path_interactively

    for p in paths:
        tag_path_interactively(p)


# ---------------------------------------------------------------------------
# Daemon loop
# ---------------------------------------------------------------------------


def run_daemon(modifiers: str = DEFAULT_MOD, key: str = DEFAULT_KEY) -> int:
    """Block on the Win32 message loop, dispatching the hotkey."""
    if not sys.platform.startswith("win"):
        print("Hotkey daemon is only supported on Windows.", file=sys.stderr)
        return 1

    user32 = ctypes.windll.user32

    mods = _parse_modifiers(modifiers) | MOD_NOREPEAT
    vk = _vk_for(key)

    if not user32.RegisterHotKey(None, HOTKEY_ID, mods, vk):
        err = ctypes.GetLastError()
        print(
            f"RegisterHotKey failed (Win32 error {err}). "
            "Another application may already own this chord.",
            file=sys.stderr,
        )
        return 2

    print(f"FileTagger hotkey daemon listening on {modifiers}+{key}. Ctrl+C to quit.")
    msg = wt.MSG()
    try:
        while True:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                try:
                    paths = _pick_files()
                except Exception as exc:
                    print(f"File picker failed: {exc}", file=sys.stderr)
                    continue
                if paths:
                    _tag_each(paths)
            else:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        user32.UnregisterHotKey(None, HOTKEY_ID)
    return 0


# ---------------------------------------------------------------------------
# Startup-folder autostart installer
# ---------------------------------------------------------------------------


def _startup_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA env var is not set; cannot locate Startup folder.")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _shortcut_path() -> Path:
    return _startup_dir() / SHORTCUT_NAME


def _create_shortcut(target_lnk: Path, target_exe: str, args: str) -> None:
    ps_script = (
        "$WScriptShell = New-Object -ComObject WScript.Shell; "
        f"$lnk = $WScriptShell.CreateShortcut('{target_lnk}'); "
        f"$lnk.TargetPath = '{target_exe}'; "
        f"$lnk.Arguments  = '{args}'; "
        "$lnk.WindowStyle = 7; "  # 7 = minimized
        "$lnk.Description = 'FileTagger global hotkey daemon'; "
        "$lnk.Save();"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        check=True,
        capture_output=True,
        text=True,
    )


def install_autostart(modifiers: str = DEFAULT_MOD, key: str = DEFAULT_KEY) -> Dict[str, object]:
    if not sys.platform.startswith("win"):
        return {"success": False, "message": "Hotkey integration is only available on Windows."}
    try:
        startup = _startup_dir()
        startup.mkdir(parents=True, exist_ok=True)
    except (OSError, RuntimeError) as exc:
        return {"success": False, "message": f"Cannot access Startup folder: {exc}"}

    target = _shortcut_path()
    pythonw = _resolve_pythonw()
    args = f"-m filetagger hotkey run --modifiers \"{modifiers}\" --key \"{key}\""

    try:
        _create_shortcut(target, pythonw, args)
    except subprocess.CalledProcessError as exc:
        return {
            "success": False,
            "message": f"PowerShell failed to create shortcut: {exc.stderr or exc.stdout}",
        }
    return {
        "success": True,
        "message": (
            f"Installed hotkey daemon to start at logon:\n  {target}\n"
            f"Trigger:  {modifiers}+{key}\n"
            "Run `ftag hotkey run` to start it now without logging out."
        ),
        "shortcut": str(target),
    }


def uninstall_autostart() -> Dict[str, object]:
    if not sys.platform.startswith("win"):
        return {"success": False, "message": "Hotkey integration is only available on Windows."}
    target = _shortcut_path()
    if not target.exists():
        return {"success": True, "message": "Hotkey autostart was not installed."}
    try:
        target.unlink()
    except OSError as exc:
        return {"success": False, "message": f"Failed to remove {target}: {exc}"}
    return {"success": True, "message": f"Removed {target}."}


def autostart_status() -> Dict[str, object]:
    if not sys.platform.startswith("win"):
        return {"installed": False, "platform_supported": False}
    target = _shortcut_path()
    return {
        "installed": target.exists(),
        "platform_supported": True,
        "shortcut": str(target),
    }
