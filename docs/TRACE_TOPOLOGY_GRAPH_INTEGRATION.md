# Trace Bitcoin Topology to Graph Integration

## Current pipeline and ownership

The implemented backend flow is:

`OnchainEvent` -> `BitcoinObservationProducer` ->
`BitcoinTopologyRelationshipProducer` -> `BitcoinTopologyEngine` ->
`BitcoinTopologySnapshot` -> `BitcoinTopologyGraphAdapter` ->
`TraceGraphBuilder` -> `TraceSnapshot` -> API/report projections.

The planned Prompt-13 browser topology and future Prompt-14/15 evidence workflows are not
implemented here.

| Concept | Canonical producer | Consumer | Identity mapping | Persistence owner | Projection owner |
| --- | --- | --- | --- | --- | --- |
| Observation | `BitcoinObservationProducer` | relationship producer | observation-version content hash | append-only `OnchainEvent` source fact | none |
| Bitcoin relationship | `BitcoinTopologyRelationshipProducer` | topology engine | relationship-version content hash | reproducible from source facts | none |
| Topology node | `BitcoinTopologyEngine` | topology adapter | network-qualified topology object ID | topology snapshot materialization | topology adapter |
| Topology relationship | `BitcoinTopologyEngine` | topology adapter | unchanged T2 relationship ID | topology snapshot materialization | topology adapter |
| Topology snapshot | `BitcoinTopologyEngine` | topology adapter/history pipeline | topology content hash | reproducible historical source-event prefix | topology adapter |
| Graph object | `TraceGraphBuilder` aggregation | API/report projections | topology ID retained unchanged | Graph snapshot materialization | Graph API projection |
| Graph relationship | `TraceGraphBuilder` aggregation | API/report projections | topology relationship ID retained unchanged | Graph snapshot materialization | Graph API projection |
| Graph snapshot | `TraceGraph` | history/API | graph hash plus builder version | deterministic projection | Graph API projection |
| Trace report projection | Graph report facts | report DTO | report fact identity | legacy report table | report projection service |
| Historical Trace projection | historical topology prefix | history DTO | exact topology snapshot reference | append-only source events | Graph API projection |

`BitcoinTopologyGraphAdapter` is the only topology-to-Graph integration boundary. The Graph
builder accepts its typed output and does not inspect observations to recreate Bitcoin edges.

## Mapping and version policy

Topology address objects map directly to `BITCOIN_ADDRESS`; transaction objects map directly to
`BITCOIN_TRANSACTION`. `ADDRESS_PARTICIPATES_IN_TRANSACTION` is directly compatible and maps to
the identically named Graph relationship. Source, target, direction, relationship identity, and
network-qualified object identity are unchanged. Unsupported topology types fail rather than map
to a generic relationship.

No current topology relationship carries an amount. Observation satoshi values remain integers
and are not copied into relationships, topology, or Graph. If a future authoritative relationship
owns an amount, its typed mapping must retain integer satoshis; float conversion is forbidden.

Topology snapshot identity is independent of Graph snapshot identity. Projection order is
Topology Snapshot first, then Graph. Graph metadata and snapshots explicitly carry the exact
`topology_snapshot_id`, topology/engine versions, and network. The graph hash is the idempotency
key for Graph snapshots; the topology content hash is the idempotency key for topology snapshots.

## Provenance, limitations, privacy, and completeness

Projected Graph relationships retain the T1 observation references, exact T2 relationship ID,
T3 topology snapshot ID, source name/type, adapter producer version, and all limitations. Graph
observations created by the adapter are reference-only records; source payloads, RPC internals,
and provider-private values are not copied to browser DTOs. Evidence references are lineage only,
not verification.

Topology limitations are unioned into Graph limitations. A successful projection does not remove
`no_ownership_inference` or `no_counterparty_inference`. The legacy
`authoritative_topology_producer_missing` limitation is removed only when at least one real
topology relationship is present. Graphs without topology use the explicit transport state
`topology_source_unavailable`; no historical linkage is fabricated.

## Current and historical selection

For a report, current topology is selected from all persisted on-chain events matching the exact
canonical report address, ordered by authoritative observation time and database identity. History
is a deterministic sequence of unique content-addressed topology snapshots over those ordered,
append-only source-event prefixes. Historical Graph A is always projected from Topology A; a later
Topology B cannot mutate A or leak facts into A. No speculative cache or duplicate snapshot table
is introduced.

The canonical durable owner remains `OnchainEvent`. Observations, relationships, topology
snapshots, and Graph snapshots are immutable deterministic materializations, avoiding a second
authoritative store. Existing reports lacking a source event remain readable and truthfully report
`topology_source_unavailable`.

## API, security, and compatibility

The existing read-only Graph metadata, snapshot, history, object, and relationship endpoints now
return topology-backed objects and relationships through strict DTOs. No write endpoint and no
visualization contract is added. The routes retain the repository's existing public Trace report
read posture; they expose public-chain references only and default-deny provider payload details.
Operation IDs and generated-client ownership remain unchanged because no operation was added.

Existing report calculations and DTOs are unchanged. Topology contributes Graph facts but does not
add counterparty, ownership, cluster, mixer, laundering, person, organization, risk, or AML claims.

## Prompt-13 readiness and remaining analytical scope

`FEATURE23_ANALYTICAL_RELATIONSHIP_SOURCE_MISSING` is eliminated for the currently supported real
relationship family: `ADDRESS_PARTICIPATES_IN_TRANSACTION`. The API exposes multiple instances
when multiple authoritative on-chain events exist. Feature-26 historical authority is defined by
immutable, content-addressed topology-prefix projections linked explicitly into Graph snapshots.

Prompt 13 can consume object identity, relationship taxonomy/direction, snapshot correlation, and
history without reconstructing semantics in the browser. More expressive input/output, spend,
UTXO, or block topology remains unavailable until T1/T2 gain those authoritative observations and
relationships; this does not invalidate the supported relationship family.

## Rollback

Rollback T4 by removing the adapter, topology pipeline orchestration, Graph enum/metadata linkage,
API topology loading, T4 tests, generated contract deltas, and this document. Keep T1 observations,
T2 relationships, T3 topology, G1-G4 Graph/report infrastructure, existing report/API tables,
on-chain events, and user data. No destructive data migration or cleanup is required.
