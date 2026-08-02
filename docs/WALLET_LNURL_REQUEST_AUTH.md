# Wallet + LNURL protected-request authentication

Protected Wallet/LNURL v2 requests use one canonical scheme:

```http
Authorization: PoP sess_<opaque>
Bastion-Request-Timestamp: 2026-08-02T12:00:00Z
Bastion-Request-Nonce: <unique random value>
Bastion-Request-Body-Hash: <lowercase SHA-256 hex>
Bastion-Request-Signature: <device/session-key signature>
Bastion-Principal: <server-issued product pseudonym>
```

The signature digest is SHA-256 over newline-delimited `METHOD`, canonical
request target, body hash, timestamp, and nonce. The canonical target is the
exact path followed by query pairs sorted by encoded key and value. The body
hash covers the exact bytes sent. Timestamps must be timezone-aware and within
the configured skew; a nonce is accepted once per session.

The principal header is only a consistency assertion. Bastion resolves the
principal, device, session, entitlement, scopes, role, and plan from server
state and rejects a mismatch. A Wallet Proof or LNURL-auth callback cannot be
used in place of these headers.

`X-Bastion-Session` and `X-Bastion-*` remain a temporary Access v1 SDK
compatibility path. They are not accepted by Wallet/LNURL v2 router
dependencies and will be removed after Prompt 67/68 SDK migration. Bearer
tokens are rejected.

High-risk operations additionally require fresh, unrevoked evidence bound to
the exact action and Human Intent hash. Generic login freshness is insufficient.
Policy responses use stable decisions such as `deny`, `step_up_required`,
`upgrade_required`, `metric_not_allowed`, `quota_exceeded`, and `revoked`.

Bastion verifies signatures. It never accepts a seed phrase, mnemonic, xprv,
wallet private key, or Lightning wallet seed.
