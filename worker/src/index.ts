/**
 * FileTagger license verify proxy.
 *
 * POST /verify  { transaction_id, machine_id }
 *   1. Look up the Paddle transaction with the seller API key.
 *   2. Confirm status === "completed" and the price id matches our Pro product.
 *   3. Mint an Ed25519-signed attestation the CLI can verify offline.
 *   4. Return { key } where key is "<payload_b64url>.<sig_b64url>".
 *
 * The Paddle API key NEVER leaves this worker. The CLI ships only the
 * matching public key.
 */

export interface Env {
  /** Paddle API key (server-side; vendor secret). */
  PADDLE_API_KEY: string;
  /** Comma-separated allowlist of Paddle price ids that grant Pro. */
  PADDLE_PRICE_IDS: string;
  /**
   * Ed25519 private key as a JWK JSON string:
   *   {"kty":"OKP","crv":"Ed25519","d":"...","x":"..."}
   * Generate with worker/keygen.py.
   */
  ED25519_PRIVATE_JWK: string;
  /** Optional. Days until an attestation expires. Default 30. */
  ATTESTATION_TTL_DAYS?: string;
  /** Optional. Use "sandbox" to hit Paddle sandbox. Default production. */
  PADDLE_ENV?: string;
}

interface VerifyBody {
  transaction_id?: unknown;
  machine_id?: unknown;
}

interface PaddleTxn {
  data?: {
    id: string;
    status: string;
    customer_id?: string;
    items?: Array<{ price?: { id?: string } }>;
  };
}

interface PaddleCustomer {
  data?: { email?: string };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function b64url(bytes: Uint8Array): string {
  let s = btoa(String.fromCharCode(...bytes));
  return s.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function paddleBase(env: Env): string {
  return env.PADDLE_ENV === "sandbox"
    ? "https://sandbox-api.paddle.com"
    : "https://api.paddle.com";
}

async function paddleGet<T>(path: string, env: Env): Promise<T> {
  const res = await fetch(paddleBase(env) + path, {
    headers: {
      "Authorization": `Bearer ${env.PADDLE_API_KEY}`,
      "Paddle-Version": "1",
    },
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`paddle ${path} -> ${res.status} ${detail.slice(0, 200)}`);
  }
  return (await res.json()) as T;
}

async function loadSigningKey(env: Env): Promise<CryptoKey> {
  const jwk = JSON.parse(env.ED25519_PRIVATE_JWK);
  return crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "Ed25519" },
    false,
    ["sign"],
  );
}

async function mintAttestation(
  email: string,
  txnId: string,
  ttlDays: number,
  key: CryptoKey,
): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    sub:  email,
    tier: "pro",
    txn:  txnId,
    iat:  now,
    exp:  now + ttlDays * 86_400,
  };
  // Canonical JSON: sorted keys, no whitespace. The CLI does not depend on
  // exact byte layout (it verifies the signature over whatever bytes arrive),
  // but keeping it stable makes audit logs comparable.
  const ordered: Record<string, unknown> = {};
  for (const k of Object.keys(payload).sort()) ordered[k] = (payload as any)[k];
  const payloadBytes = new TextEncoder().encode(JSON.stringify(ordered));
  const sig = new Uint8Array(
    await crypto.subtle.sign({ name: "Ed25519" }, key, payloadBytes),
  );
  return `${b64url(payloadBytes)}.${b64url(sig)}`;
}

async function handleVerify(req: Request, env: Env): Promise<Response> {
  let body: VerifyBody;
  try {
    body = await req.json();
  } catch {
    return json({ error: "invalid JSON body" }, 400);
  }

  const txnId = typeof body.transaction_id === "string" ? body.transaction_id.trim() : "";
  if (!txnId.startsWith("txn_")) {
    return json({ error: "transaction_id must start with 'txn_'" }, 400);
  }

  let txn: PaddleTxn;
  try {
    txn = await paddleGet<PaddleTxn>(`/transactions/${encodeURIComponent(txnId)}`, env);
  } catch (e) {
    return json({ error: `paddle lookup failed: ${(e as Error).message}` }, 502);
  }

  if (!txn.data) {
    return json({ error: "transaction not found" }, 404);
  }
  if (txn.data.status !== "completed") {
    return json(
      { error: `transaction status is '${txn.data.status}', not 'completed'` },
      409,
    );
  }

  const allowed = new Set(
    env.PADDLE_PRICE_IDS.split(",").map((s) => s.trim()).filter(Boolean),
  );
  const priceIds = (txn.data.items ?? [])
    .map((it) => it.price?.id)
    .filter((x): x is string => Boolean(x));
  if (!priceIds.some((id) => allowed.has(id))) {
    return json({ error: "transaction is not for a Pro product" }, 403);
  }

  let email = "unknown@example.com";
  if (txn.data.customer_id) {
    try {
      const cust = await paddleGet<PaddleCustomer>(
        `/customers/${encodeURIComponent(txn.data.customer_id)}`,
        env,
      );
      if (cust.data?.email) email = cust.data.email;
    } catch {
      // Non-fatal: we still issue the attestation, just without an email.
    }
  }

  const ttl = Number(env.ATTESTATION_TTL_DAYS ?? "30");
  const signingKey = await loadSigningKey(env);
  const key = await mintAttestation(email, txnId, ttl, signingKey);
  return json({ key });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (req.method === "POST" && url.pathname === "/verify") {
      return handleVerify(req, env);
    }
    if (req.method === "GET" && url.pathname === "/healthz") {
      return json({ ok: true });
    }
    return json({ error: "not found" }, 404);
  },
};
