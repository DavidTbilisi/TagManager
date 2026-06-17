# FileTagger License Verify Worker

A tiny Cloudflare Worker that sits between the `ftag` CLI and the Paddle API.

- Buyer pastes their Paddle transaction id into `ftag license activate`.
- CLI POSTs `{ transaction_id, machine_id }` to this Worker.
- Worker calls Paddle with the seller API key, confirms the transaction is
  `completed` and for a Pro price id, then mints an Ed25519-signed
  attestation the CLI can verify offline.

The CLI ships only the Ed25519 *public* key, so this Worker is the only
place that holds either the Paddle API key or the Ed25519 private key.

## One-time setup

```bash
# 1. Generate the signing keypair (run from repo root).
python worker/keygen.py
#    Paste PUBLIC_KEY_B64 into filetagger/licensing.py.
#    Save the JWK output for step 3.

cd worker
npm install

# 2. Edit wrangler.toml and set PADDLE_PRICE_IDS to your Pro Paddle price id
#    (comma-separated if you have several). For sandbox testing also
#    uncomment PADDLE_ENV = "sandbox".

# 3. Push secrets.
wrangler secret put PADDLE_API_KEY        # paste your Paddle server API key
wrangler secret put ED25519_PRIVATE_JWK   # paste the JWK from keygen.py

# 4. Deploy.
wrangler deploy
```

After deploy Wrangler prints the Worker URL, e.g.
`https://filetagger-license-verify.yourname.workers.dev`. Either:

- Put that URL in `filetagger/licensing.py` as `VERIFY_URL`, or
- Set up a custom domain (e.g. `license.filetagger.dev`) on the Worker
  and use that — easier to rotate later without breaking installed CLIs.

## Endpoints

- `POST /verify` — body `{ "transaction_id": "txn_…", "machine_id": "…" }`,
  returns `{ "key": "<attestation>" }` on success, or `{ "error": "…" }`
  with a 4xx/5xx status on failure.
- `GET /healthz` — returns `{ "ok": true }`.

## Testing without Paddle

Set `FTAG_DEV_BYPASS_LICENSE=1` in your shell and the CLI treats every gated
command as licensed. Use that for local development; do not document it for
customers.

For testing the Worker against Paddle sandbox, set `PADDLE_ENV="sandbox"`
in `wrangler.toml` and use a sandbox API key and a sandbox transaction id.
