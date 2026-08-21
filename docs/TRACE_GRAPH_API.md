# Trace Graph API, Snapshots, and History

## Updated architecture

Trace Graph is now an authoritative backend resource. The lifecycle is: Trace report persistence -> `TraceGraphBuilder` -> immutable graph -> typed API projection -> immutable snapshot -> backend-owned history -> generated typed transport. Frontend code must consume these contracts and must not reconstruct graph semantics.

## API surface

All endpoints are read-only and nested under the existing Trace report resource:

- `GET /api/v1/trace/report/{report_id}/graph/metadata`
- `GET /api/v1/trace/report/{report_id}/graph/snapshot`
- `GET /api/v1/trace/report/{report_id}/graph/history`
- `GET /api/v1/trace/report/{report_id}/graph/objects/{object_id}`
- `GET /api/v1/trace/report/{report_id}/graph/relationships/{relationship_id}`

The API intentionally excludes visualization, browser state, layout, replay UI, and topology renderer concerns.

## DTO hierarchy

`TraceGraphDTO` owns metadata, objects, relationships, observations, and snapshot. `TraceGraphSnapshotDTO` is frozen and identifies immutable analytical state. `TraceGraphHistoryDTO` records backend-owned history entries. `TraceGraphError` is the typed Graph error schema for Graph-specific failures.

## Version semantics

- Graph Version: graph-domain semantics (`trace-graph-v1`).
- Snapshot Version: immutable snapshot contract (`trace-snapshot-v1`).
- Analysis Version: analytical engine version that produced the graph.
- API Version: public Graph API contract (`trace-graph-api-v1`).
- Schema Version: DTO schema contract (`trace-graph-schema-v1`).
- Builder Version: builder execution semantics (`trace-graph-builder-v1`).

These values are separate and must not be overloaded.

## History semantics

History is backend-owned and derived from persisted Trace analytical state. Each entry records snapshot id, graph id, graph version, creation time, builder version, analysis version, provenance summary, and limitations. History never depends on frontend state.

## Ownership and generated transport

The five Graph operations are registered in the frontend migration ownership matrix and `01_HTTP_CLIENT_OWNERSHIP_INPUT.json`, then generated into `frontend/bastion_ui/transport/generated_http.py` and `generated_schemas.py`. This preserves Feature-53 ownership and avoids handwritten transport methods.

## Feature-54 provenance

The API uses the same `TraceProvenance` model created by the Graph Domain and projected into strict DTOs. It does not introduce a duplicate provenance system.

## Security review

The endpoints are read-only GET operations over existing public-address Trace report identifiers. They do not mutate state, do not accept seed/private-key material, do not require Human Intent, and do not expose browser state. Access rules match the current public-address Trace workflow; future private/business graph surfaces must add PoP/scope gates before exposure.

## Remaining blockers before report migration

Reports can be validated through graph projection, but full report migration still requires authoritative topology producers, graph snapshot persistence decisions, and a complete report-from-graph projection service for all report fields.

## Rollback

Rollback can remove the Graph API routes, `app/schemas/trace_graph.py`, `api_projection.py`, generated transport entries, ownership rows, this document, and Graph API tests. Existing Graph Domain, builder, reports, APIs, and persistence remain valid.
