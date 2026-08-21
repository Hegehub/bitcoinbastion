# Trace Graph Domain Foundation

## Current architecture inventory

Trace currently normalizes a Bitcoin address, executes baseline scoring, saves `TraceReport`, and projects public/API report views from that report. The authoritative persistence objects are `TraceReport`, `TraceEvidence`, `TraceSource`, source snapshots, watchlist entries, batch items, policy profiles, review items, operator notes, proof packets, exports, and business events. Current analytical inputs are the submitted public Bitcoin address, source registry rows, baseline reason codes, provider-disagreement placeholders, evidence-independence calculations, origin passport output, privacy shield output, counterparty lens output, and payment-context request data when present.

Intermediate analytical objects include scoring input/result, score breakdown, trace DNA, factor contributions, confidence ledger entries, origin passport, source summaries, provider disagreement, evidence independence, privacy shield, UTXO hygiene placeholders, dust radar placeholders, and counterparty lens. Outputs are report schemas, lite reports, public summaries, evidence lists, proof packets, policy facts, batch results, business events, and integration advisories. Persistence is currently report-centric JSON columns plus related relational rows.

The main type-erasure points are JSON columns on `TraceReport`, dictionary-returning service methods for metadata projections, and SDK `unknown` payloads. Analytical information becomes report-only when `TraceService.analyze_address` serializes limitations, reason codes, evidence refs, origin metadata, disagreement metadata, privacy metadata, and counterparty lens data onto the saved report instead of placing them in an independent analytical container.

## Architectural limitations

Trace does not yet have an authoritative blockchain-topology producer. The current engine can authoritatively relate the normalized Bitcoin address analytical object to the report projection generated from it, but it cannot authoritatively create address-to-address, address-to-transaction, flow, clustering, counterparty, or temporal topology relationships. The graph builder therefore records `authoritative_topology_producer_missing` as a graph limitation rather than fabricating unsupported edges.

## New domain model

The internal graph domain separates raw observations, derived facts, analytical objects, relationships, graph containers, snapshots, provenance, and report projections. Analytical objects are backend subjects, not UI nodes. Relationships are directed, stable, typed, provenance-preserving facts that must cite their originating observation. Graph snapshots are immutable backend analytical state and intentionally exclude browser layout or visualization state.

## Responsibility diagram

```text
TraceService / current producers
  -> TraceGraphBuilder.add_report_projection(...)
     -> observations: raw subject + derived scoring fact
     -> analytical objects: bitcoin address + trace report projection object
     -> relationships: only current authoritative ANALYZED_AS projection relationship
     -> provenance + limitations
  -> TraceGraph
     -> TraceSnapshot
  -> future report projection migration
```

## Persistence strategy

The foundation is internal and in-memory for now. It avoids a duplicate source of truth by continuing to persist existing reports and metadata unchanged. A future persistence prompt can store graph snapshots once the repository has authoritative topology producers beyond report projection relationships.

## Extension-point and migration strategy

`TraceGraphBuilder` is the extension point for current and future analytical producers. Current report generation remains backward-compatible. Future work can add producer-specific builder methods and gradually move report generation to read from `TraceGraph` without changing existing public APIs first.

## Versioning model

`graph_version` identifies graph-domain semantics only. It is independent from API version, report version, capture version, and database schema version. `analysis_version` records the analytical engine version that produced a graph instance.

## Rollback plan

Rollback can remove `app/services/bastion_trace/graph/`, `tests/services/bastion_trace/test_trace_graph_builder.py`, and this document. Because no database schema, public API, report model, or existing persistence behavior changed, rollback preserves existing reports, APIs, persistence, and user data.
