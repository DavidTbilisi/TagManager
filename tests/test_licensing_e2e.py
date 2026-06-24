#!/usr/bin/env python3
"""End-to-end test of the license-activation chain (worker mocked).

Covers the path that broke at launch: a buyer's transaction id ->
verify worker -> signed attestation -> `ftag license activate` writes it ->
offline signature verification -> `ftag license status` reports Pro.

The only thing stubbed is the network boundary (urllib): we return a real
attestation signed with an ephemeral key whose public half is patched into
``licensing.PUBLIC_KEY_B64``. Everything else is the real code.
"""

import base64
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class _FakeResp:
    """Minimal context-manager stand-in for urllib's urlopen() return."""

    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._payload


class TestLicenseActivationE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
        except ImportError:
            raise unittest.SkipTest("cryptography not installed")
        cls._Ed = Ed25519PrivateKey
        cls._ser = serialization
        cls.priv = Ed25519PrivateKey.generate()
        raw = cls.priv.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        cls.pub_b64 = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        cls.other = Ed25519PrivateKey.generate()  # for the wrong-key case

    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _attestation(self, payload, signer=None):
        signer = signer or self.priv
        pb = json.dumps(payload).encode("utf-8")
        sig = signer.sign(pb)
        b = lambda x: base64.urlsafe_b64encode(x).decode().rstrip("=")
        return f"{b(pb)}.{b(sig)}"

    def _worker_returns(self, body: dict):
        """Patch the network so the verify worker 'returns' *body* as JSON."""
        return patch("urllib.request.urlopen",
                     return_value=_FakeResp(json.dumps(body).encode("utf-8")))

    def _isolate_storage(self, lic):
        return patch.object(lic, "_tm_dir", lambda: Path(self.dir))

    def test_activate_then_status_reports_pro(self):
        import filetagger.licensing as lic
        now = int(time.time())
        key = self._attestation(
            {"sub": "buyer@example.com", "tier": "pro", "txn": "txn_abc123",
             "iat": now, "exp": now + 30 * 86400}
        )
        with patch.object(lic, "PUBLIC_KEY_B64", self.pub_b64), \
             self._isolate_storage(lic), \
             patch.dict(os.environ, {}, clear=False), \
             self._worker_returns({"key": key}):
            os.environ.pop("FTAG_DEV_BYPASS_LICENSE", None)
            # activate
            info = lic.activate_with_transaction("txn_abc123")
            self.assertTrue(info.valid)
            self.assertEqual(info.tier, "pro")
            self.assertEqual(info.transaction_id, "txn_abc123")
            self.assertTrue(lic.license_path().exists(), "license file was written")
            # status reads it back from disk and re-verifies offline
            cur = lic.current_license()
            self.assertTrue(cur.valid)
            self.assertEqual(cur.email, "buyer@example.com")
            self.assertTrue(lic.is_pro_active())

    def test_activate_rejects_attestation_signed_by_wrong_key(self):
        import filetagger.licensing as lic
        now = int(time.time())
        forged = self._attestation(
            {"sub": "x", "tier": "pro", "txn": "txn_x", "iat": now, "exp": now + 86400},
            signer=self.other,  # not the embedded public key
        )
        with patch.object(lic, "PUBLIC_KEY_B64", self.pub_b64), \
             self._isolate_storage(lic), \
             self._worker_returns({"key": forged}):
            with self.assertRaises(lic.VerifyError):
                lic.activate_with_transaction("txn_x")
            self.assertFalse(lic.license_path().exists(), "must not persist a bad key")

    def test_activate_surfaces_worker_rejection(self):
        import filetagger.licensing as lic
        with patch.object(lic, "PUBLIC_KEY_B64", self.pub_b64), \
             self._isolate_storage(lic), \
             self._worker_returns({"error": "transaction not found"}):
            with self.assertRaises(lic.VerifyError):
                lic.activate_with_transaction("txn_missing")

    def test_refresh_reuses_stored_transaction_id(self):
        import filetagger.licensing as lic
        now = int(time.time())
        key = self._attestation(
            {"sub": "b@x.io", "tier": "pro", "txn": "txn_refresh",
             "iat": now, "exp": now + 30 * 86400}
        )
        with patch.object(lic, "PUBLIC_KEY_B64", self.pub_b64), \
             self._isolate_storage(lic), \
             self._worker_returns({"key": key}):
            lic.activate_with_transaction("txn_refresh")
            info = lic.refresh()  # re-fetch using the stored txn id
            self.assertTrue(info.valid)
            self.assertEqual(info.transaction_id, "txn_refresh")


if __name__ == "__main__":
    unittest.main()
