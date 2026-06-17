"""Windows Explorer right-click context menu integration via IExplorerCommand.

Modern Win11 context menus (both the new menu and "Show more options") filter
ad-hoc registry-only shell verbs. The way through is to register a COM class
implementing IExplorerCommand and reference it from the shell verb via
`ExplorerCommandHandler`.

Layout (per-user, HKCU, no admin required):
  Software\\Classes\\CLSID\\{GUID}
      (Default)               = "FileTagger Shell Command"
  Software\\Classes\\CLSID\\{GUID}\\InProcServer32
      (Default)               = "<...>\\filetagger_shellext.dll"
      ThreadingModel          = "Apartment"
  Software\\Classes\\AllFilesystemObjects\\shell\\FileTagger
      MUIVerb                 = "Tag with FileTagger"
      ExplorerCommandHandler  = "{GUID}"
  Software\\Classes\\Directory\\Background\\shell\\FileTagger
      (same)

The DLL launches the Python dialog (`pythonw -m filetagger shell tag <path>`).
A sibling .cfg file next to the DLL tells the DLL which pythonw to use, so
the verb works no matter how the user installed filetagger.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Must match CLSID_FILETAGGER_COMMAND in filetagger_shellext/src/lib.rs
COM_CLSID = "{2B6CF6E1-7F4A-4D2B-9D6B-7C0B2A7E1A11}"
COM_CLSID_NAME = "FileTagger Shell Command"

VERB_KEY = "FileTagger"
VERB_LABEL = "Tag with FileTagger"

VERB_PARENTS = [
    r"Software\Classes\AllFilesystemObjects\shell",
    r"Software\Classes\Directory\Background\shell",
]

DLL_FILENAME = "filetagger_shellext.dll"
CFG_FILENAME = "filetagger_shellext.cfg"


def _find_shellext_dll() -> Path:
    """Locate the prebuilt shell extension DLL.

    Search order:
      1. FILETAGGER_SHELLEXT_DLL env var (escape hatch / packaging).
      2. filetagger_shellext/target/release/<dll> in the source checkout.
      3. <package_dir>/_shellext/<dll> — where wheel builds drop it.
    """
    override = os.environ.get("FILETAGGER_SHELLEXT_DLL")
    if override and Path(override).is_file():
        return Path(override).resolve()

    here = Path(__file__).resolve()
    # filetagger/app/shell/service.py -> repo root is parents[3]
    repo_root = here.parents[3]
    candidate = repo_root / "filetagger_shellext" / "target" / "release" / DLL_FILENAME
    if candidate.is_file():
        return candidate.resolve()

    # Installed-package layout fallback
    pkg_root = here.parents[2]  # filetagger/
    candidate = pkg_root / "_shellext" / DLL_FILENAME
    if candidate.is_file():
        return candidate.resolve()

    raise FileNotFoundError(
        f"Could not locate {DLL_FILENAME}. Looked in:\n"
        f"  - $FILETAGGER_SHELLEXT_DLL\n"
        f"  - {repo_root / 'filetagger_shellext' / 'target' / 'release'}\n"
        f"  - {pkg_root / '_shellext'}\n"
        f"Run `cargo build --release` in filetagger_shellext/ first."
    )


def _resolve_pythonw() -> str:
    """Best-effort path to the pythonw.exe that owns the filetagger package."""
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = exe[:-len("python.exe")] + "pythonw.exe"
        if os.path.isfile(candidate):
            return candidate
    return exe


def _open_writable(parent_path: str):
    import winreg

    return winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, parent_path, 0, winreg.KEY_ALL_ACCESS
    )


def _delete_tree(root_path: str) -> None:
    """Recursively delete root_path under HKCU (RegDeleteTree-style)."""
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, root_path, 0, winreg.KEY_ALL_ACCESS
        ) as key:
            # Walk children first, then delete self.
            while True:
                try:
                    sub = winreg.EnumKey(key, 0)
                except OSError:
                    break
                _delete_tree(f"{root_path}\\{sub}")
    except FileNotFoundError:
        return
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, root_path)
    except FileNotFoundError:
        pass


def install_context_menu() -> Dict[str, object]:
    """Register the COM class + shell verbs in HKCU. No admin required."""
    if not sys.platform.startswith("win"):
        return {
            "success": False,
            "message": "Shell integration is only available on Windows.",
        }

    import winreg

    try:
        dll_path = _find_shellext_dll()
    except FileNotFoundError as exc:
        return {"success": False, "message": str(exc)}

    # Write companion .cfg so the DLL knows which pythonw to launch.
    cfg_path = dll_path.with_name(CFG_FILENAME)
    try:
        cfg_path.write_text(_resolve_pythonw(), encoding="utf-8")
    except OSError as exc:
        return {"success": False, "message": f"Cannot write {cfg_path}: {exc}"}

    installed: List[str] = []
    errors: List[str] = []

    # 1) CLSID registration
    clsid_root = rf"Software\Classes\CLSID\{COM_CLSID}"
    inproc = rf"{clsid_root}\InProcServer32"
    try:
        with _open_writable(clsid_root) as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, COM_CLSID_NAME)
        with _open_writable(inproc) as k:
            winreg.SetValueEx(k, None, 0, winreg.REG_SZ, str(dll_path))
            winreg.SetValueEx(k, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
    except OSError as exc:
        return {"success": False, "message": f"CLSID registration failed: {exc}"}

    # 2) Shell verb pointing at the CLSID
    for parent in VERB_PARENTS:
        verb_path = f"{parent}\\{VERB_KEY}"
        try:
            with _open_writable(verb_path) as k:
                # Some Explorer versions require (Default) alongside MUIVerb
                # for the classic menu; setting both is safe.
                winreg.SetValueEx(k, None, 0, winreg.REG_SZ, VERB_LABEL)
                winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, VERB_LABEL)
                winreg.SetValueEx(
                    k, "ExplorerCommandHandler", 0, winreg.REG_SZ, COM_CLSID
                )
                # Icon: point at python.exe so the menu item gets a snake icon.
                icon = sys.executable
                if icon.lower().endswith("pythonw.exe"):
                    icon = icon[:-len("pythonw.exe")] + "python.exe"
                winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon)
            installed.append(parent)
        except OSError as exc:
            errors.append(f"{parent}: {exc}")

    msg_lines = [f"Installed COM context menu under {len(installed)} location(s)."]
    msg_lines.append(f"  CLSID: {COM_CLSID}")
    msg_lines.append(f"  DLL:   {dll_path}")
    msg_lines.append(f"  CFG:   {cfg_path}  ({_resolve_pythonw()})")
    if errors:
        msg_lines.append("Warnings:")
        for e in errors:
            msg_lines.append(f"  {e}")
    return {
        "success": bool(installed) and not errors,
        "message": "\n".join(msg_lines),
        "installed": installed,
        "clsid": COM_CLSID,
        "dll": str(dll_path),
    }


def uninstall_context_menu() -> Dict[str, object]:
    """Remove the CLSID registration and shell verbs from HKCU."""
    if not sys.platform.startswith("win"):
        return {
            "success": False,
            "message": "Shell integration is only available on Windows.",
        }

    removed: List[str] = []
    for parent in VERB_PARENTS:
        path = f"{parent}\\{VERB_KEY}"
        _delete_tree(path)
        removed.append(parent)
    _delete_tree(rf"Software\Classes\CLSID\{COM_CLSID}")

    return {
        "success": True,
        "message": (
            f"Removed shell verb from {len(removed)} location(s) and unregistered "
            f"CLSID {COM_CLSID}."
        ),
    }


def context_menu_status() -> Dict[str, object]:
    """Report which registry parents currently have the verb installed."""
    if not sys.platform.startswith("win"):
        return {
            "installed": [],
            "missing": [],
            "platform_supported": False,
            "clsid_registered": False,
        }

    import winreg

    installed: List[str] = []
    missing: List[str] = []
    for parent in VERB_PARENTS:
        verb_path = f"{parent}\\{VERB_KEY}"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, verb_path):
                installed.append(parent)
        except OSError:
            missing.append(parent)

    clsid_registered = False
    dll_value = None
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            rf"Software\Classes\CLSID\{COM_CLSID}\InProcServer32",
        ) as k:
            dll_value, _ = winreg.QueryValueEx(k, None)
            clsid_registered = bool(dll_value)
    except OSError:
        pass

    return {
        "installed": installed,
        "missing": missing,
        "platform_supported": True,
        "clsid_registered": clsid_registered,
        "dll": dll_value,
    }


# ---------------------------------------------------------------------------
# Dialog launched by the DLL (and by `tm shell tag <path>` for fallback)
# ---------------------------------------------------------------------------


def _existing_tags_for(target_path: str) -> List[str]:
    """Return the tag list currently stored for target_path, or [] if none.

    Done here (not in the dialog) so the dialog stays pure UI and can be
    unit-tested with synthetic existing-tag inputs.
    """
    try:
        from ..helpers import load_tags
    except Exception:
        return []
    try:
        store = load_tags() or {}
    except Exception:
        return []
    # The store is keyed by abspath; try the normalized form first, then
    # fall back to a case-insensitive scan on Windows.
    norm = os.path.normpath(os.path.abspath(target_path))
    if norm in store:
        return list(store[norm])
    if sys.platform.startswith("win"):
        low = norm.lower()
        for k, v in store.items():
            if isinstance(k, str) and k.lower() == low:
                return list(v)
    return []


def prompt_tags_dialog(
    target_path: str, existing_tags: Optional[List[str]] = None
) -> Optional[List[str]]:
    """Show the tag dialog and return the user's desired final tag list.

    Returns:
      - None if the user cancelled (Esc / close / Cancel button) — caller
        should make no changes.
      - [] if the user explicitly cleared all tags and pressed Save —
        caller should remove every existing tag.
      - [tag, ...] the final desired set of tags for this path (chips that
        were kept + freshly typed tags, deduped and order-preserving).
    """
    import tkinter as tk
    from tkinter import ttk

    from .._gui import (
        all_known_tags,
        apply_icon,
        apply_theme,
        apply_titlebar_theme,
        is_dark_mode,
        palette,
        pick_font_family,
        tag_usage_counts,
    )

    existing_tags = list(dict.fromkeys(existing_tags or []))  # dedupe, keep order

    display_target = target_path
    if len(display_target) > 80:
        display_target = "…" + display_target[-79:]

    kept: List[str] = list(existing_tags)
    result: Dict[str, Optional[List[str]]] = {"final": None}  # None = cancelled

    root = tk.Tk()
    root.title("Tag with FileTagger")
    apply_icon(root)
    try:
        root.attributes("-topmost", True)
    except tk.TclError:
        pass

    # Hi-DPI: ask Tk to scale fonts so it doesn't look microscopic on 4K screens.
    try:
        root.tk.call("tk", "scaling", 1.4)
    except tk.TclError:
        pass

    dark = is_dark_mode()
    pal = palette(dark)
    font_family = pick_font_family(root)
    apply_theme(root, pal, font_family)
    apply_titlebar_theme(root, dark)

    root.minsize(560, 320)

    outer = ttk.Frame(root, padding=18)
    outer.pack(fill="both", expand=True)
    outer.columnconfigure(0, weight=1)

    # ---- Header --------------------------------------------------------
    header = ttk.Label(outer, text="Tag with FileTagger", style="Title.TLabel")
    header.grid(row=0, column=0, sticky="w")
    ttk.Label(
        outer, text="Organise this item with one or more tags.",
        style="Muted.TLabel",
    ).grid(row=1, column=0, sticky="w", pady=(2, 12))

    # ---- Target path "card" -------------------------------------------
    target_card = tk.Frame(
        outer, background=pal["surface"],
        highlightbackground=pal["border"], highlightthickness=1,
    )
    target_card.grid(row=2, column=0, sticky="ew")
    target_card.columnconfigure(1, weight=1)
    tk.Label(
        target_card, text="📄  ", background=pal["surface"], foreground=pal["fg_muted"],
        font=(font_family, 12),
    ).grid(row=0, column=0, sticky="w", padx=(8, 0), pady=4)
    ttk.Label(target_card, text=display_target, style="Path.TLabel").grid(
        row=0, column=1, sticky="w"
    )

    # Forward declarations — render_chips/render_suggestions reference `entry`
    # which is built further down; we set these via nonlocal afterwards.
    entry_widget: Dict[str, Optional[ttk.Entry]] = {"e": None}

    # ---- Existing tag chips -------------------------------------------
    chips_container: Optional[tk.Frame] = None

    def _hover_in(widget, child_label, child_btn):
        widget.configure(background=pal["chip_bg_hov"])
        child_label.configure(background=pal["chip_bg_hov"])
        child_btn.configure(background=pal["chip_bg_hov"])

    def _hover_out(widget, child_label, child_btn):
        widget.configure(background=pal["chip_bg"])
        child_label.configure(background=pal["chip_bg"])
        child_btn.configure(background=pal["chip_bg"])

    def render_chips() -> None:
        if chips_container is None:
            return
        for child in chips_container.winfo_children():
            child.destroy()
        if not kept:
            ttk.Label(
                chips_container,
                text="All current tags will be removed when you save.",
                style="Danger.TLabel",
            ).pack(side="left", pady=2)
            return
        for tag in list(kept):
            chip = tk.Frame(
                chips_container, background=pal["chip_bg"],
                highlightbackground=pal["chip_border"], highlightthickness=1,
                cursor="hand2",
            )
            lbl = tk.Label(
                chip, text=tag, background=pal["chip_bg"], foreground=pal["chip_fg"],
                font=(font_family, 10, "bold"), padx=10, pady=3,
            )
            lbl.pack(side="left")

            def _remove(t=tag):
                if t in kept:
                    kept.remove(t)
                render_chips()
                render_suggestions()  # already-kept tags become "available" again

            btn = tk.Label(
                chip, text="✕", background=pal["chip_bg"], foreground=pal["chip_fg"],
                font=(font_family, 10), padx=8, pady=3, cursor="hand2",
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda _e, t=tag: _remove(t))

            chip.bind("<Enter>", lambda _e, w=chip, l=lbl, b=btn: _hover_in(w, l, b))
            chip.bind("<Leave>", lambda _e, w=chip, l=lbl, b=btn: _hover_out(w, l, b))
            lbl.bind("<Enter>", lambda _e, w=chip, l=lbl, b=btn: _hover_in(w, l, b))
            btn.bind("<Enter>", lambda _e, w=chip, l=lbl, b=btn: _hover_in(w, l, b))

            chip.pack(side="left", padx=(0, 8), pady=4)

    row = 3
    if existing_tags:
        ttk.Label(
            outer, text="CURRENT TAGS", style="SectionHeader.TLabel",
        ).grid(row=row, column=0, sticky="w", pady=(16, 4))
        row += 1
        chips_container = tk.Frame(outer, background=pal["bg"])
        chips_container.grid(row=row, column=0, sticky="ew")
        render_chips()
        row += 1

    ttk.Label(
        outer, text="ADD TAGS", style="SectionHeader.TLabel",
    ).grid(row=row, column=0, sticky="w", pady=(16, 4))
    row += 1
    ttk.Label(
        outer, text="Comma or space separated. Pick from suggestions below or "
        "type for autocomplete.", style="Muted.TLabel",
    ).grid(row=row, column=0, sticky="w", pady=(0, 6))
    row += 1

    entry = ttk.Entry(outer, font=(font_family, 11))
    entry.grid(row=row, column=0, sticky="ew", ipady=4)
    entry.focus_force()
    root.after(50, lambda: (root.focus_force(), entry.focus_force()))
    entry_widget["e"] = entry
    row += 1

    # ---- Suggestions (top-N most-used tags) ---------------------------
    usage = tag_usage_counts()
    all_tags = all_known_tags()
    top_suggestions = sorted(
        (t for t in all_tags if t not in kept),
        key=lambda t: (-usage.get(t, 0), t.casefold()),
    )[:12]  # render up to 12; wrap into rows of 4

    suggestions_container: Optional[tk.Frame] = None

    def _add_tag_from_suggestion(tag: str) -> None:
        if tag in kept:
            return
        kept.append(tag)
        render_chips()
        render_suggestions()

    def render_suggestions() -> None:
        if suggestions_container is None:
            return
        for child in suggestions_container.winfo_children():
            child.destroy()
        available = [t for t in top_suggestions if t not in kept]
        if not available:
            ttk.Label(
                suggestions_container,
                text="(no more suggestions — type to add new tags)",
                style="Subtle.TLabel",
            ).pack(side="left", pady=2)
            return
        # Wrap chips into rows of `per_row` so the dialog doesn't grow horizontally.
        per_row = 4
        current_row: Optional[tk.Frame] = None
        for i, tag in enumerate(available):
            if i % per_row == 0:
                current_row = tk.Frame(suggestions_container, background=pal["bg"])
                current_row.pack(fill="x", anchor="w")
            count = usage.get(tag, 0)
            chip = tk.Frame(
                current_row, background=pal["sugg_bg"],
                highlightbackground=pal["sugg_border"], highlightthickness=1,
                cursor="hand2",
            )
            lbl = tk.Label(
                chip, text=f"+ {tag}",
                background=pal["sugg_bg"], foreground=pal["sugg_fg"],
                font=(font_family, 10), padx=10, pady=3,
            )
            lbl.pack(side="left")
            badge = tk.Label(
                chip, text=str(count),
                background=pal["sugg_bg"], foreground=pal["fg_subtle"],
                font=(font_family, 9), padx=6, pady=3,
            )
            badge.pack(side="left")

            def _on_click(_e=None, t=tag):
                _add_tag_from_suggestion(t)

            for w in (chip, lbl, badge):
                w.bind("<Button-1>", _on_click)
                w.bind(
                    "<Enter>",
                    lambda _e, c=chip, l=lbl, b=badge: (
                        c.configure(background=pal["sugg_bg_hov"]),
                        l.configure(background=pal["sugg_bg_hov"]),
                        b.configure(background=pal["sugg_bg_hov"]),
                    ),
                )
                w.bind(
                    "<Leave>",
                    lambda _e, c=chip, l=lbl, b=badge: (
                        c.configure(background=pal["sugg_bg"]),
                        l.configure(background=pal["sugg_bg"]),
                        b.configure(background=pal["sugg_bg"]),
                    ),
                )
            chip.pack(side="left", padx=(0, 6), pady=4)

    if top_suggestions:
        ttk.Label(
            outer, text="SUGGESTIONS", style="SectionHeader.TLabel",
        ).grid(row=row, column=0, sticky="w", pady=(14, 4))
        row += 1
        suggestions_container = tk.Frame(outer, background=pal["bg"])
        suggestions_container.grid(row=row, column=0, sticky="ew")
        render_suggestions()
        row += 1

    # ---- Inline autocomplete popup ------------------------------------
    # Floating Toplevel under the entry that shows tags matching the
    # currently-typed token. Arrow keys + Tab/Enter to accept.
    popup: Dict[str, Optional[tk.Toplevel]] = {"win": None}
    popup_state: Dict[str, object] = {"items": [], "index": -1, "labels": []}

    def _current_token() -> str:
        """Return the in-flight token the user is typing (last comma/space chunk)."""
        if entry_widget["e"] is None:
            return ""
        text = entry_widget["e"].get()
        # Find the cursor position so deleting earlier text still refreshes.
        # (Tk doesn't expose cursor easily for ttk.Entry, so just use end.)
        last_sep = max(text.rfind(","), text.rfind(" "))
        return text[last_sep + 1:].strip() if last_sep >= 0 else text.strip()

    def _accepted_tokens_already_in_entry() -> List[str]:
        e = entry_widget["e"]
        if e is None:
            return []
        text = e.get()
        last_sep = max(text.rfind(","), text.rfind(" "))
        if last_sep < 0:
            return []
        chunk = text[: last_sep + 1]
        return [t.strip() for t in chunk.replace(",", " ").split() if t.strip()]

    def _close_popup() -> None:
        win = popup["win"]
        if win is not None:
            try:
                win.destroy()
            except tk.TclError:
                pass
        popup["win"] = None
        popup_state["items"] = []
        popup_state["labels"] = []
        popup_state["index"] = -1

    def _highlight_popup() -> None:
        labels = popup_state["labels"]
        idx = popup_state["index"]
        for i, lbl in enumerate(labels):  # type: ignore[arg-type]
            if i == idx:
                lbl.configure(background=pal["accent"], foreground=pal["accent_fg"])
            else:
                lbl.configure(background=pal["sugg_bg"], foreground=pal["sugg_fg"])

    def _accept_popup(_e=None) -> str:
        items = popup_state["items"]
        idx = popup_state["index"]
        if not items or idx < 0:
            return ""
        chosen = items[idx]  # type: ignore[index]
        e = entry_widget["e"]
        if e is None:
            return "break"
        # Replace the in-flight token with the chosen tag + a trailing space.
        text = e.get()
        last_sep = max(text.rfind(","), text.rfind(" "))
        prefix = text[: last_sep + 1] if last_sep >= 0 else ""
        new_text = f"{prefix}{chosen} "
        e.delete(0, "end")
        e.insert(0, new_text)
        e.icursor("end")
        _close_popup()
        return "break"  # swallow the Tab/Enter

    def _build_popup_entries(matches: List[str]) -> None:
        _close_popup()
        if not matches:
            return
        e = entry_widget["e"]
        if e is None:
            return
        # Position popup just below the entry.
        e.update_idletasks()
        x = e.winfo_rootx()
        y = e.winfo_rooty() + e.winfo_height() + 2
        w = e.winfo_width()

        win = tk.Toplevel(root)
        win.overrideredirect(True)  # no title bar
        win.attributes("-topmost", True)
        win.configure(background=pal["sugg_border"])  # acts as 1px border
        win.geometry(f"{w}x{min(28 * len(matches) + 2, 240)}+{x}+{y}")

        inner = tk.Frame(win, background=pal["sugg_bg"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        labels: List[tk.Label] = []
        for i, tag in enumerate(matches):
            lbl = tk.Label(
                inner, text=tag, anchor="w",
                background=pal["sugg_bg"], foreground=pal["sugg_fg"],
                font=(font_family, 10), padx=10, pady=4, cursor="hand2",
            )
            lbl.pack(fill="x")

            def _click(_e=None, idx=i):
                popup_state["index"] = idx
                _accept_popup()

            def _enter(_e=None, idx=i):
                popup_state["index"] = idx
                _highlight_popup()

            lbl.bind("<Button-1>", _click)
            lbl.bind("<Enter>", _enter)
            labels.append(lbl)

        popup["win"] = win
        popup_state["items"] = matches
        popup_state["labels"] = labels
        popup_state["index"] = 0
        _highlight_popup()

    def _refresh_autocomplete(_event=None) -> None:
        token = _current_token().casefold()
        already = {t.casefold() for t in _accepted_tokens_already_in_entry()}
        already.update(t.casefold() for t in kept)
        if not token:
            _close_popup()
            return
        matches = [
            t for t in all_tags
            if t.casefold() != token
            and token in t.casefold()
            and t.casefold() not in already
        ]
        # Prioritise prefix matches over substring matches, then by usage.
        matches.sort(
            key=lambda t: (
                0 if t.casefold().startswith(token) else 1,
                -usage.get(t, 0),
                t.casefold(),
            )
        )
        _build_popup_entries(matches[:8])

    def _popup_nav(event) -> Optional[str]:
        if popup["win"] is None:
            return None
        items = popup_state["items"]
        if not items:
            return None
        idx = popup_state["index"]
        if event.keysym == "Down":
            popup_state["index"] = (idx + 1) % len(items)
            _highlight_popup()
            return "break"
        if event.keysym == "Up":
            popup_state["index"] = (idx - 1) % len(items)
            _highlight_popup()
            return "break"
        if event.keysym in ("Escape",):
            _close_popup()
            return "break"
        return None

    entry.bind("<KeyRelease>", _refresh_autocomplete)
    entry.bind("<Down>", _popup_nav)
    entry.bind("<Up>", _popup_nav)
    entry.bind("<Tab>", lambda e: _accept_popup() if popup["win"] else None)
    entry.bind("<FocusOut>", lambda _e: root.after(150, _close_popup))

    # ---- Buttons -------------------------------------------------------
    button_row = ttk.Frame(outer)
    button_row.grid(row=row, column=0, sticky="e", pady=(18, 0))

    def submit(_event=None) -> None:
        _close_popup()
        raw = entry.get().strip()
        new_parts: List[str] = []
        for chunk in raw.replace(",", " ").split():
            chunk = chunk.strip()
            if chunk and chunk not in new_parts:
                new_parts.append(chunk)
        final: List[str] = []
        for t in kept + new_parts:
            if t not in final:
                final.append(t)
        result["final"] = final
        root.destroy()

    def cancel(_event=None) -> None:
        _close_popup()
        result["final"] = None
        root.destroy()

    def on_return(_event=None) -> str:
        # Accept the popup suggestion if the popup is open; otherwise submit.
        if popup["win"] is not None:
            return _accept_popup()
        submit()
        return "break"

    def on_escape(_event=None) -> str:
        # Close the popup first; if no popup, cancel the dialog.
        if popup["win"] is not None:
            _close_popup()
            return "break"
        cancel()
        return "break"

    ttk.Button(button_row, text="Cancel", command=cancel).pack(side="right", padx=(8, 0))
    save_label = "Save" if existing_tags else "Add tags"
    ttk.Button(
        button_row, text=save_label, command=submit, style="Accent.TButton",
    ).pack(side="right")

    root.bind("<Return>", on_return)
    root.bind("<Escape>", on_escape)
    root.protocol("WM_DELETE_WINDOW", cancel)

    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    root.mainloop()
    return result["final"]


def tag_path_interactively(target_path: str) -> Dict[str, object]:
    """Pop the tag dialog and reconcile the user's final tag set with the store."""
    if not target_path:
        return {"success": False, "message": "No target path provided."}

    target_path = os.path.abspath(target_path)
    if not os.path.exists(target_path):
        return {"success": False, "message": f"Path does not exist: {target_path}"}

    existing = _existing_tags_for(target_path)

    try:
        final = prompt_tags_dialog(target_path, existing)
    except Exception as exc:
        return {"success": False, "message": f"Failed to show tag dialog: {exc}"}

    if final is None:
        return {"success": True, "message": "Cancelled (no changes made)."}

    existing_set = set(existing)
    final_set = set(final)
    to_add = [t for t in final if t not in existing_set]
    to_remove = [t for t in existing if t not in final_set]

    if not to_add and not to_remove:
        return {"success": True, "message": "No changes (tags unchanged)."}

    # Apply removals directly against the store; add via add_tags so we keep
    # alias resolution + extension auto-tags consistent with the CLI.
    summary_parts: List[str] = []
    if to_remove:
        try:
            from ..helpers import load_tags, save_tags

            store = load_tags() or {}
            norm = os.path.normpath(target_path)
            key = norm if norm in store else None
            if key is None and sys.platform.startswith("win"):
                low = norm.lower()
                for k in store.keys():
                    if isinstance(k, str) and k.lower() == low:
                        key = k
                        break
            if key is not None:
                remaining = [t for t in store.get(key, []) if t not in set(to_remove)]
                store[key] = remaining
                save_tags(store)
                summary_parts.append(f"removed: {', '.join(to_remove)}")
        except Exception as exc:
            return {
                "success": False,
                "message": f"Failed to remove tags from {target_path}: {exc}",
            }

    if to_add:
        from ..add.service import add_tags

        ok = add_tags(target_path, to_add)
        if not ok:
            return {"success": False, "message": f"Failed to add tags to {target_path}."}
        summary_parts.append(f"added: {', '.join(to_add)}")

    return {
        "success": True,
        "message": f"{target_path} — " + "; ".join(summary_parts),
        "added": to_add,
        "removed": to_remove,
        "final": final,
    }
