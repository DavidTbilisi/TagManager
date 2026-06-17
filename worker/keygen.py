#!/usr/bin/env python3
"""
Generate the Ed25519 keypair used by the license verify worker.

Run once, then:
  - Paste the printed PUBLIC_KEY_B64 into filetagger/licensing.py.
  - Pipe the printed JWK into Wrangler:
        wrangler secret put ED25519_PRIVATE_JWK
    and paste the JSON when prompted.

The private key never touches disk in the worker repo; if you also save it
locally for backup, store it outside git (e.g. a password manager).
"""

from __future__ import annotations

import base64
import json
import sys


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def main() -> int:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        print("Install cryptography first:  pip install cryptography", file=sys.stderr)
        return 1

    priv = Ed25519PrivateKey.generate()
    priv_raw = priv.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_raw = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    jwk = {
        "kty": "OKP",
        "crv": "Ed25519",
        "d":   b64url(priv_raw),
        "x":   b64url(pub_raw),
    }

    print("=" * 72)
    print("PUBLIC KEY  (paste into filetagger/licensing.py as PUBLIC_KEY_B64):")
    print("=" * 72)
    print(b64url(pub_raw))
    print()
    print("=" * 72)
    print("PRIVATE JWK (paste into wrangler secret ED25519_PRIVATE_JWK):")
    print("=" * 72)
    print(json.dumps(jwk))
    print()
    print("Keep the JWK secret. Anyone who has it can forge licenses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
