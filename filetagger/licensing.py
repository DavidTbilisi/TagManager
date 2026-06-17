"""
FileTagger Pro licensing — Paddle-backed activation with cached attestations.

The CLI never talks to Paddle directly (we'd have to ship the Paddle API key,
which would expose the seller account). Instead, after a buyer completes
checkout on Paddle they paste their Paddle **transaction id** into:

    ftag license activate txn_01h...

That id goes to a small proxy worker that holds the Paddle API key. The
worker calls Paddle, confirms the transaction is `completed`, and returns
an Ed25519-signed **attestation** of the form `<payload_b64>.<sig_b64>`:

    {
      "sub":  "buyer@example.com",
      "tier": "pro",
      "txn":  "txn_01h...",          # so we can refresh later
      "iat":  1716336000,
      "exp":  1718928000             # ~30 days out; refreshed periodically
    }

The attestation is stored at ~/.filetagger/license.key and verified offline
against the embedded public key below. When `exp` is within REFRESH_WINDOW,
the CLI silently re-fetches a fresh attestation (rate-limited to once a day).
After `exp`, there is a GRACE_WINDOW during which the cached license still
counts as valid in case the worker / network is unreachable.
"""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Embedded public key (Ed25519, raw 32 bytes, base64url-encoded, no padding).
#
# The matching private key lives only inside the verify worker (see worker/).
# Regenerate with `python worker/keygen.py` and paste the public key here.
# ---------------------------------------------------------------------------

PUBLIC_KEY_B64 = "b4-nFJdFO6Oti50bNBGxyonf3t8Mbjl5EfISv2w9UU0"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

# Where the CLI sends transaction ids to be verified. POST { "transaction_id",
# "machine_id" } -> { "key": "<attestation>" }. Override with TM_VERIFY_URL
# for staging / dev.
VERIFY_URL = os.environ.get(
    "FTAG_VERIFY_URL",
    "https://filetagger-license-verify.davidchincharashvili.workers.dev/verify",
)

# Where buyers go to purchase a license. Paddle hosted checkout link.
PURCHASE_URL = "https://buy.filetagger.dev/pro"


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

REFRESH_WINDOW_SECONDS = 7 * 24 * 3600        # start refreshing 7 days before exp
GRACE_SECONDS          = 7 * 24 * 3600        # license still valid 7 days past exp
REFRESH_RATE_LIMIT_S   = 24 * 3600            # at most one silent refresh per day
NETWORK_TIMEOUT_S      = 10


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _tm_dir() -> Path:
    return Path.home() / ".filetagger"


def license_path() -> Path:
    return _tm_dir() / "license.key"


def _refresh_state_path() -> Path:
    return _tm_dir() / "refresh.json"


def _machine_id_path() -> Path:
    return _tm_dir() / "machine.id"


def _read_stored_key() -> Optional[str]:
    p = license_path()
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def write_license_file(key: str) -> Path:
    p = license_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(key.strip() + "\n", encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    return p


def delete_license_file() -> bool:
    p = license_path()
    if p.exists():
        p.unlink()
        return True
    return False


def machine_id() -> str:
    """Stable per-machine identifier sent to the verify worker.

    Random UUID generated on first call and persisted. The worker uses it to
    detect activation abuse (one license used on hundreds of machines).
    """
    p = _machine_id_path()
    if p.exists():
        try:
            existing = p.read_text(encoding="utf-8").strip()
            if existing:
                return existing
        except OSError:
            pass
    new = uuid.uuid4().hex
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(new + "\n", encoding="utf-8")
        os.chmod(p, 0o600)
    except OSError:
        pass
    return new


def _read_refresh_state() -> dict:
    p = _refresh_state_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_refresh_state(state: dict) -> None:
    p = _refresh_state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

@dataclass
class LicenseInfo:
    valid: bool
    reason: str = ""
    email: Optional[str] = None
    tier: Optional[str] = None
    issued_at: Optional[int] = None
    expires_at: Optional[int] = None
    transaction_id: Optional[str] = None
    in_grace: bool = False

    @property
    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at < int(time.time())


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def verify_key_string(key: str) -> LicenseInfo:
    """Verify a signed attestation. Caller decides whether to honor grace."""
    if not key or "." not in key:
        return LicenseInfo(False, "malformed key")

    if PUBLIC_KEY_B64.startswith("REPLACE_ME"):
        return LicenseInfo(False, "client misconfigured (no public key)")

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        return LicenseInfo(False, "cryptography package not installed")

    try:
        payload_b64, sig_b64 = key.strip().split(".", 1)
        payload_bytes = _b64url_decode(payload_b64)
        signature = _b64url_decode(sig_b64)
    except Exception:
        return LicenseInfo(False, "malformed key")

    try:
        pub = Ed25519PublicKey.from_public_bytes(_b64url_decode(PUBLIC_KEY_B64))
        pub.verify(signature, payload_bytes)
    except InvalidSignature:
        return LicenseInfo(False, "signature does not match")
    except Exception as e:
        return LicenseInfo(False, f"verification error: {e}")

    try:
        data = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return LicenseInfo(False, "payload is not valid JSON")

    info = LicenseInfo(
        valid=True,
        email=data.get("sub"),
        tier=data.get("tier"),
        issued_at=data.get("iat"),
        expires_at=data.get("exp"),
        transaction_id=data.get("txn"),
    )

    if info.tier != "pro":
        return LicenseInfo(False, f"unexpected tier '{info.tier}'")

    now = int(time.time())
    if info.expires_at is not None:
        if info.expires_at + GRACE_SECONDS < now:
            return LicenseInfo(False, "license expired (grace period elapsed)")
        if info.expires_at < now:
            info.in_grace = True

    return info


# ---------------------------------------------------------------------------
# Worker communication
# ---------------------------------------------------------------------------

class VerifyError(RuntimeError):
    """Raised when the verify worker rejects or is unreachable."""


def _fetch_attestation(transaction_id: str, *, timeout: float = NETWORK_TIMEOUT_S) -> str:
    """POST to the verify worker. Returns the signed attestation string."""
    import urllib.request
    import urllib.error

    body = json.dumps({
        "transaction_id": transaction_id.strip(),
        "machine_id":     machine_id(),
    }).encode("utf-8")

    req = urllib.request.Request(
        VERIFY_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent":   "filetagger-cli",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("error", "")
        except Exception:
            detail = ""
        msg = f"HTTP {e.code}"
        if detail:
            msg += f": {detail}"
        raise VerifyError(msg)
    except urllib.error.URLError as e:
        raise VerifyError(f"could not reach verify server ({e.reason})")
    except Exception as e:
        raise VerifyError(str(e))

    try:
        data = json.loads(payload)
    except ValueError:
        raise VerifyError("verify server returned invalid JSON")

    key = data.get("key")
    if not key:
        raise VerifyError(data.get("error") or "verify server returned no key")
    return key


def activate_with_transaction(transaction_id: str) -> LicenseInfo:
    """Fetch an attestation for `transaction_id` and persist it.

    Raises VerifyError if the worker rejects or is unreachable. Raises
    VerifyError with a verification message if the returned attestation
    fails local signature check (should not happen unless keys diverged).
    """
    key = _fetch_attestation(transaction_id)
    info = verify_key_string(key)
    if not info.valid:
        raise VerifyError(f"signed attestation failed local verification: {info.reason}")
    write_license_file(key)
    state = _read_refresh_state()
    state["last_refresh_attempt"] = int(time.time())
    state["last_refresh_success"] = int(time.time())
    _write_refresh_state(state)
    return info


def refresh() -> LicenseInfo:
    """Re-fetch the attestation for the currently-installed license."""
    key = _read_stored_key()
    if not key:
        raise VerifyError("no license to refresh")
    info = verify_key_string(key)
    if not info.transaction_id:
        raise VerifyError("stored license has no transaction id; re-activate instead")
    return activate_with_transaction(info.transaction_id)


def _maybe_silent_refresh(info: LicenseInfo) -> None:
    """If the license is approaching expiry, try to refresh it in the background.

    Rate-limited to one attempt per REFRESH_RATE_LIMIT_S. Failures are
    swallowed — the cached license is still good (we have a grace window).
    """
    if not info.valid or not info.expires_at or not info.transaction_id:
        return
    now = int(time.time())
    if info.expires_at - now > REFRESH_WINDOW_SECONDS:
        return  # not yet in refresh window

    state = _read_refresh_state()
    last = state.get("last_refresh_attempt", 0)
    if now - last < REFRESH_RATE_LIMIT_S:
        return  # already tried recently

    state["last_refresh_attempt"] = now
    _write_refresh_state(state)
    try:
        refresh()
    except VerifyError:
        pass  # cached license is still serving us; try again tomorrow


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def current_license() -> LicenseInfo:
    """Return verified info from the stored attestation, or an invalid LicenseInfo."""
    if os.environ.get("FTAG_DEV_BYPASS_LICENSE") == "1":
        return LicenseInfo(True, tier="pro", email="dev-bypass")
    key = _read_stored_key()
    if not key:
        return LicenseInfo(False, "no license activated")
    info = verify_key_string(key)
    if info.valid:
        _maybe_silent_refresh(info)
    return info


def is_pro_active() -> bool:
    return current_license().valid


# ---------------------------------------------------------------------------
# Gate helper for CLI commands
# ---------------------------------------------------------------------------

def require_pro(feature: str) -> None:
    """Abort the CLI with a friendly message if Pro is not active."""
    info = current_license()
    if info.valid:
        return

    import typer

    typer.echo("", err=True)
    typer.echo(f"  '{feature}' is a FileTagger Pro feature.", err=True)
    typer.echo(f"  Status: {info.reason}.", err=True)
    typer.echo("", err=True)
    typer.echo(f"  Get a license:   {PURCHASE_URL}", err=True)
    typer.echo("  Activate:        ftag license activate <TRANSACTION_ID>", err=True)
    typer.echo("", err=True)
    raise typer.Exit(2)
