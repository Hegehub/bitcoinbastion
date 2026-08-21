# Device-bound Access issuance

## Security model

A2 uses **PI1, atomic verify-and-issue**. An eligible frozen Checkout is the
immutable issuance intent. The browser sends only the Checkout identity, a
device public key, and later the device signature. Price, duration, capability,
scope, terms, eligibility, and expiry remain backend-owned.

The existing Feature-67 Ed25519 suite is reused. The server creates 256 bits of
cryptographic nonce material and a canonical JSON payload under the
`BastionProofOfAccess:v1:access_challenge` signing domain. The payload binds the
`access.issue` operation, Checkout, Offer revision, capability, sorted scopes,
terms version, device-key fingerprint, issue time, expiry, and protocol version.

PoP proves only possession of the private key corresponding to the supplied
device public key for that exact payload. It does not prove payment, legal
identity, or authorization. Eligibility is checked both before challenge
creation and immediately before verification/issuance.

## Persistence and atomicity

`access_issuance_challenges` persists the exact payload, payload hash, Checkout,
device, operation, expiry, and consumption state. `access_issued_grants` is a
non-secret C1 server-side grant with exactly one row per Checkout. Signature
verification, challenge consumption, certificate creation, grant creation, and
Checkout transition occur in the API transaction. A failure rolls all of them
back. The unique Checkout grant constraint is the final concurrent-issuance
guard; retries return the existing semantic grant.

The issued grant derives Offer revision, capability, scopes, terms, and expiry
only from the Checkout. It exposes no raw Access Pass or bearer credential.
The generated issuer pass is deliberately not projected by the A2 endpoint.

## Operation security matrix

| Operation | Kind | Auth | PoP | Human Intent | Idempotency | Replay |
|---|---|---|---|---|---|---|
| Offer read | read | public | no | no | n/a | n/a |
| Checkout create/read | mutation/read | public acquisition | no | explicit checkout click | hashed intent | checkout key |
| Issuance challenge | mutation | eligible Checkout | device context target | no separate ceremony | explicit action | persistent nonce |
| Verify + issue | mutation | eligible Checkout | required, Ed25519 | signature is explicit device intent | one grant/Checkout | single-use challenge |
| Issued summary | read | safe opaque grant reference | no | no | n/a | no mutation |

## Secret boundary

The service accepts a public key and signature. No API or DTO has a private-key
field. The private key stays in the secure device provider, and no localStorage
fallback is authorized. Internal issuer keys, generated raw passes, provider
configuration, and `ACCESS_SECRET_CANARY_NEVER_BROWSER` are absent from the
safe Challenge and Grant DTOs.

## Rollback

The issuance challenge/grant tables, PI1 service, endpoints, generated bindings,
and UI integration can be disabled independently. A1 Offers, frozen Checkouts,
payment binding, and caller-price protection remain. If A2 is disabled,
issuance must report unavailable; it must never fall back to unsigned or
browser-authoritative issuance.
