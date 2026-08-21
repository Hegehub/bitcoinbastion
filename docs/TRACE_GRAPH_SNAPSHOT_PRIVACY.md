# Immutable Trace Graph snapshots and browser privacy

## Authority model

A Trace Graph Snapshot is an immutable persisted representation of the canonical
Graph semantic state at one topology/analytical capture boundary. It is not a route
identifier, report alias, current projection, layout, or browser cache.

The implementation uses **GS1**, a canonical JSON serialization that is validated as
the strict `TraceGraphDTO` both before storage and after retrieval. The row retains the
report identity, exact topology snapshot identity, Claim capture identity, Graph and
snapshot schema versions, builder version, SHA-256 content digest, and payload. A
unique `(report, topology snapshot, builder version)` key makes creation idempotent;
the repository exposes insertion and exact reads, not updates. Transaction commit
makes content and history identity visible atomically.

Existing transient history IDs are not reused. When immutable source-event prefixes
remain available, history performs an honest one-time materialization into newly
persisted snapshots. Otherwise no selectable historical row is returned. Missing or
cross-report snapshot reads return not found and never substitute current state.

## Historical disagreement

Each Graph Snapshot stores the immutable Claim capture identity
`trace_report:<report-id>`. D1 Claims retain producer versions and D2 evaluations retain
the evaluator version and stable Claim Set identity. The exact historical disagreement
operation first validates `(report, graph snapshot)` ownership, then derives the typed
D2 result only from the immutable Claims belonging to that report capture. No timestamp
matching or current-Graph reconstruction occurs. D2 remains R1: disagreements are
unresolved and no winner is selected.

## Browser trust boundary

The browser boundary includes HTTP JSON, generated clients, Reflex State, hydration,
visible and hidden DOM, accessibility metadata, and browser-generated downloads.
Threats include credentials, private URLs, internal RPC/host configuration, filesystem
paths, raw provider/debug payloads, operator-only annotations, and unnecessarily rich
provenance. Public Bitcoin addresses, transaction IDs, block hashes, outpoints, and
public-chain amounts are deliberately public-chain data; visual shortening is
presentation truncation, not redaction.

`TracePrivacyPolicy` is the centralized policy owner. Its classifications are public
chain, browser-safe analytical, redactable, internal, and secret. Actions are ALLOW,
DENY, and REDACT; the default for an unknown type or field is DENY. Graph, Claim,
Disagreement, source, and provenance projections all pass explicit mappings through
that policy. REDACT projections may expose safe redaction metadata but never the
original value. Historical internal content is immutable, while browser projection is
performed at read time under the current policy (**PP1**) so a newer security policy
can deny an older stored field.

## Rollback

Snapshot storage, API routes, privacy policy, disagreement projection, generated
transport, and future UI can be disabled independently. Existing snapshot rows must be
retained unless an explicit retention migration removes them. Disabling exact history
must make selection unavailable; it must never fall back to current Graph. Privacy
rollback must retain default-deny behavior and must never restore denied values.
