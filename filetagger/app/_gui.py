"""Shared Tk theming + tag-store helpers used by all FileTagger dialogs.

All UI code (shell/service.py, config/gui.py, ...) goes through these helpers
so the dialogs stay visually consistent. Bumping a colour here changes every
window in the app at once.

Public surface:
    is_dark_mode() -> bool
    palette(dark: bool) -> dict[str, str]
    pick_font_family(root) -> str
    apply_theme(root, pal, font_family) -> None
    apply_icon(root) -> None
    all_known_tags() -> list[str]
    tag_usage_counts() -> dict[str, int]
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------


def is_dark_mode() -> bool:
    """Best-effort dark-mode probe. Currently Windows-only; other OSes get light."""
    if not sys.platform.startswith("win"):
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as k:
            apps_use_light, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
            return apps_use_light == 0
    except Exception:
        return False


def palette(dark: bool) -> Dict[str, str]:
    """Return a coordinated colour palette. Tweaks here propagate everywhere."""
    if dark:
        return {
            "bg":           "#202020",
            "surface":      "#2b2b2b",
            "surface_alt":  "#333333",
            "fg":           "#f1f1f1",
            "fg_muted":     "#a8a8a8",
            "fg_subtle":    "#7a7a7a",
            "accent":       "#4cc2ff",
            "accent_fg":    "#0a1014",
            "accent_hov":   "#62caff",
            "chip_bg":      "#1f3a52",
            "chip_bg_hov":  "#27496a",
            "chip_fg":      "#cfe6ff",
            "chip_border":  "#3b5d80",
            "sugg_bg":      "#2f2f2f",
            "sugg_bg_hov":  "#3a3a3a",
            "sugg_fg":      "#d0d0d0",
            "sugg_border":  "#454545",
            "danger":       "#ff8a87",
            "success":      "#7bd88f",
            "entry_bg":     "#1a1a1a",
            "entry_fg":     "#f1f1f1",
            "border":       "#3a3a3a",
        }
    return {
        "bg":           "#f5f6f8",
        "surface":      "#ffffff",
        "surface_alt":  "#f0f1f4",
        "fg":           "#1c1c1c",
        "fg_muted":     "#5a6473",
        "fg_subtle":    "#8a93a3",
        "accent":       "#0067c0",
        "accent_fg":    "#ffffff",
        "accent_hov":   "#1a78cc",
        "chip_bg":      "#e6efff",
        "chip_bg_hov":  "#d6e4ff",
        "chip_fg":      "#1f3b66",
        "chip_border":  "#b8ccea",
        "sugg_bg":      "#f0f2f5",
        "sugg_bg_hov":  "#e4e7ec",
        "sugg_fg":      "#1c1c1c",
        "sugg_border":  "#d6dae1",
        "danger":       "#b3261e",
        "success":      "#1e7d34",
        "entry_bg":     "#ffffff",
        "entry_fg":     "#1c1c1c",
        "border":       "#dcdfe5",
    }


def pick_font_family(root) -> str:
    """Prefer Segoe UI Variable (Win11) → Segoe UI (Win10) → Inter → defaults."""
    try:
        import tkinter.font as tkfont

        families = set(tkfont.families(root))
    except Exception:
        return "TkDefaultFont"
    for candidate in ("Segoe UI Variable", "Segoe UI", "Inter", "Helvetica"):
        if candidate in families:
            return candidate
    return "TkDefaultFont"


def apply_theme(root, pal: Dict[str, str], font_family: str) -> None:
    """Style root + ttk widgets. Tries sv-ttk first; falls back to manual."""
    import tkinter as tk
    from tkinter import ttk

    root.configure(background=pal["bg"])

    sv_loaded = False
    try:
        import sv_ttk  # type: ignore

        sv_ttk.set_theme("dark" if pal["bg"].startswith("#2") else "light")
        sv_loaded = True
    except Exception:
        pass

    style = ttk.Style(root)
    if not sv_loaded:
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    base_font = (font_family, 10)
    bold_font = (font_family, 10, "bold")
    title_font = (font_family, 13, "bold")
    mono_font = ("Consolas" if sys.platform.startswith("win") else "TkFixedFont", 9)

    style.configure(".", background=pal["bg"], foreground=pal["fg"], font=base_font)
    style.configure("TFrame", background=pal["bg"])
    style.configure("Card.TFrame", background=pal["surface"])
    style.configure("TLabel", background=pal["bg"], foreground=pal["fg"], font=base_font)
    style.configure(
        "Title.TLabel", background=pal["bg"], foreground=pal["fg"], font=title_font
    )
    style.configure(
        "Muted.TLabel", background=pal["bg"], foreground=pal["fg_muted"], font=base_font
    )
    style.configure(
        "Subtle.TLabel", background=pal["bg"], foreground=pal["fg_subtle"], font=base_font
    )
    style.configure(
        "Path.TLabel",
        background=pal["surface"], foreground=pal["fg_muted"], font=mono_font,
        padding=(8, 4),
    )
    style.configure(
        "SectionHeader.TLabel",
        background=pal["bg"], foreground=pal["fg_muted"], font=bold_font,
    )
    style.configure(
        "Danger.TLabel", background=pal["bg"], foreground=pal["danger"], font=base_font
    )
    style.configure(
        "Success.TLabel", background=pal["bg"], foreground=pal["success"], font=base_font
    )

    if not sv_loaded:
        style.configure(
            "TEntry",
            fieldbackground=pal["entry_bg"], foreground=pal["entry_fg"],
            bordercolor=pal["border"], lightcolor=pal["border"], darkcolor=pal["border"],
            padding=6,
        )
        style.configure(
            "TButton",
            background=pal["surface"], foreground=pal["fg"], padding=(14, 6),
            bordercolor=pal["border"], focusthickness=0,
        )
        style.map(
            "TButton",
            background=[("active", pal["chip_bg"])],
            bordercolor=[("focus", pal["accent"])],
        )
        style.configure(
            "Accent.TButton",
            background=pal["accent"], foreground=pal["accent_fg"], padding=(16, 6),
            bordercolor=pal["accent"], focusthickness=0, font=bold_font,
        )
        style.map(
            "Accent.TButton",
            background=[("active", pal["accent_hov"]), ("pressed", pal["accent_hov"])],
            foreground=[("active", pal["accent_fg"])],
        )
        style.configure(
            "TCheckbutton",
            background=pal["bg"], foreground=pal["fg"],
            focuscolor=pal["bg"], indicatorbackground=pal["entry_bg"],
            indicatorforeground=pal["accent"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=pal["entry_bg"], foreground=pal["entry_fg"],
            background=pal["surface"], bordercolor=pal["border"], padding=6,
            arrowcolor=pal["fg"],
            insertcolor=pal["fg"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", pal["entry_bg"])],
            foreground=[("readonly", pal["fg"])],
            bordercolor=[("focus", pal["accent"])],
        )
        style.configure(
            "TSpinbox",
            fieldbackground=pal["entry_bg"], foreground=pal["entry_fg"],
            background=pal["surface"], bordercolor=pal["border"], padding=6,
            arrowcolor=pal["fg"],
            insertcolor=pal["fg"],
        )
        style.map(
            "TSpinbox",
            bordercolor=[("focus", pal["accent"])],
        )
        # Notebook (settings tabs)
        style.configure(
            "TNotebook",
            background=pal["bg"], borderwidth=0, tabmargins=(0, 4, 0, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=pal["bg"], foreground=pal["fg_muted"],
            padding=(16, 8), borderwidth=0, font=bold_font,
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", pal["surface_alt"]),
                ("active",   pal["surface_alt"]),
            ],
            foreground=[
                ("selected", pal["accent"]),
                ("active",   pal["fg"]),
            ],
        )
        # Vertical scrollbar (used by settings list)
        style.configure(
            "Vertical.TScrollbar",
            background=pal["surface_alt"], troughcolor=pal["bg"],
            bordercolor=pal["bg"], arrowcolor=pal["fg_muted"],
            relief="flat", borderwidth=0, gripcount=0, arrowsize=14,
        )
        style.map(
            "Vertical.TScrollbar",
            background=[("active", pal["border"])],
        )


def apply_icon(root) -> None:
    """Apply the FileTagger tag icon to a Tk root. Silent on failure."""
    import tkinter as tk

    from ._assets import ICON_ICO, ICON_PNG

    # iconbitmap (.ico) is the *only* way to get the title-bar icon to show up
    # in a non-default colour on Windows. iconphoto also affects the taskbar.
    if ICON_ICO.is_file():
        try:
            root.iconbitmap(default=str(ICON_ICO))
        except tk.TclError:
            pass
    if ICON_PNG.is_file():
        try:
            img = tk.PhotoImage(file=str(ICON_PNG))
            # Hold a reference on the root so Tk doesn't garbage-collect it
            root._filetagger_icon_ref = img  # type: ignore[attr-defined]
            root.iconphoto(False, img)
        except tk.TclError:
            pass


class ToggleSwitch:
    """A canvas-drawn iOS/Win11-style toggle switch with optional On/Off label.

    Why a custom widget: ttk.Checkbutton under the `clam` theme renders as a
    cramped square with an X glyph — looks dated and noisy. A canvas-drawn
    pill matches the rest of the chrome and reads clearly at a glance.

    Use `pack_with_label()` to get a Frame containing the switch + a styled
    "On"/"Off" label to the left (Twinkle-Tray style).
    """

    WIDTH = 44
    HEIGHT = 22
    PAD = 3

    def __init__(self, parent, variable, palette_, command=None):
        import tkinter as tk

        self._tk = tk
        self._pal = palette_
        self._var = variable
        self._command = command
        self._parent = parent
        self._bg = parent.cget("background")
        self._label: Optional["tk.Label"] = None
        self._font: Optional[tuple] = None

        self.widget = tk.Canvas(
            parent,
            width=self.WIDTH, height=self.HEIGHT,
            background=self._bg,
            highlightthickness=0, borderwidth=0, cursor="hand2",
        )
        self.widget.bind("<Button-1>", self._toggle)
        self.widget.bind("<space>", self._toggle)
        variable.trace_add("write", lambda *_: self._redraw())
        self._redraw()

    def pack_with_label(self, label_font: tuple) -> "object":
        """Build a Frame containing 'On'/'Off' text + the switch. Returns the Frame.

        Caller still packs the returned Frame wherever it wants. The original
        canvas built in __init__ is destroyed — we rebuild inside the wrapper
        so geometry sits cleanly on one row.
        """
        tk = self._tk
        # Discard the canvas built in __init__; it was never packed by us.
        try:
            self.widget.destroy()
        except Exception:
            pass

        wrapper = tk.Frame(self._parent, background=self._bg)
        self._font = label_font
        self._label = tk.Label(
            wrapper, background=self._bg, foreground=self._pal["fg_muted"],
            font=label_font, width=3, anchor="e",
        )
        self._label.pack(side="left", padx=(0, 8))
        self.widget = tk.Canvas(
            wrapper,
            width=self.WIDTH, height=self.HEIGHT,
            background=self._bg,
            highlightthickness=0, borderwidth=0, cursor="hand2",
        )
        self.widget.bind("<Button-1>", self._toggle)
        self.widget.bind("<space>", self._toggle)
        self.widget.pack(side="left")
        self._redraw()
        return wrapper

    def _toggle(self, _event=None):
        self._var.set(not bool(self._var.get()))
        if self._command:
            try:
                self._command()
            except Exception:
                pass

    def _redraw(self):
        c = self.widget
        c.delete("all")
        on = bool(self._var.get())
        r = self.HEIGHT // 2 - 1
        track_color = self._pal["accent"] if on else self._pal["border"]
        c.create_oval(0, 0, self.HEIGHT - 1, self.HEIGHT - 1, fill=track_color, outline=track_color)
        c.create_oval(self.WIDTH - self.HEIGHT, 0, self.WIDTH - 1, self.HEIGHT - 1,
                      fill=track_color, outline=track_color)
        c.create_rectangle(r, 0, self.WIDTH - r - 1, self.HEIGHT - 1,
                           fill=track_color, outline=track_color)
        knob_size = self.HEIGHT - self.PAD * 2
        knob_color = self._pal["accent_fg"] if on else self._pal["fg_muted"]
        if on:
            x0 = self.WIDTH - self.PAD - knob_size
        else:
            x0 = self.PAD
        c.create_oval(x0, self.PAD, x0 + knob_size, self.PAD + knob_size,
                      fill=knob_color, outline=knob_color)
        if self._label is not None:
            self._label.configure(
                text="On" if on else "Off",
                foreground=self._pal["fg"] if on else self._pal["fg_muted"],
            )


def apply_titlebar_theme(root, dark: bool) -> None:
    """Ask DWM to use a dark title bar to match the dialog body. Windows-only.

    Tk doesn't expose this — without it, dialogs on a dark-mode system show
    the body in dark colours but keep a stark white title bar above them.
    Uses DWMWA_USE_IMMERSIVE_DARK_MODE (attribute 20 on Win10 1903+, with
    fallback to attribute 19 for the original undocumented value on older
    builds). Safe to call multiple times; safe on non-Windows (no-op).
    """
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return
    try:
        # Make sure the HWND exists before we poke DWM at it.
        root.update_idletasks()
    except Exception:
        pass
    try:
        # root.winfo_id() returns the child window; the actual top-level
        # HWND is its parent.
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        if not hwnd:
            hwnd = root.winfo_id()
        value = ctypes.c_int(1 if dark else 0)
        DwmSetWindowAttribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        # Try the modern attribute number first, then the legacy one.
        for attr in (20, 19):
            res = DwmSetWindowAttribute(
                wintypes.HWND(hwnd),
                ctypes.c_uint(attr),
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
            if res == 0:
                break
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Tag store introspection (used for suggestions + autocomplete)
# ---------------------------------------------------------------------------


def _load_store() -> Dict[str, List[str]]:
    try:
        from .helpers import load_tags
    except Exception:
        return {}
    try:
        return load_tags() or {}
    except Exception:
        return {}


def all_known_tags() -> List[str]:
    """Distinct tag names across every file, sorted alphabetically."""
    seen: set = set()
    for tags in _load_store().values():
        if not tags:
            continue
        for t in tags:
            if isinstance(t, str) and t.strip():
                seen.add(t)
    return sorted(seen, key=str.casefold)


def tag_usage_counts() -> Dict[str, int]:
    """Map of tag -> how many files have it. Used to rank suggestions."""
    counts: Dict[str, int] = {}
    for tags in _load_store().values():
        if not tags:
            continue
        for t in tags:
            if isinstance(t, str) and t.strip():
                counts[t] = counts.get(t, 0) + 1
    return counts
