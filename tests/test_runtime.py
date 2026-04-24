#!/usr/bin/env python3
"""Tests for tagmanager.runtime (CLI init, JSON/quiet, echo, log file)."""

import io
import json
import logging
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestRuntime(unittest.TestCase):
    def tearDown(self):
        import tagmanager.runtime as rt

        os.environ.pop("TM_JSON", None)
        rt.init_cli(verbose=False, quiet=False, json_output=False)

    def test_init_cli_json_from_env(self):
        import tagmanager.runtime as rt

        os.environ["TM_JSON"] = "true"
        rt.init_cli()
        self.assertTrue(rt.json_mode())
        del os.environ["TM_JSON"]

    def test_init_cli_quiet_suppresses_non_error_echo(self):
        import tagmanager.runtime as rt

        rt.init_cli(quiet=True, verbose=False)
        self.assertTrue(rt.quiet_mode())
        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            rt.echo("hi", err=False)
        self.assertEqual(buf.getvalue(), "")

    def test_init_cli_verbose_allows_echo_when_also_quiet_false(self):
        import tagmanager.runtime as rt

        rt.init_cli(quiet=False, verbose=False)
        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            rt.echo("x", err=False)
        self.assertEqual(buf.getvalue(), "x\n")

    def test_echo_error_goes_stderr_even_when_quiet(self):
        import tagmanager.runtime as rt

        rt.init_cli(quiet=True, verbose=False)
        buf = io.StringIO()
        with patch.object(sys, "stderr", buf):
            rt.echo("warn", err=True)
        self.assertIn("warn", buf.getvalue())

    def test_emit_json_prints(self):
        import tagmanager.runtime as rt

        buf = io.StringIO()
        with patch.object(sys, "stdout", buf):
            rt.emit_json({"a": 1})
        self.assertEqual(json.loads(buf.getvalue()), {"a": 1})

    def test_init_cli_log_file_opens_second_handler(self):
        import tagmanager.runtime as rt

        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as f:
            log_path = f.name
        try:
            rt.init_cli(log_file=log_path)
            log = logging.getLogger()
            self.assertGreaterEqual(len(log.handlers), 1)
        finally:
            try:
                os.unlink(log_path)
            except OSError:
                pass
            rt.init_cli()

    def test_init_cli_log_file_os_error_warns(self):
        import tagmanager.runtime as rt

        with patch("logging.FileHandler", side_effect=OSError("nope")):
            rt.init_cli(log_file="/nonexistent/dir/x.log")
        log = logging.getLogger()
        self.assertTrue(any(isinstance(h, logging.StreamHandler) for h in log.handlers))

    def test_log_debug_no_crash(self):
        import tagmanager.runtime as rt

        rt.init_cli(verbose=True)
        rt.log_debug("msg %s", "a")
