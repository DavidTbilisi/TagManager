#!/usr/bin/env python3
"""Regression tests for the post-launch bug-fix pass.

Covers:
- CLI handler wiring (license/shell/sendto/hotkey were called but never imported).
- Journal/undo coverage for remove, move, and bulk-remove operations.
- Alias transitive resolution + cycle safety.
- Licensing attestation verification (signature, tier, grace window).
"""

import base64
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


# ---------------------------------------------------------------------------
# P0.1 — every subcommand's handler must be resolvable (no NameError on call)
# ---------------------------------------------------------------------------
class TestCliHandlerWiring(unittest.TestCase):
    def test_top_level_handlers_imported(self):
        import filetagger.cli as cli

        for name in (
            "handle_license_activate", "handle_license_status",
            "handle_license_refresh", "handle_license_deactivate",
            "handle_shell_tag", "handle_shell_uninstall", "handle_shell_status",
            "handle_sendto_install", "handle_sendto_uninstall", "handle_sendto_status",
        ):
            self.assertTrue(hasattr(cli, name), f"cli.{name} not imported -> NameError on use")

    def test_license_status_runs_without_nameerror(self):
        from typer.testing import CliRunner
        import filetagger.cli as cli

        res = CliRunner().invoke(cli.app, ["license", "status"])
        self.assertNotIsInstance(res.exception, NameError)

    @unittest.skipUnless(sys.platform == "win32", "hotkey handler imports ctypes.wintypes")
    def test_hotkey_handlers_exist(self):
        from filetagger.app.hotkey import handler as h

        for n in ("handle_run", "handle_install", "handle_uninstall", "handle_status"):
            self.assertTrue(hasattr(h, n))


# ---------------------------------------------------------------------------
# P1.2 — remove / move / bulk-remove must be undoable via the journal
# ---------------------------------------------------------------------------
class TestRemoveMoveUndo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.tags_file = os.path.join(self.dir, "tags.json")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    @contextmanager
    def _env(self, initial):
        with open(self.tags_file, "w", encoding="utf-8") as f:
            json.dump(initial, f)
        with patch("filetagger.app.helpers.get_tag_file_path", return_value=self.tags_file), \
             patch("filetagger.app.journal.service.get_tag_file_path", return_value=self.tags_file), \
             patch.dict(os.environ, {"FILETAGGER_JOURNAL": "1"}):
            yield

    def _key(self, name):
        return os.path.normpath(os.path.abspath(os.path.join(self.dir, name)))

    def test_remove_path_is_undoable(self):
        from filetagger.app.helpers import load_tags
        from filetagger.app.remove.service import remove_path
        from filetagger.app.journal.service import undo_last

        p = self._key("a.txt")
        with self._env({p: ["work", "q1"]}):
            self.assertTrue(remove_path(p)["success"])
            self.assertEqual(load_tags(), {})
            ok, _, n = undo_last(1)
            self.assertTrue(ok)
            self.assertEqual(load_tags(), {p: ["work", "q1"]})

    def test_move_path_is_undoable(self):
        from filetagger.app.helpers import load_tags
        from filetagger.app.move.service import move_path
        from filetagger.app.journal.service import undo_last

        old, new = self._key("old.txt"), self._key("new.txt")
        with self._env({old: ["t"]}):
            ok, _ = move_path(old, new)
            self.assertTrue(ok)
            self.assertEqual(load_tags(), {new: ["t"]})
            uok, _, _ = undo_last(1)
            self.assertTrue(uok)
            self.assertEqual(load_tags(), {old: ["t"]})

    def test_bulk_remove_by_tag_is_undoable(self):
        from filetagger.app.helpers import load_tags
        from filetagger.app.bulk.service import bulk_remove_by_tag
        from filetagger.app.journal.service import undo_last

        p1, p2 = self._key("1.txt"), self._key("2.txt")
        with self._env({p1: ["drop", "keep"], p2: ["other"]}), \
             patch("filetagger.app.bulk.service.backup_if_configured", lambda: None):
            res = bulk_remove_by_tag("drop")
            self.assertTrue(res["success"])
            self.assertNotIn(p1, load_tags())
            ok, _, _ = undo_last(1)
            self.assertTrue(ok)
            self.assertEqual(load_tags().get(p1), ["drop", "keep"])


# ---------------------------------------------------------------------------
# P2 — alias transitive resolution + cycle safety
# ---------------------------------------------------------------------------
class TestAliasResolution(unittest.TestCase):
    def test_transitive_resolution(self):
        from filetagger.app.alias.service import apply_aliases

        with patch("filetagger.app.alias.service.get_aliases",
                   return_value={"a": "b", "b": "c"}):
            self.assertEqual(apply_aliases(["a"]), ["c"])

    def test_non_alias_preserves_original(self):
        from filetagger.app.alias.service import apply_aliases

        with patch("filetagger.app.alias.service.get_aliases", return_value={"a": "b"}):
            self.assertEqual(apply_aliases(["Keep", "a"]), ["Keep", "b"])

    def test_cycle_terminates(self):
        from filetagger.app.alias.service import apply_aliases

        with patch("filetagger.app.alias.service.get_aliases",
                   return_value={"a": "b", "b": "a"}):
            out = apply_aliases(["a"])  # must not hang
            self.assertEqual(len(out), 1)


# ---------------------------------------------------------------------------
# Licensing — full attestation verification with an ephemeral signing key
# ---------------------------------------------------------------------------
class TestLicensingVerify(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
        except ImportError:
            raise unittest.SkipTest("cryptography not installed")
        cls._ser = serialization
        cls.priv = Ed25519PrivateKey.generate()
        raw = cls.priv.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        cls.pub_b64 = base64.urlsafe_b64encode(raw).decode().rstrip("=")

    def _mint(self, payload, tamper=False):
        pb = json.dumps(payload).encode("utf-8")
        sig = self.priv.sign(pb)
        if tamper:
            sig = bytes([sig[0] ^ 0xFF]) + sig[1:]
        b = lambda x: base64.urlsafe_b64encode(x).decode().rstrip("=")
        return f"{b(pb)}.{b(sig)}"

    def _verify(self, key):
        import filetagger.licensing as lic
        with patch.object(lic, "PUBLIC_KEY_B64", self.pub_b64):
            return lic.verify_key_string(key)

    def test_valid_pro(self):
        now = int(time.time())
        info = self._verify(self._mint(
            {"sub": "x@y.z", "tier": "pro", "txn": "txn_1", "iat": now, "exp": now + 30 * 86400}
        ))
        self.assertTrue(info.valid)
        self.assertEqual(info.tier, "pro")
        self.assertFalse(info.in_grace)

    def test_expired_within_grace(self):
        now = int(time.time())
        info = self._verify(self._mint(
            {"sub": "x@y.z", "tier": "pro", "txn": "t", "iat": now - 40 * 86400, "exp": now - 86400}
        ))
        self.assertTrue(info.valid)
        self.assertTrue(info.in_grace)

    def test_expired_beyond_grace(self):
        now = int(time.time())
        info = self._verify(self._mint(
            {"sub": "x@y.z", "tier": "pro", "txn": "t", "iat": now - 60 * 86400, "exp": now - 30 * 86400}
        ))
        self.assertFalse(info.valid)

    def test_wrong_tier_rejected(self):
        now = int(time.time())
        info = self._verify(self._mint(
            {"sub": "x", "tier": "free", "txn": "t", "iat": now, "exp": now + 86400}
        ))
        self.assertFalse(info.valid)

    def test_tampered_signature_rejected(self):
        now = int(time.time())
        info = self._verify(self._mint(
            {"sub": "x", "tier": "pro", "txn": "t", "iat": now, "exp": now + 86400}, tamper=True
        ))
        self.assertFalse(info.valid)

    def test_malformed_rejected(self):
        self.assertFalse(self._verify("not-a-key").valid)


if __name__ == "__main__":
    unittest.main()
