# Wallet PoP Request Signing

Wallet proof is **not** used to sign each API request. After a wallet proof,
Device Binding, entitlement check, and Policy Engine pre-session decision create
a short-lived PoP session, routine protected API requests are signed by the
client-controlled session key.

## Required headers

```http
Authorization: PoP sess_<opaque-session-token>
Bastion-Request-Timestamp: <unix-seconds>
Bastion-Request-Nonce: <base64url-random-value>
Bastion-Request-Body-Hash: <lowercase-sha256-hex>
Bastion-Request-Signature: <base64url-signature>
```

`Bastion-Principal` is optional and is only a consistency check. Identity is
always resolved from the verified server-side session.

`Authorization: Bearer` and raw Access Pass, wallet proof, Bitcoin address, or
LNURL linking-key authorization are rejected.

## Canonical request format

The signed payload is a versioned UTF-8 string:

```text
BASTION-POP-V1
<METHOD>
<NORMALIZED_PATH>
<CANONICAL_QUERY>
<BODY_SHA256>
<TIMESTAMP>
<NONCE>
<SESSION_BINDING>
```

The request digest is `SHA256(UTF8(canonical_request))`. Ed25519 signs that
digest using the existing Access signature-suite context. The session binding is
the non-secret session lookup hash/fingerprint; the raw session token is never
placed in the canonical request or logs.

## Canonicalization rules

* Methods are uppercase and limited to `GET`, `POST`, `PUT`, `PATCH`, `DELETE`,
  `HEAD`, and `OPTIONS`.
* Paths must be the effective ASGI path, begin with `/`, and contain no control
  characters. Repeated slashes, trailing slashes, UTF-8 segments, and
  percent-encoding are preserved rather than silently collapsed.
* Query strings preserve duplicates, keep blank values, percent-encode using
  RFC3986 unreserved characters, and sort by normalized key then value.
* Body hash is SHA-256 of the exact raw body bytes. JSON is never parsed and
  reserialized before hashing.

## Timestamp and nonce policy

Timestamps are integer Unix seconds. Default skew is 90 seconds. Nonces are
base64url values that decode to 16-64 bytes and are unique per session. Nonce
records are stored as HMAC-SHA256 commitments scoped to the session and are
consumed atomically via the durable `wallet_session_nonces` unique constraint in
production.

## Authorization boundary

The PoP verifier authenticates the request and returns a verified context. It is
not the Policy Engine and does not grant business authorization. Policy still
must evaluate scopes, plan, quota, object access, business roles, risk,
revocation state, and any step-up requirements.

## SDK vectors

Deterministic fixtures live in `tests/fixtures/wallet_pop_request_vectors.json`.
They contain non-secret test public keys, canonical requests, request digests,
and signatures for SDK and CLI compatibility tests.
