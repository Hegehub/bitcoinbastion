# Access Request Signing

Protected API calls require Proof‑of‑Possession.  Each request must be signed with the session's device key to prevent replay and tampering.  The client attaches the following headers:

- `X-Bastion-Session`: your current session token (issued by `POST /access/sessions`).
- `X-Bastion-Timestamp`: the current UNIX timestamp in seconds.
- `X-Bastion-Nonce`: a unique random string for this request (at least 8 bytes of entropy).
- `X-Bastion-Body-Hash`: a base64url‑encoded SHA‑256 hash of the request body.  For empty bodies use the SHA‑256 of the empty string.
- `X-Bastion-Signature`: the base64url‑encoded Ed25519 signature over the digest described below.

## Digest format

To compute the signature:

1. Compute `body_hash = SHA256(request body)`.  Use a canonical JSON representation if signing JSON.
2. Construct the digest string as:

```
digest = method + "\n" + path + "\n" + body_hash + "\n" + timestamp + "\n" + nonce
```

Where `method` is the upper‑case HTTP method and `path` is the absolute path (e.g. `/api/v1/trace/report`).  `timestamp` is the value of `X-Bastion-Timestamp` and `nonce` is the value of `X-Bastion-Nonce`.  Use newline (`\n`) to separate fields exactly as shown.

3. Compute `signature = sign(digest, device_private_key)` using Ed25519.
4. Include the signature in `X-Bastion-Signature`.  Do **not** include the raw private key or certificate in any header.

## Timestamp freshness and nonce uniqueness

- **Timestamp:** The server accepts timestamps within a skew window configured by `ACCESS_REQUEST_MAX_CLOCK_SKEW_SECONDS` (e.g. ±120 seconds).  Requests outside this window return `timestamp_stale`.
- **Nonce:** Each nonce must be unique per session.  Nonces are stored for the duration of the session; reusing a nonce returns `nonce_reused`.
- **Body hash:** Ensures that a signature cannot be replayed with a different body.  Tampering with the body will produce a different hash and result in `invalid_request_signature`.

## Which requests require signatures?

- **Protected APIs**: All POST/PUT/DELETE requests and sensitive GET requests to premium endpoints require signatures.  These endpoints are annotated with `x-proof-of-access-required` in the OpenAPI specification.
- **Public APIs**: Health, status pages, marketing data and `payment-intents` endpoints do not require a session or signature.
- **Human‑intent signatures**: High‑impact actions (e.g. creating delegated passes, rotating plans, lockdown) may require an additional `X-Bastion-Intent-Signature` header computed with a separate signing key.  Those flows are documented separately.

## Signing examples

### Signed GET request

Suppose you have session `sess_abc` and want to fetch your entitlements.  The request body is empty so `body_hash` is the SHA‑256 of an empty string.

```
GET /api/v1/access/me/entitlements HTTP/1.1
Host: api.bitcoinbastion.org
X-Bastion-Session: sess_abc
X-Bastion-Timestamp: 1720283800
X-Bastion-Nonce: b7c2df883fa2451e
X-Bastion-Body-Hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
X-Bastion-Signature: KA9V... (signature omitted)
```

### Signed POST request with JSON body

```
POST /api/v1/trace/report HTTP/1.1
Host: api.bitcoinbastion.org
X-Bastion-Session: sess_abc
X-Bastion-Timestamp: 1720284000
X-Bastion-Nonce: 84a2596de3b147c2
Content-Type: application/json
Body: {"txid":"...","analysis_level":"basic"}
X-Bastion-Body-Hash: 8e7dd61da7b97b9325ab73e2ced5e348... (hash of the JSON)
X-Bastion-Signature: Lm6c... (signature omitted)
```

The digest string would be:

```
POST
/api/v1/trace/report
8e7dd61da7b97b9325ab73e2ced5e348...
1720284000
84a2596de3b147c2
```

which is then signed with your device key.

### Replay protection

If you reuse the same `nonce` or `timestamp`/`nonce` combination, the server returns:

```json
{
  "code": "nonce_reused",
  "message": "The nonce has already been used for this session."
}
```

### Body tampering

If the body hash does not match the content, the server returns:

```json
{
  "code": "invalid_request_signature",
  "message": "Request signature verification failed."
}
```

## Why not `Authorization: Bearer`?

Bearer tokens allow anyone who obtains the token to access the API until it expires.  Proof‑of‑Access sessions are bound to the origin and device key; requests must be signed with the corresponding private key.  This eliminates single‑string bearer tokens and reduces the blast radius of leaked credentials.

## SDK guidance

- SDKs should manage the per‑session device key in secure local storage.
- Always synchronise time with a trusted source to avoid timestamp skew errors.
- Generate a unique random nonce per request.  A UUID or 128‑bit random value encoded as hex is sufficient.
- Compute the body hash exactly; do not include whitespace differences or canonicalization changes.
- Ensure that the `path` used in the digest matches the exact path sent to the server (including query string if present).
