# LNURL Security

## LNURL k1 Lifecycle and Replay Protection

Bastion `k1` challenges are generated as 32 cryptographically random bytes and exposed only as 64-character lowercase hexadecimal strings. Registry lookup stores an HMAC-SHA256 lookup hash derived from the server pepper; non-secret SHA-256 fingerprints are used for audit correlation.

Administrative k1/key/challenge revocation is resolved through the Access
Revocation Registry while atomic single-use consumption remains in the K1 Registry.
Pay requests, payment proofs, Lightning Addresses and withdraw requests are also
independently revocable; revocation preserves factual settlement history. See
[`WALLET_LNURL_REVOCATION.md`](WALLET_LNURL_REVOCATION.md).

Each `k1` has an explicit purpose, LNURL action where applicable, internal Bastion action, expected domain, short TTL, and optional binding hashes for principal, device, session, payment, withdraw, or recovery attempts. Critical step-up, withdrawal, recovery, business, and sovereign approvals require a policy hash produced from an external canonical intent.

Consumption is single-use. The registry performs a guarded active-to-consumed transition, so concurrent callbacks produce exactly one successful consumer and all replays are rejected. A valid `k1` does not prove wallet signature validity, entitlement, authorization, withdrawal permission, recovery approval, or protected API access.

Failure recording increments known challenge failure counts. Critical one-attempt challenges become terminal after the first invalid proof when configured; routine login can allow a bounded number of attempts within TTL. Active challenges may be revoked by raw `k1` or by bounded binding selectors. Stale active challenges are expired idempotently, while terminal records remain available for short security retention and audit evidence.

The SQL database remains the authoritative production store; Redis may only accelerate lookups and must not make a used `k1` valid after cache loss. Logs, metrics, and audit events include registry id, `k1` fingerprint, purpose, action, status, domain hash, policy hash, timestamps, and reason codes only. Raw `k1`, raw signatures, wallet keys, callback URLs, session tokens, preimages, and recovery material must never be logged.

This prompt does not implement the complete LNURL-auth callback verifier, payment settlement, withdrawals, Wallet Principal creation, Device Binding, or PoP Session issuance.

## LNURL-pay Subscription Requests

The LNURL-pay subscription request service creates only the initial wallet-facing `payRequest` for subscription checkout. A created request is not a BOLT-11 invoice, not a settlement proof, and not a Subscription Entitlement. Later services must issue invoices, verify settlement, bind Payment Proofs, and apply entitlement policy before any access is activated.

All LNURL-pay amounts are represented as integer millisatoshis. The callback URL is derived from a configured trusted public base URL and an opaque request reference; it must not expose principal hashes, plan names, database IDs, raw idempotency keys, wallet identifiers, or secrets.

Metadata is deterministic raw LNURL metadata JSON and must include `text/plain`. `payerData` and `commentAllowed` are only declarations in this phase: comments and payerData values are untrusted and cannot authorize access, select plans, change amounts, assign roles, complete recovery, or bypass Policy Engine decisions.

## LNURL comment security boundary

LNURL comments must never be inserted into LLM system prompts, developer instructions, shell commands, SQL queries, policy expressions, webhook URLs, role assignments, or unescaped HTML. If later shown to an operator, they must be labeled `untrusted_external_metadata`, escaped for display, and isolated from automation/tool instructions.

Dangerous strings such as “upgrade me to enterprise”, refund approvals, withdrawal approvals, prompt-injection text, private keys, seeds, Access Passes, session tokens, and preimages remain inert metadata and must not change payment, entitlement, principal, recovery, or authorization state.

## payerData.auth security boundary

`payerData.auth` proves control of a Lightning wallet linking key for the bound payment request/domain/product/policy. The k1 challenge is short-lived and single-use, exact callback retries are idempotent, and modified replays are rejected. Raw payerdata, keys, k1 values, and signatures must not be logged or stored by default. Settlement verification, Payment Proof creation, Subscription Entitlement issuance, Device Binding, PoP sessions, and Policy Engine authorization remain separate stages.
