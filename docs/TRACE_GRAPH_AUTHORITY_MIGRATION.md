# Trace Graph Authority Migration and Prompt-13 Readiness

## Updated architecture

The canonical analytical flow is now observations -> `TraceGraphBuilder` -> authoritative `TraceGraph` -> projection layer -> DTO/transport/frontend. Existing persistence remains report-compatible, but report-facing analytical values are now carried by graph-owned `TraceReportProjectionFacts` and projected through `TraceReportGraphProjectionService`.

## Projection architecture

`TraceReportProjectionFacts` is the graph-owned analytical record for legacy `TraceReport` fields. `TraceReportGraphProjectionService` is the report projection layer and never mutates graph state. `TraceGraphApiProjectionService` is the API projection layer and converts the same graph/provenance model into strict transport DTOs.

## Ownership audit

| Report field group | Graph owner | Projection owner | Transport owner | Frontend owner |
| --- | --- | --- | --- | --- |
| address/chain | `TraceReportProjectionFacts` | `TraceReportGraphProjectionService` | existing `TraceReport` DTO and Graph DTOs | consumer display only |
| trace score/band/confidence | `TraceReportProjectionFacts` | `TraceReportGraphProjectionService` | existing `TraceReport` DTO and Graph DTOs | consumer display only |
| source quality/freshness | `TraceReportProjectionFacts` | `TraceReportGraphProjectionService` | existing `TraceReport` DTO and Graph DTOs | consumer display only |
| reason/evidence/limitations/guidance | `TraceReportProjectionFacts` and graph provenance | `TraceReportGraphProjectionService` | existing `TraceReport` DTO and Graph DTOs | consumer display only |
| graph object/relationship identities | `TraceGraph` | `TraceGraphApiProjectionService` | generated Graph transport | consumer display only |

Legacy report persistence remains a compatibility storage projection. It is transitional and must not be treated as an independent analytical owner.

## Migrated report pipeline

`TraceService.analyze_address` still runs the existing baseline analytical producers, then creates a graph from those observations and returns the report through `TraceReportGraphProjectionService.project_compatible_report`. This keeps API compatibility while making report-facing analytical values graph-projected.

## Legacy paths

Legacy JSON columns on `TraceReport` remain for compatibility with existing APIs and stored data. They are transitional persistence projections. Existing metadata endpoints that return raw dictionaries remain legacy compatibility paths until their fields are migrated into graph-owned projection facts or graph DTOs.

## Provenance validation

Every report projection fact includes graph provenance, including builder stage, originating observation, and limitations. Snapshots include report fact identities so a consumer can link projected report values to the immutable graph snapshot.

## Feature-53 and Feature-54 validation

Feature-53 ownership remains registered for the Graph API operations in the frontend migration matrix and ownership input. Feature-54 provenance is preserved by projecting from the Graph Domain `TraceProvenance` model instead of creating a second provenance model.

## Prompt-13 readiness audit

T1-T4 now provide an authoritative non-report
`ADDRESS_PARTICIPATES_IN_TRANSACTION` relationship from persisted Bitcoin source facts. The
Topology Engine owns semantics and `BitcoinTopologyGraphAdapter` preserves those semantics in
Graph. The original relationship-source blocker is eliminated for this supported family. See
`TRACE_TOPOLOGY_GRAPH_INTEGRATION.md` for identity, snapshot, history, privacy, and rollback policy.

## Rollback

Rollback can remove `TraceReportProjectionFacts`, the report projection migration changes, snapshot report fact IDs, this document, and the added tests. Keep G1-G3 Graph Domain, builder, snapshots, history, typed transport, reports, APIs, persistence, and user data intact.
