# Trace Proof Packet and Evidence authority

## Feature ownership

| Feature ID | Canonical name | Requirement | Existing authority | Prompt 14 ownership | Evidence |
|---|---|---|---|---|---|
| 43 | Contextual evidence details drawer | Show safe details for one selected Evidence item in context | Trace Graph provenance, D1 Claims, D2 evaluations, immutable Graph Snapshots | Typed packet Evidence list and contextual detail surface | Backend/API tests, Feature-54 tests, browser request-to-DOM checks |
| 52 | Provenance State Model | Preserve exactly four provenance states | Existing Feature-52 domain | Reuse only; packet verification is not provenance | Provenance scenario assertions |
| 53 | HTTP Ownership | One generated owner per packet read | Stage-1 transport generator | Current and historical packet GET ownership | Stage-1 and semantic-handoff validators |
| 54 | Domain Adapters | End generated DTOs at a strict adapter boundary | Existing Feature-54 pattern | Packet/Evidence ViewModels | Frontend adapter tests |
| 59/60 | Degraded states/fixtures | Deterministic non-production scenarios | Existing scenario framework | Typed packet/evidence scenarios, always `DEMO_FIXTURE` | Scenario tests |
| 67 | Security metadata | Match operation-level access posture | Proof-of-Access dependency and OpenAPI security | Protected packet route/transport classification | OpenAPI and route tests |

Prompt 15 retains recursive Evidence-chain traversal, replay, verification workflow, and
export/copy architecture.

## Authority inventory

| Concept | Producer | Persistence | Identity | Integrity | Verification | API/browser safety |
|---|---|---|---|---|---|---|
| Bitcoin observation reference | T1 observation producer | immutable on-chain event/topology capture | observation reference | not checked by packet | not verified | projected metadata only |
| Topology relationship support | T2/T3 then T4 provenance | persisted immutable Graph Snapshot | stable Evidence ID plus relationship ID | not checked by packet | not verified | centralized Trace Privacy Policy |
| Claim input reference | D1 Claim producer | append-only Claim capture | stable Evidence ID plus Claim ID | not checked by packet | not verified | centralized Trace Privacy Policy |
| Packet membership | Proof Packet assembler | PP1: derived from immutable snapshot/capture | backend content-derived packet ID | packet digest checked | not verified | strict safe DTO |

Evidence record identity and a content digest are distinct. This implementation does not claim
that referenced content bytes were independently retrieved or verified. `CONTENT_INTEGRITY_CHECKED`
means only that canonical packet membership produced the displayed packet digest. `NOT_VERIFIED`
is preserved independently. Linked Evidence never implies verification.

## Canonical semantics

A Trace Proof Packet is a typed, backend-assembled inspection package bound to a Trace report,
an exact persisted Graph Snapshot, the report Claim capture, D2 evaluations, selected Evidence
references, provenance, and limitations. It is advisory analytical context. It is not legal proof,
cryptographic proof of attribution, independent external verification, or Bitcoin consensus proof.

The implementation uses **PP1 (derived read-only packet)**. Packet IDs are backend-owned and
content-derived from schema/assembler versions and sorted immutable membership identities. There
is no packet mutation and therefore no mutation idempotency key. Repeated reads of unchanged
source state are deterministic. Current reads bind the latest persisted current capture;
historical reads require an exact Graph Snapshot ID and never fall back to current state.

## Selection and versioning

The backend assembler selects only explicit links:

1. Graph relationship provenance Evidence linked to that exact relationship ID.
2. D1 Claim input references linked to that exact Claim ID.

It does not scan every Evidence record, infer relevance from layout, rerun topology, resolve D2
disagreement, or select a winning Claim. Packet schema and assembler versions are independent of
Graph Snapshot, producer, evaluator, Evidence, privacy-policy, and API versions.

## Privacy boundary

The existing centralized Trace Privacy Policy owns browser crossing. Packet and Evidence fields
are explicit allowlists and unknown fields default to `DENY`. The safe contract exposes IDs,
kind, safe reference, producer/source category, timestamps, explicit linkage, integrity and
verification posture, and limitations. It excludes raw content, provider configuration,
credentials, internal URLs and paths, debug payloads, and unclassified provenance. The synthetic
`TRACE_EVIDENCE_PRIVACY_CANARY_NEVER_BROWSER` is asserted absent from safe HTTP serialization.

## Request-to-render lineage

`Trace/capture → TraceProofPacketAssembler → TraceProofPacket → TracePrivacyPolicy →
SafeTraceProofPacketDTO → generated client → adapt_trace_proof_packet →
TraceProofPacketState → Proof Packet/Evidence DOM`.

Claims and D2 evaluations retain their backend identities and status. Evidence linkage retains
the backend Claim/relationship IDs. The frontend performs no packet assembly, Evidence creation,
verification upgrade, disagreement calculation, or historical reconstruction.

## Rollback

The domain/assembler, safe projection, two read routes, generated transport, Feature-54 adapter,
State, route, UI, scenarios, tests, and this document can be disabled independently. Rollback must
leave Prompt-13 Graph snapshots/topology/history/privacy and D1/D2 data intact. Existing packet
routes should become unavailable rather than returning raw data or assembling packets in the
browser. Linked Evidence must continue to be labelled not verified.

## Prompt-14 browser-remediation gates

The reproducible acceptance target is `python scripts/verify_prompt14_browser.py`. It creates two
canonical persisted Graph boundaries through Trace analysis, on-chain Observation production, and
Graph snapshot capture. It never seeds a final packet DTO. The test proves the matrix below.

| Gate | Browser action | Prior evidence | Remediation evidence | Code fix required? |
|---|---|---|---|---|
| P14-A86 | Open exact historical A | One historical packet only | Exact A route, packet, Evidence and snapshot IDs | Harness added |
| P14-A87 | Navigate A→B | Missing | Exact B request and canonical B-only Evidence | Harness added |
| P14-A88/A89 | Browser Back B→A | Missing | A restored; B-only Evidence absent | Harness added |
| P14-A90 | Hard refresh A | Missing | Exact A route/request/DOM; no current substitution | Harness added |
| P14-A91 | Inspect HTTP and DOM | Manual only | Canary absent from safe HTTP, DOM and accessibility scan | Harness added |
| P14-A92/A93 | Keyboard and mobile | Manual pass | Keyboard detail flow and 390×844 scan | Automated |
| P14-A94 | Toggle both themes | Missing request ledger | Packet request count unchanged for current and historical | Automated |
| P14-A95 | Scan production DOM | No scanner | axe-core current, historical, detail and mobile scans | Contrast fixes |
| P14-A96/A97 | Repeated route/detail actions | Partial | Exact request ledger with zero unexplained duplicates/storms | Automated |

The harness also delays no analytical operation and relies on the existing generation-token and
snapshot-ID latest-wins guard. Unit coverage asserts that stale response protection remains in the
State.

Rollback of this remediation may remove the harness, test-only axe dependency, and contrast/focus
repairs independently. It must not remove or reinterpret persisted
snapshots, packet/Evidence authority, privacy policy, D1/D2, topology, generated transport, or user
data. A rollback must leave exact historical reads unavailable rather than substituting current.
