# LNURL Security

## LNURL k1 Lifecycle and Replay Protection

Bastion `k1` challenges are generated as 32 cryptographically random bytes and exposed only as 64-character lowercase hexadecimal strings. Registry lookup stores an HMAC-SHA256 lookup hash derived from the server pepper; non-secret SHA-256 fingerprints are used for audit correlation.

Each `k1` has an explicit purpose, LNURL action where applicable, internal Bastion action, expected domain, short TTL, and optional binding hashes for principal, device, session, payment, withdraw, or recovery attempts. Critical step-up, withdrawal, recovery, business, and sovereign approvals require a policy hash produced from an external canonical intent.

Consumption is single-use. The registry performs a guarded active-to-consumed transition, so concurrent callbacks produce exactly one successful consumer and all replays are rejected. A valid `k1` does not prove wallet signature validity, entitlement, authorization, withdrawal permission, recovery approval, or protected API access.

Failure recording increments known challenge failure counts. Critical one-attempt challenges become terminal after the first invalid proof when configured; routine login can allow a bounded number of attempts within TTL. Active challenges may be revoked by raw `k1` or by bounded binding selectors. Stale active challenges are expired idempotently, while terminal records remain available for short security retention and audit evidence.

The SQL database remains the authoritative production store; Redis may only accelerate lookups and must not make a used `k1` valid after cache loss. Logs, metrics, and audit events include registry id, `k1` fingerprint, purpose, action, status, domain hash, policy hash, timestamps, and reason codes only. Raw `k1`, raw signatures, wallet keys, callback URLs, session tokens, preimages, and recovery material must never be logged.

This prompt does not implement the complete LNURL-auth callback verifier, payment settlement, withdrawals, Wallet Principal creation, Device Binding, or PoP Session issuance.
