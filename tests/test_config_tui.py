"""Tests for ``tm config tui`` quick settings menu."""

import sys
import unittest
from io import StringIO
from unittest.mock import patch

import typer

from tagmanager.app.config.service import validate_configuration_key
from tagmanager.app.config.tui import (
    allowed_values_hint,
    run_config_tui,
    tui_entry_keys,
)


class TestConfigTui(unittest.TestCase):
    def test_tui_entry_keys_are_valid_config_keys(self):
        for key in tui_entry_keys():
            self.assertTrue(validate_configuration_key(key), msg=key)

    def test_autotag_config_keys_validate(self):
        for key in (
            "autotag.enabled",
            "autotag.content_enabled",
            "autotag.content_use_defaults",
            "autotag.content_pattern_groups",
        ):
            self.assertTrue(validate_configuration_key(key), msg=key)

    def test_allowed_values_hint_lists_enums_and_ranges(self):
        from tagmanager.app.config import tui as tui_mod

        for entry in tui_mod.TUI_ENTRIES:
            hint = allowed_values_hint(entry)
            self.assertTrue(hint.strip(), msg=entry["key"])
        fmt = next(e for e in tui_mod.TUI_ENTRIES if e["key"] == "output.format")
        self.assertIn("table", allowed_values_hint(fmt))
        self.assertIn("yaml", allowed_values_hint(fmt))
        fuzzy = next(e for e in tui_mod.TUI_ENTRIES if e["key"] == "search.fuzzy_threshold")
        self.assertIn("0.0", allowed_values_hint(fuzzy))
        self.assertIn("1.0", allowed_values_hint(fuzzy))
        backups = next(e for e in tui_mod.TUI_ENTRIES if e["key"] == "backup.count")
        self.assertIn("1", allowed_values_hint(backups))
        self.assertIn("99", allowed_values_hint(backups))

    def test_non_tty_prints_hint(self):
        from rich.console import Console

        out = StringIO()
        console = Console(file=out, width=80)
        with patch.object(sys.stdin, "isatty", return_value=False):
            run_config_tui(console=console)
        text = out.getvalue()
        self.assertIn("TTY", text)
        self.assertIn("tm config set", text)

    def test_handle_config_tui_json_mode_exits(self):
        from tagmanager.app.config.handler import handle_config_tui

        with patch("tagmanager.app.config.handler.runtime.json_mode", return_value=True):
            with self.assertRaises(typer.Exit) as ctx:
                handle_config_tui()
        self.assertEqual(ctx.exception.exit_code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
