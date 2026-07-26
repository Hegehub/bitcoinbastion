# Access Integrity Score 2.0

> **Access Integrity Score is an advisory security posture signal. It does not
> grant access and cannot override Policy Engine decisions.**

> **A valid LNURL-auth proof demonstrates control of a domain-specific Lightning
> wallet key. It is not proof of control over an on-chain Bitcoin treasury address.**

## Model and weights

Version 2.0 deterministically evaluates server-verified evidence. Its explicit 100
points are wallet proof (15), LNURL-auth (10), device (15), PoP session (15),
entitlement/payment settlement (10), policy and revocation (10), recovery (10),
privacy (5), delegation/Business controls (5), and Access Certificate/offline/
high-assurance controls (5). `not_applicable` evidence is excluded and remaining
applicable points are normalized; missing required evidence receives no points.

Bands are excellent (90–100), strong (75–89), guarded (55–74), restricted (30–54),
and critical (0–29). Policy hints may recommend step-up, short sessions, read-only,
recovery or lockdown, but the Policy Engine independently checks actor proof, device,
session, entitlement, scopes, metrics, quota, objects, revocation and Human Intent.

## Signals and hard caps

Wallet evidence distinguishes BIP-322 from compatibility signatures, applies
freshness, and awards no hardware assurance for client metadata alone. LNURL evidence
requires a valid callback, expected consumed k1, matching action/domain, and uses only
evidence commitments. Invoice issuance earns no settlement assurance; entitlement
posture becomes healthy only after verified settlement when payment is relevant.
Email/name, comments, Lightning Addresses and payment routing are not identity factors.

Positive points cannot conceal hard failures. Caps include revoked principal/policy
bypass (10), revoked device/reused k1 (20), bearer-only protected session (25), raw
private material handling (0), accepted replay (15), support-only recovery/high-risk
compatibility (29), and stale revocation/global raw-address identity (54).

## Caching, audit and privacy

The optional cache key contains the principal pseudonym and policy, revocation,
entitlement, device and session versions. Wallet/LNURL proof events, replay,
device/session/entitlement/recovery/lockdown changes, epoch changes, certificates and
offline packs invalidate cached posture. Cache values contain results and evidence
commitments—not raw evidence.

Material score changes and critical signals use canonical audit event types. Metrics
use only low-cardinality band, actor type, category/reason and score-version labels.
Results expose pseudonymous hashes and safe evidence codes, never addresses, linking
keys, k1, signatures, session tokens, recovery material, invoices or private keys.

## Limitations and incidents

This is a deterministic posture summary, not anonymity, legal compliance, hardware
attestation, PQ verification, authentication, or authorization. It evaluates metadata
produced by existing verifiers and does not inspect wallet private material. Critical
signals should trigger server-side recalculation, cache invalidation, Policy Engine
review and the established revocation/lockdown incident procedure.

