# LNURL-auth Callback Security

The LNURL-auth callback verifier handles wallet callbacks containing `k1`, `key`, `sig`, and optionally `action`. It proves control of the domain-specific LNURL-auth linking key only.

## Verification Contract

- `k1` must be exactly 32 bytes represented as 64 lowercase hexadecimal characters.
- `key` must be a compressed secp256k1 public key.
- `sig` must be a bounded DER-encoded ECDSA signature.
- The signature is verified against the exact 32-byte k1 challenge using secp256k1 ECDSA.
- The callback action must match the server-side challenge action.
- The callback host and stored challenge auth domain must match the configured stable auth domain.

## Single-Use Guarantee

The verifier checks the k1 registry for the active challenge, verifies the signature, and then atomically consumes k1 through the registry. Concurrent valid callbacks may both pass cryptographic verification, but only one can consume k1 successfully.

## Privacy and Handoff

The raw linking public key is used transiently for signature verification. Principal lookup uses an HMAC-SHA256 hash of the compressed public key, and audit uses safe fingerprints only. The verifier returns a `VerifiedLNURLAuthProof` handoff for the Lightning Principal service.

## Public Responses

Wallet-facing responses are LNURL compatible:

- success: `{ "status": "OK" }`
- failure: `{ "status": "ERROR", "reason": "Authentication request could not be verified." }`

Detailed reason codes are kept internally for audit and tests. Public errors do not reveal whether a k1 exists, was expired, was reused, or failed cryptographic verification.

## Boundary

The callback verifier does not create a Lightning Principal, bind a device, issue a Proof-of-Possession session, issue an entitlement, issue an Access Certificate, or authorize protected API access. Policy Engine, revocation, device binding, entitlement, audit chain, and PoP session services remain mandatory.

## Cryptographic Limitation

This implementation uses the repository's existing `cryptography` dependency for secp256k1 ECDSA verification and enforces strict compressed public keys and DER parsing. Low-S canonicality is enforced in the service before verification.
