# Trace Evidence lineage, replay, verification, copy, and export

## Canonical Prompt-15 ownership

| Feature | Canonical repository name | Existing authority | Prompt-15 responsibility | Explicit non-goal | Required proof |
|---|---|---|---|---|---|
| 27 | Progressive evidence-chain reveal | Prompt-14 stable Evidence and packet membership | Bounded typed lineage/chain rooted at one Evidence ID | Bitcoin transaction-path explorer | API, VM, structured DOM, browser |
| 28 | Confidence provenance waterfall | D1 producer identity and typed provenance | Display producer/version and deterministic identity replay without recomputing confidence | Re-score or infer confidence frontend-side | replay MATCH/mismatch tests and DOM |
| 29 | Snapshot versus recompute diff | Immutable Graph Snapshot and packet capture | Compare original and replayed Evidence identity under pinned method v1 | Recompute historical analytics with current producers | historical A/B and replay input proof |
| 44 | One-click copy for IDs, hashes and citations | Browser-safe Trace privacy projection | Copy full safe Evidence IDs and export digests with accessible feedback | Copy redacted originals/raw content | clipboard/browser privacy proof |
| 62 | Source-provenance breadcrumbs and lineage trail | Observation, relationship, Claim, snapshot and packet identities | Typed directed lineage nodes, edges and paths | Generic `RELATED_TO` inference | backend/DOM identity parity |

Features 52/53/54/59/60/67 remain shared foundations. Prompt 16 Access work and generic
blockchain exploration remain out of scope.

## Existing authority and verifier inventory

| Capability | Existing source | Prompt-15 use | Semantics |
|---|---|---|---|
| Evidence identity | Prompt-14 stable SHA-256-derived Evidence ID | replay and identity-integrity verifier | Identity derived from kind + safe reference + one canonical owner |
| Graph/Claim links | Immutable packet membership | lineage nodes/edges | Explicit support/provenance link, not causality |
| Graph Snapshot | Persisted exact snapshot | historical boundary | Exact captured Graph, no current fallback |
| Packet digest | Prompt-14 packet assembler | packet context only | Packet membership integrity, not Evidence verification |
| Object storage | Generic `StorageArtifact` infrastructure | not used | No Evidence content blob is required by this workflow |
| Content/signature/inclusion verifier | none for Trace Evidence | reported as unsupported/not claimed | No source authenticity, signature, or Bitcoin inclusion claim |

The only implemented verifier is `trace-evidence-identity-integrity-v1`. Its proposition is:
the stored Evidence identity matches the pinned Evidence kind, safe source reference, and exact
Claim/relationship owner identity. A successful result is **Evidence identity integrity verified**.
It does not verify source authenticity, blockchain inclusion, ownership, attribution, Claim truth,
or causality. `captured_at`, `replayed_at`, and `verified_at` are separate timestamps. Multiple
verification scopes are not currently available, so multi-scope display is not applicable rather
than flattened.

## Lineage and Evidence Chain

Evidence lineage is a backend-owned bounded directed graph of explicit upstream source references
and downstream analytical references. Node kinds are `SOURCE_REFERENCE`, `EVIDENCE`,
`TOPOLOGY_RELATIONSHIP`, `CLAIM`, `GRAPH_SNAPSHOT`, `REPORT_CAPTURE`, and `PROOF_PACKET`.
Relations are only `PRODUCED_FROM`, `SUPPORTS`, `CAPTURED_IN`, `INCLUDED_IN`, and
`REFERENCED_BY`; there is no generic relation fallback. Direction and stable IDs are emitted by the
backend. Completeness is explicitly `COMPLETE`, `PARTIAL`, `TRUNCATED`, or `UNAVAILABLE`.

An Evidence Chain is one ordered path through that lineage graph. Branches are represented as
multiple typed paths and are never flattened into a deceptive single list. The chain is provenance
and support lineage—not Bitcoin topology—and hashes do not make the whole chain verified.
Historical lineage is assembled only from the exact packet/Graph Snapshot supplied by the caller;
later Evidence or relationships cannot enter historical A.

## Replay and verification

Replay reproduces the stable Evidence identity from immutable packet inputs using
`trace-evidence-identity-v1`. Eligibility is typed as replayable, not replayable, input unavailable,
version unavailable, or unsupported legacy. Results distinguish MATCH, MISMATCH, NOT_REPLAYABLE,
INPUT_UNAVAILABLE, VERSION_UNAVAILABLE, and EXECUTION_FAILED.

MATCH means only that the reproduced stable identity equals the captured Evidence ID. MISMATCH
means identity derivation differed; it does not establish malicious tampering or falsify a Claim.
Replay is read-only and deterministic for the same immutable inputs. Historical replay includes the
exact Graph Snapshot ID in its input boundary and never substitutes current data or a current
producer version. Replay MATCH and scoped verification remain separate backend results.

## Copy and export

Copy is limited to browser-safe full Evidence IDs. Visual wrapping/truncation does not change the
copied value. Privacy-redacted originals never enter the DTO or State, so no copy path can recover
them. Copy success is announced through a polite status region without echoing secret material.

Export uses **E1: backend-generated export** and supports one format:
`application/json`, schema `trace-evidence-export-v1`. It contains the safe Evidence projection,
lineage, replay result, scoped verification result, exact Graph Snapshot/packet identities,
provenance, and limitations. The SHA-256 export digest protects the returned bytes only; the export
is unsigned and not independently verified. The deterministic safe filename contains only a
sanitized Evidence identity. There are no internal/signed URLs. CSV is unsupported, so spreadsheet
formula-injection handling is not applicable. Historical exports bind the exact snapshot and packet.

All API surfaces are protected read-only GET operations. Replay and verification are deterministic
computations without persistence or side effects, so there is no mutation idempotency or Human
Intent ceremony. The generated client carries canonical Proof-of-Access metadata.

## Privacy and frontend boundary

Lineage, replay, verification, and export use the centralized `TracePrivacyPolicy`; unknown fields
remain denied. The browser receives strict DTOs only. Feature-54 adapters copy backend semantics,
and Reflex State stores typed ViewModels. Export content is used transiently by `rx.download`; State
stores only export metadata/status. The frontend does not infer lineage/order, calculate replay,
aggregate verification, create canonical exports, or retain binary/raw Evidence.

Feature 52 remains exactly `LIVE`, `VERIFIED_SNAPSHOT`, `DEMO_FIXTURE`, and `UNAVAILABLE`.
Replay and verification statuses are not provenance states. Feature-59 covers every typed degraded
lineage/replay/verification/export posture; Feature-60 fixtures remain deterministic
`DEMO_FIXTURE` values and never replace live proof.

## Rollback

Lineage schemas/service/routes, replay, verifier, export, generated transport, Feature-54 adapters,
State, UI, scenarios, browser tests, and this document can be disabled independently. Rollback must
preserve Prompt-14 Evidence/packets, Prompt-13, D1/D2, immutable Graph Snapshots, privacy policy,
T1–T4, G1–G4, Trace Submit/Report, existing Evidence rows, and user data. Removed capabilities must
become unavailable; rollback must never infer lineage frontend-side, expose denied values, relabel
integrity as generic verification, or replay historical Evidence from current state.
