"""CLI handlers for `ftag license ...` commands."""

from __future__ import annotations

import time

import typer

from ...licensing import (
    PURCHASE_URL,
    VerifyError,
    activate_with_transaction,
    current_license,
    delete_license_file,
    license_path,
    refresh,
)


def _format_expiry(ts: int | None) -> str:
    if ts is None:
        return "never"
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def handle_activate(transaction_id: str) -> None:
    typer.echo(f"Contacting license server for {transaction_id}...")
    try:
        info = activate_with_transaction(transaction_id)
    except VerifyError as e:
        typer.echo(f"Activation failed: {e}", err=True)
        typer.echo("", err=True)
        typer.echo("Things to check:", err=True)
        typer.echo("  - The transaction id starts with 'txn_' and matches your Paddle receipt", err=True)
        typer.echo("  - The purchase has finished processing on Paddle's side", err=True)
        typer.echo("  - You are online", err=True)
        raise typer.Exit(1)

    typer.echo(f"Activated FileTagger Pro for {info.email}")
    typer.echo(f"  Attestation expires: {_format_expiry(info.expires_at)}  (auto-refreshes near expiry)")
    typer.echo(f"  Key stored at:       {license_path()}")


def handle_status() -> None:
    info = current_license()
    if info.valid:
        typer.echo("FileTagger Pro: ACTIVE" + ("  (in grace period)" if info.in_grace else ""))
        if info.email and info.email != "dev-bypass":
            typer.echo(f"  Licensed to:         {info.email}")
        if info.email == "dev-bypass":
            typer.echo("  (FTAG_DEV_BYPASS_LICENSE is set)")
        else:
            typer.echo(f"  Attestation expires: {_format_expiry(info.expires_at)}")
            if info.transaction_id:
                typer.echo(f"  Paddle transaction:  {info.transaction_id}")
        typer.echo(f"  Key file:            {license_path()}")
        if info.in_grace:
            typer.echo("")
            typer.echo("  The cached attestation is past its expiry but still inside the")
            typer.echo("  offline grace window. Run `ftag license refresh` when you're online.")
    else:
        typer.echo("FileTagger Pro: not active")
        typer.echo(f"  Reason: {info.reason}")
        typer.echo("")
        typer.echo(f"  Get a license:   {PURCHASE_URL}")
        typer.echo("  Activate:        ftag license activate <TRANSACTION_ID>")


def handle_refresh() -> None:
    typer.echo("Refreshing license from server...")
    try:
        info = refresh()
    except VerifyError as e:
        typer.echo(f"Refresh failed: {e}", err=True)
        raise typer.Exit(1)
    typer.echo(f"Refreshed. New expiry: {_format_expiry(info.expires_at)}")


def handle_deactivate() -> None:
    if delete_license_file():
        typer.echo("License removed.")
    else:
        typer.echo("No license file to remove.")
