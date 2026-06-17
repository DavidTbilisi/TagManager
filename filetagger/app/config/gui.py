"""Themed settings window — `tm config gui`.

Lists every known setting in a tabbed view (one tab per category), with a
type-appropriate widget per row (checkbox / spinbox / combobox / entry).
Changes are batched and only written on Save.

Visual styling comes from `filetagger.app._gui` so it matches the tag dialog.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from .service import (
    _get_all_configuration_keys,
    _get_configuration_categories,
    _get_key_description,
    delete_configuration_value,
    list_configuration_values,
    set_configuration_value,
)


# ---------------------------------------------------------------------------
# Type metadata — drives widget choice and validation.
# ---------------------------------------------------------------------------

# A key shows as a Combobox if it appears here; otherwise the widget is chosen
# from the inferred python type (bool/int/float/str).
ENUMS: Dict[str, List[str]] = {
    "output.format": ["table", "json", "csv", "tree"],
    "advanced.log_level": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    "output.timezone": ["local", "utc"],
}

# Range hints for spinboxes; (from, to, increment).
RANGES: Dict[str, Tuple[float, float, float]] = {
    "display.max_items":          (1, 10000, 10),
    "search.fuzzy_threshold":     (0.0, 1.0, 0.05),
    "tags.max_per_file":          (1, 1000, 1),
    "files.max_size_mb":          (1, 100_000, 10),
    "performance.cache_ttl":      (0, 86400, 60),
    "performance.batch_size":     (1, 100_000, 100),
    "backup.count":               (0, 100, 1),
}


def _infer_type(value: Any) -> str:
    """Return one of: bool/int/float/str."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "str"


def _category_of(key: str) -> str:
    return key.split(".", 1)[0] if "." in key else "other"


# Friendly sidebar labels + emoji icons (Segoe UI Emoji renders these on Win).
CATEGORY_ICONS = {
    "display":     "🖥️",
    "search":      "🔍",
    "tags":        "🏷️",
    "files":       "📁",
    "output":      "📤",
    "performance": "⚡",
    "backup":      "💾",
    "storage":     "💽",
    "advanced":    "⚙️",
}
CATEGORY_LABELS = {
    "display":     "Display",
    "search":      "Search",
    "tags":        "Tags",
    "files":       "Files",
    "output":      "Output",
    "performance": "Performance",
    "backup":      "Backup",
    "storage":     "Storage",
    "advanced":    "Advanced",
}


# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------


def open_settings_dialog() -> int:
    """Pop the settings window. Returns the typer exit code (0 = ok, 1 = error)."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except Exception as exc:
        print(f"Tk is unavailable: {exc}")
        return 1

    from .._gui import (
        ToggleSwitch,
        apply_icon,
        apply_theme,
        apply_titlebar_theme,
        is_dark_mode,
        palette,
        pick_font_family,
    )

    # ---- Build the model: list every key, with its current value + default
    # `list_configuration_values(show_defaults=True)` returns everything.
    all_data = list_configuration_values(show_defaults=True)

    # Make sure we include every known key even if list_configuration_values
    # missed any (defensive — schema can drift).
    for k in _get_all_configuration_keys():
        if k not in all_data:
            all_data[k] = {
                "value": None, "is_default": True,
                "type": "str", "description": _get_key_description(k),
            }

    # Group by category
    categories: Dict[str, List[str]] = {}
    for key in sorted(all_data.keys()):
        categories.setdefault(_category_of(key), []).append(key)

    # ---- Build the UI
    root = tk.Tk()
    root.title("FileTagger Settings")
    apply_icon(root)

    try:
        root.tk.call("tk", "scaling", 1.4)
    except tk.TclError:
        pass

    dark = is_dark_mode()
    pal = palette(dark)
    font_family = pick_font_family(root)
    apply_theme(root, pal, font_family)
    apply_titlebar_theme(root, dark)

    root.minsize(820, 580)

    # State: per-key tk.Variable + revert helpers
    var_for: Dict[str, "tk.Variable"] = {}
    original: Dict[str, Any] = {k: v["value"] for k, v in all_data.items()}
    is_default: Dict[str, bool] = {k: v["is_default"] for k, v in all_data.items()}

    # Top-level layout:
    #   ┌─────────┬──────────────────────┐
    #   │ sidebar │  scrollable cards    │  ← row 0, fills
    #   ├─────────┴──────────────────────┤
    #   │  status + button row           │  ← row 1
    #   └────────────────────────────────┘
    outer = ttk.Frame(root)
    outer.pack(fill="both", expand=True)
    outer.rowconfigure(0, weight=1)

    # Two columns: sidebar (fixed) + main (stretches).
    SIDEBAR_WIDTH = 220
    outer.columnconfigure(0, minsize=SIDEBAR_WIDTH, weight=0)
    outer.columnconfigure(1, weight=1)

    sidebar = tk.Frame(outer, background=pal["surface"], width=SIDEBAR_WIDTH)
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)  # honour the fixed width

    main = tk.Frame(outer, background=pal["bg"])
    main.grid(row=0, column=1, sticky="nsew")
    main.columnconfigure(0, weight=1)
    main.rowconfigure(1, weight=1)

    # ---- Sidebar: brand at top, then category buttons.
    brand_frame = tk.Frame(sidebar, background=pal["surface"])
    brand_frame.pack(fill="x", padx=20, pady=(20, 8))
    tk.Label(
        brand_frame, text="FileTagger",
        background=pal["surface"], foreground=pal["fg"],
        font=(font_family, 13, "bold"),
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        brand_frame, text="Settings",
        background=pal["surface"], foreground=pal["fg_muted"],
        font=(font_family, 10),
        anchor="w",
    ).pack(anchor="w")

    # Separator
    tk.Frame(sidebar, height=1, background=pal["border"]).pack(
        fill="x", padx=12, pady=(4, 8)
    )

    nav_items: Dict[str, tk.Frame] = {}     # category -> button row frame
    nav_indicators: Dict[str, tk.Frame] = {}  # category -> left accent bar
    nav_label: Dict[str, tk.Label] = {}     # category -> label
    nav_icon: Dict[str, tk.Label] = {}      # category -> icon label
    current_cat: List[str] = []  # one-element list so closures can mutate

    def _redraw_nav() -> None:
        active = current_cat[0] if current_cat else None
        for cat, frame in nav_items.items():
            is_active = cat == active
            bg = pal["surface_alt"] if is_active else pal["surface"]
            for w in (frame, nav_label[cat], nav_icon[cat]):
                w.configure(background=bg)
            nav_label[cat].configure(
                foreground=pal["accent"] if is_active else pal["fg"],
                font=(font_family, 11, "bold" if is_active else "normal"),
            )
            # Show/hide the left accent bar.
            ind = nav_indicators[cat]
            if is_active:
                ind.configure(background=pal["accent"])
            else:
                ind.configure(background=pal["surface"])

    def _make_nav_button(cat: str) -> None:
        row = tk.Frame(sidebar, background=pal["surface"], cursor="hand2")
        row.pack(fill="x", padx=8, pady=1)

        # 3px accent bar on the left
        indicator = tk.Frame(row, background=pal["surface"], width=3)
        indicator.pack(side="left", fill="y")

        icon_lbl = tk.Label(
            row, text=CATEGORY_ICONS.get(cat, "•"),
            background=pal["surface"], foreground=pal["fg"],
            font=(font_family, 13),
            padx=10, pady=8,
        )
        icon_lbl.pack(side="left")

        text_lbl = tk.Label(
            row, text=CATEGORY_LABELS.get(cat, cat.title()),
            background=pal["surface"], foreground=pal["fg"],
            font=(font_family, 11),
            anchor="w",
        )
        text_lbl.pack(side="left", fill="x", expand=True, pady=8)

        nav_items[cat] = row
        nav_indicators[cat] = indicator
        nav_label[cat] = text_lbl
        nav_icon[cat] = icon_lbl

        def _select(_event=None):
            current_cat[0] = cat
            _show_category(cat)
            _redraw_nav()

        def _hover_in(_event=None):
            if current_cat[0] != cat:
                row.configure(background=pal["surface_alt"])
                text_lbl.configure(background=pal["surface_alt"])
                icon_lbl.configure(background=pal["surface_alt"])

        def _hover_out(_event=None):
            if current_cat[0] != cat:
                row.configure(background=pal["surface"])
                text_lbl.configure(background=pal["surface"])
                icon_lbl.configure(background=pal["surface"])

        for w in (row, text_lbl, icon_lbl):
            w.bind("<Button-1>", _select)
            w.bind("<Enter>", _hover_in)
            w.bind("<Leave>", _hover_out)

    # ---- Header + scrollable content area on the right
    header_frame = tk.Frame(main, background=pal["bg"])
    header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 6))
    header_title = tk.Label(
        header_frame, text="",
        background=pal["bg"], foreground=pal["fg"],
        font=(font_family, 18, "bold"),
        anchor="w",
    )
    header_title.pack(anchor="w")
    header_sub = tk.Label(
        header_frame,
        text="Change values, then click Save. Changes write to your user config only.",
        background=pal["bg"], foreground=pal["fg_muted"],
        font=(font_family, 10),
        anchor="w",
    )
    header_sub.pack(anchor="w", pady=(2, 0))

    # Scrollable list of cards
    list_frame = tk.Frame(main, background=pal["bg"])
    list_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 4), pady=(0, 4))
    list_frame.columnconfigure(0, weight=1)
    list_frame.rowconfigure(0, weight=1)

    list_canvas = tk.Canvas(
        list_frame, background=pal["bg"], highlightthickness=0, borderwidth=0,
    )
    list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=list_canvas.yview)
    list_canvas.configure(yscrollcommand=list_scroll.set)
    list_canvas.grid(row=0, column=0, sticky="nsew")
    list_scroll.grid(row=0, column=1, sticky="ns")

    cards_host = tk.Frame(list_canvas, background=pal["bg"])
    cards_host_id = list_canvas.create_window(
        (0, 0), window=cards_host, anchor="nw"
    )

    def _on_cards_resize(_e=None):
        list_canvas.configure(scrollregion=list_canvas.bbox("all"))

    def _on_canvas_resize(event):
        list_canvas.itemconfigure(cards_host_id, width=event.width)

    def _on_mousewheel(event):
        list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    cards_host.bind("<Configure>", _on_cards_resize)
    list_canvas.bind("<Configure>", _on_canvas_resize)
    list_canvas.bind("<Enter>", lambda _e: list_canvas.bind_all("<MouseWheel>", _on_mousewheel))
    list_canvas.bind("<Leave>", lambda _e: list_canvas.unbind_all("<MouseWheel>"))

    def _make_widget(parent, key: str, value: Any) -> "tk.Variable":
        """Build the right widget for the key's type; return its variable."""
        kind = "enum" if key in ENUMS else _infer_type(value)

        if kind == "bool":
            var = tk.BooleanVar(value=bool(value))
            sw = ToggleSwitch(parent, var, pal)
            wrapper = sw.pack_with_label((font_family, 10, "bold"))
            wrapper.pack(side="right")
        elif kind == "int":
            var = tk.StringVar(value=str(int(value) if value is not None else 0))
            lo, hi, step = RANGES.get(key, (0, 1_000_000, 1))
            sb = ttk.Spinbox(
                parent, from_=lo, to=hi, increment=step, textvariable=var, width=10,
                font=(font_family, 10),
            )
            sb.pack(side="right", ipady=2)
        elif kind == "float":
            var = tk.StringVar(
                value=f"{float(value) if value is not None else 0.0:.2f}"
            )
            lo, hi, step = RANGES.get(key, (0.0, 1.0, 0.05))
            sb = ttk.Spinbox(
                parent, from_=lo, to=hi, increment=step, textvariable=var, width=10,
                font=(font_family, 10), format="%.2f",
            )
            sb.pack(side="right", ipady=2)
        elif kind == "enum":
            options = ENUMS[key]
            var = tk.StringVar(value=str(value) if value is not None else options[0])
            cb = ttk.Combobox(
                parent, textvariable=var, values=options, state="readonly",
                width=18, font=(font_family, 10),
            )
            cb.pack(side="right", ipady=2)
        else:  # str
            var = tk.StringVar(value="" if value is None else str(value))
            en = ttk.Entry(parent, textvariable=var, width=24, font=(font_family, 10))
            en.pack(side="right", fill="x", expand=False, ipady=2)

        return var

    def _show_category(category: str) -> None:
        # Clear existing cards + rebuild for the selected category.
        for child in cards_host.winfo_children():
            child.destroy()
        header_title.configure(text=CATEGORY_LABELS.get(category, category.title()))

        keys = categories.get(category, [])
        if not keys:
            tk.Label(
                cards_host, text="(no settings in this category)",
                background=pal["bg"], foreground=pal["fg_muted"],
                font=(font_family, 10, "italic"),
            ).pack(anchor="w", pady=10)
            return

        for row_idx, key in enumerate(keys):
            data = all_data[key]
            card = tk.Frame(
                cards_host,
                background=pal["surface_alt"],
                highlightbackground=pal["border"], highlightthickness=1,
            )
            card.pack(fill="x", pady=(0 if row_idx == 0 else 6, 0), padx=4)

            content = tk.Frame(card, background=pal["surface_alt"])
            content.pack(fill="x", padx=18, pady=14)

            # Right side first — claims its width, then left can expand.
            right = tk.Frame(content, background=pal["surface_alt"])
            right.pack(side="right", anchor="e", padx=(16, 0))

            var = _make_widget(right, key, data["value"])
            var_for[key] = var

            # Left: name + description
            left = tk.Frame(content, background=pal["surface_alt"])
            left.pack(side="left", fill="x", expand=True, anchor="w")

            name_row = tk.Frame(left, background=pal["surface_alt"])
            name_row.pack(anchor="w", fill="x")

            label_text = key.split(".", 1)[-1].replace("_", " ").capitalize()
            tk.Label(
                name_row, text=label_text,
                background=pal["surface_alt"], foreground=pal["fg"],
                font=(font_family, 11, "bold"),
                anchor="w",
            ).pack(side="left")

            if not is_default[key]:
                tk.Label(
                    name_row, text="modified",
                    background=pal["accent"], foreground=pal["accent_fg"],
                    font=(font_family, 8, "bold"),
                    padx=8, pady=1,
                ).pack(side="left", padx=(10, 0))

            desc = data.get("description") or ""
            if desc:
                tk.Label(
                    left, text=desc,
                    background=pal["surface_alt"], foreground=pal["fg_muted"],
                    font=(font_family, 10),
                    anchor="w", justify="left", wraplength=520,
                ).pack(anchor="w", fill="x", pady=(2, 0))

            # Fully-qualified key path in subtle small text under the description.
            tk.Label(
                left, text=key,
                background=pal["surface_alt"], foreground=pal["fg_subtle"],
                font=("Consolas" if sys.platform.startswith("win") else "TkFixedFont", 8),
                anchor="w",
            ).pack(anchor="w", fill="x", pady=(4, 0))

    # Build sidebar in canonical category order
    ordered = [c for c in _get_configuration_categories() if c in categories]
    extras = [c for c in categories if c not in _get_configuration_categories()]
    nav_order = ordered + extras
    for cat in nav_order:
        _make_nav_button(cat)

    # ---- Footer (status + buttons) — placed in `main` so it sits below cards
    status_text = tk.StringVar(value="")
    footer = tk.Frame(main, background=pal["bg"])
    footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(8, 14))
    footer.columnconfigure(0, weight=1)
    ttk.Label(footer, textvariable=status_text, style="Muted.TLabel").grid(
        row=0, column=0, sticky="w"
    )
    button_row = tk.Frame(footer, background=pal["bg"])
    button_row.grid(row=0, column=1, sticky="e")

    def _coerce(value_str: str, original_value: Any, kind: str) -> Any:
        """Convert a tk.Variable's string into the right Python type."""
        if kind == "bool":
            return bool(value_str) if isinstance(value_str, bool) else value_str
        if kind == "int":
            return int(float(value_str))
        if kind == "float":
            return float(value_str)
        return value_str  # str / enum

    def _gather_diff() -> Dict[str, Any]:
        """Return {key: new_value} for keys whose value actually changed."""
        diff: Dict[str, Any] = {}
        for key, var in var_for.items():
            kind = "enum" if key in ENUMS else _infer_type(original[key])
            raw = var.get()
            try:
                new = _coerce(raw, original[key], kind)
            except Exception as exc:
                raise ValueError(f"{key}: invalid value '{raw}' ({exc})")
            if new != original[key]:
                diff[key] = new
        return diff

    def _on_save() -> None:
        try:
            diff = _gather_diff()
        except ValueError as exc:
            messagebox.showerror("Invalid value", str(exc), parent=root)
            return
        if not diff:
            status_text.set("No changes.")
            return
        failed: List[str] = []
        for key, value in diff.items():
            ok = set_configuration_value(key, value)
            if not ok:
                failed.append(key)
        if failed:
            messagebox.showerror(
                "Save failed",
                f"Could not write: {', '.join(failed)}",
                parent=root,
            )
            return
        status_text.set(f"Saved {len(diff)} setting(s).")
        # Refresh originals so further edits diff against the new baseline
        for k, v in diff.items():
            original[k] = v
            is_default[k] = False
        root.after(900, root.destroy)

    def _on_cancel() -> None:
        root.destroy()

    def _on_reset_visible() -> None:
        """Reset every key in the currently-selected category to its default."""
        if not current_cat:
            return
        cat = current_cat[0]
        if not messagebox.askyesno(
            "Reset section",
            f"Reset all '{CATEGORY_LABELS.get(cat, cat)}' settings to defaults?",
            parent=root,
        ):
            return
        count = 0
        for key in categories[cat]:
            if delete_configuration_value(key):
                count += 1
            from .service import get_configuration_value

            new_val, _ = get_configuration_value(key)
            var = var_for[key]
            if isinstance(var, tk.BooleanVar):
                var.set(bool(new_val))
            else:
                var.set("" if new_val is None else str(new_val))
            original[key] = new_val
            is_default[key] = True
        # Re-render the cards so "modified" pills update.
        _show_category(cat)
        status_text.set(f"Reset {count} setting(s) in {CATEGORY_LABELS.get(cat, cat)}.")

    ttk.Button(button_row, text="Cancel", command=_on_cancel).pack(
        side="right", padx=(8, 0)
    )
    ttk.Button(button_row, text="Save", command=_on_save, style="Accent.TButton").pack(
        side="right"
    )
    ttk.Button(button_row, text="Reset section", command=_on_reset_visible).pack(
        side="right", padx=(0, 8)
    )

    # Select first category by default
    if nav_order:
        current_cat.append(nav_order[0])
        _show_category(nav_order[0])
        _redraw_nav()

    root.bind("<Escape>", lambda _e: _on_cancel())
    root.protocol("WM_DELETE_WINDOW", _on_cancel)

    root.update_idletasks()
    width = max(720, root.winfo_reqwidth())
    height = max(520, root.winfo_reqheight())
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Force focus so Escape and keyboard nav reach the window when launched
    # from a non-terminal context (Start menu, scripts, etc.).
    root.focus_force()
    root.after(50, root.focus_force)

    root.mainloop()
    return 0
