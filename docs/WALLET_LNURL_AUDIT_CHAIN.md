# Wallet and LNURL Audit Chain

## Canonical chain and purpose

`AccessAuditChain` is the canonical security history for Access, Wallet-first,
LNURL, recovery, revocation and PayRegister security events. Wallet and LNURL
modules are event builders/projections into that writer; operational logs, metrics,
SIEM exports, Trace business events and proof packets are projections and are not
independent authorization or audit authorities. Audit proves history—it never grants
permission or replaces a Policy Engine decision.

The chain is **tamper-evident and integrity-verifiable**, not automatically immutable
or externally anchored. WORM storage and transparency checkpoints are separate
deployment capabilities.

## Canonical envelope and hashing

Every event has a version, category, status, severity, retention class, stable chain
ID (`access-security`), sequence, event type, UTC timestamp, pseudonymous actor and
subject references, safe policy/crypto context, correlation hashes and allowlisted
details. The event hash is:

```text
SHA256(previous_event_hash || chain_id || sequence_number || canonical_json(event))
```

Canonical JSON has sorted keys and normalized UTC timestamps. The hash input excludes
the resulting event hash itself. Verification compares hashes in constant time and
detects payload changes, previous-hash breaks, and missing/duplicate sequences. It
reports damage and never repairs it automatically.

## Concurrency and idempotency

Append reads the chain tail with a database row lock, allocates the next sequence,
and relies on unique `(chain_id, sequence_number)` and `(chain_id,
idempotency_key_hash)` constraints. Conflicts retry at most three times and then fail
explicitly. Callback, settlement, revocation, recovery and session producers supply
peppered or SHA-256 idempotency hashes; a semantic retry returns the existing event.
Event creation and the protected state transition should share one transaction.
Critical operations fail closed when the event cannot be durably flushed.

## Taxonomy and privacy

The taxonomy covers wallet challenge/proof/principal/device/session/step-up,
LNURL-auth/pay/verify/withdraw, Lightning Address routing, payerData.auth,
entitlements, policy decisions, revocation/lockdown, recovery, certificates and
crypto epochs, and PayRegister payment/refund/terminal events. Invoice issuance and
settlement are separate events; settlement must precede entitlement issuance.

Raw addresses, linking keys, k1, signatures, session tokens, Access Passes, private
keys, seeds/mnemonics, xprv/tprv/WIF, BOLT-11 invoices, preimages, payerData personal
fields and comments are rejected before persistence. Canonical events contain only
hashes/fingerprints, stable codes and explicitly safe metadata. Error messages never
echo rejected values.

## Severity, retention, access and export

Severity is `info`, `notice`, `warning`, `high`, or `critical`. Retention is
`transient`, `operational`, `security`, `compliance`, or `legal_hold`; deployments
must configure bounded retention. Privacy-sensitive details belong outside the
minimal chain envelope in governed storage so their expiry does not remove middle
chain events. Operator queries remain policy-protected and paginated. SIEM and proof
packet exports include event/previous hashes, chain ID, sequence and policy hash, but
never forbidden metadata.

## Verification, backup and incidents

Run recent-segment verification periodically and full verification on demand. On a
failure, preserve the database, chain head and restored backup; do not append a
purported repair to the damaged chain. Raise an incident through an independent
operational channel. Backups include canonical events and must be verified after
restore; compare an external checkpoint when available to detect rollback.

Known limitation: the current chain has database-enforced sequencing but no external
WORM anchor. External transparency checkpoint publication is handled separately.

