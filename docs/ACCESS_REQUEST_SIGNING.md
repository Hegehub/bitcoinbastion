# Access Request Signing

Proof-of-Possession request signing protects protected Bastion APIs after a session is created. `Authorization: Bearer` is not sufficient because bearer tokens can be replayed without proving device possession or request integrity.

## Required headers

- `X-Bastion-Session`
- `X-Bastion-Timestamp`
- `X-Bastion-Nonce`
- `X-Bastion-Body-Hash`
- `X-Bastion-Signature`

## Digest format

The canonical digest is:

```text
SHA256(method || path || body_hash || timestamp || nonce)
```

Implementations should use deterministic delimiters internally, uppercase methods, include the query string in `path`, hash the exact request body bytes/canonical JSON, and sign either the digest bytes or canonical digest representation consistently with the Access signature suite.

## Replay and tamper protection

- Timestamp freshness is bounded by `ACCESS_REQUEST_MAX_CLOCK_SKEW_SECONDS` or the compatibility setting `ACCESS_REQUEST_MAX_SKEW_SECONDS`.
- Nonces must be unique per session and rejected on reuse.
- Body hash changes when JSON body content changes.
- A copied signature must fail if method, path, body hash, timestamp, nonce, session, origin, or device key differs.

## Public versus protected requests

Public health/status and public presentation endpoints may be unsigned. Premium/private endpoints, critical actions, child-key/delegated-pass management, treasury/policy operations, business/enterprise trace, and lockdown require Proof-of-Access session checks and request signing when policy requires it.

## Signed GET example

```http
GET /api/v1/access/me
X-Bastion-Session: sess_redacted
X-Bastion-Timestamp: 2026-07-07T00:00:00Z
X-Bastion-Nonce: nonce_redacted
X-Bastion-Body-Hash: sha256:e3b0c44298fc...
X-Bastion-Signature: sig_redacted
```

## Signed POST example

```http
POST /api/v1/access/lockdown
Content-Type: application/json
X-Bastion-Session: sess_redacted
X-Bastion-Timestamp: 2026-07-07T00:00:00Z
X-Bastion-Nonce: nonce_redacted
X-Bastion-Body-Hash: sha256:body_hash_redacted
X-Bastion-Signature: sig_redacted

{"scope":"current_pass","reason":"suspected_device_compromise","recovery_mode":true}
```

## Failed replay example

Reusing the same `X-Bastion-Nonce` with the same session must fail with `nonce_reused` or `invalid_request_signature`.

## Failed body tampering example

Changing a JSON field after signing changes `X-Bastion-Body-Hash`; the verifier must reject the request with `invalid_request_signature`.

## SDK guidance

SDKs should keep raw Access Pass material out of long-lived client state, create a PoP session, generate a fresh timestamp and nonce per protected request, hash the body, sign the digest with a Bastion device signer, and redact session tokens, signatures, passes, recovery phrases, and private-key material from logs.
