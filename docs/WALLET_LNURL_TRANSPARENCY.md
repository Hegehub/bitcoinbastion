# Wallet/LNURL transparency checkpoints

## Purpose and threat model

The canonical implementation lives under
`app/services/wallet_auth/transparency`. General issuer signing remains centralized
under `app/services/access/crypto`; the transparency package does not introduce a
second signature format. Checkpoints make policy, issuer, revocation, credential,
recovery, offline-pack, and LNURL state transitions tamper-evident while assuming
the database, publication transport, local clocks, and operators may fail or become
partially compromised.

Transparency checkpoints are not Bitcoin consensus, proof of legal identity, or
proof that a payment settled. They do not expose user wallet data. Internal storage
is not independent public publication. Blockchain anchoring is not implemented and
no transaction is created or broadcast.

## Checkpoint and visibility types

The version-one taxonomy includes issuer-key, policy, revocation, Wallet/LNURL
schema/domain, wallet and Lightning credential, entitlement, Access Certificate,
delegation, recovery, quorum, offline-pack, LNURL payment/withdraw, Lightning
Address, compatibility-registry, audit-chain, and emergency-lockdown streams.
Unknown types fail closed. Visibility is one of `public_safe`, `operator`,
`restricted`, or `recovery_quorum_only`; unknown types default to restricted.

## Checkpoint chain and Merkle commitments

Streams are separated by checkpoint type, environment, issuer family, optional auth
domain, and optional product context. Sequence numbers start at one and increase
monotonically within a stream. Every checkpoint commits the previous checkpoint
hash; cross-stream links are rejected.

Leaves use canonical JSON and the domain-separated hash
`SHA256("BASTION_TRANSPARENCY_LEAF_V1" || 0x00 || leaf)`. Internal nodes use a
separate `BASTION_TRANSPARENCY_NODE_V1` domain. Leaves are deterministically ordered;
duplicate leaves remain explicit, and odd levels duplicate their final node. Empty
batches have a versioned deterministic root. Inclusion proofs disclose only the
requested committed leaf and sibling path.

## Privacy model

Source adapters retain context-local commitments, coarse status/policy classes, and
epochs—not raw records. Public-safe validation rejects stable principal hashes,
Bitcoin addresses, wallet keys/signatures, LNURL linking keys and k1 values,
invoices, payment hashes/preimages, payer identity, sessions, Access Passes, device
identifiers, recovery material, seeds, mnemonics, xprvs, and private keys. Product-
or stream-specific HMAC commitments reduce cross-stream correlation. Public
artifacts use an explicit field allowlist and omit source leaves by default.

Batch windows should be coarse enough for the deployment's traffic volume. Very
small source counts or fine timestamps can leak activity patterns even when records
are hashed; operators should delay publication or aggregate low-volume streams.

## Issuer signatures and PQ limitations

Checkpoints use the shared version-one Bastion issuer envelope and operational
Ed25519 implementation. The signed payload excludes signatures and mutable
publication/verification retry state. ML-DSA and SLH-DSA remain metadata-only;
fake PQ signatures are rejected, and a required unsupported suite fails closed.
No PQ assurance is claimed.

## Publication and verification

Creation and publication are separate. The supported targets are internal storage
and an allowlisted signed JSON artifact for public-safe checkpoints. External or
blockchain publication is not implemented. Publication retry is idempotent, and a
publication failure does not alter a correctly signed checkpoint.

Verification recomputes canonical payload and checkpoint hashes, verifies the
shared issuer envelope, checks stream/sequence/previous-hash continuity, optionally
recomputes the Merkle root, checks issuer epoch and visibility, and surfaces revoked
or superseded state as a structured failure. Verification bundles may include the
artifact, public-key reference, previous checkpoint reference, and one inclusion
proof, but never raw source records.

## Incident response, supersession, and retention

Signed checkpoints are never edited or deleted as a correction mechanism. A
compromised checkpoint, publication endpoint, issuer key, or stream is revoked or
superseded, and a corrective checkpoint references the affected checkpoint. The
Audit Chain records lifecycle events without recursively changing finalized roots.
Default retention is 2,555 days; legal and operational policy may require longer.

Operators should: freeze affected publication; revoke the issuer/stream target;
preserve signed evidence; build a corrective checkpoint with a new batch identity;
verify both chains; publish only if visibility permits; and document sequence gaps.

## Known limitations and future anchoring

This foundation does not run background schedules, expose final public API routes,
operate a public append-only service, provide gossip/witness cosigning, prove data
availability, or anchor roots externally. Future publication adapters may target an
independent evidence registry or external anchor only after separate operational,
privacy, fee, and consensus review.
