# Trace Graph Builder Pipeline

## Updated builder architecture

`TraceGraphBuilder` is the canonical backend producer of `TraceGraph`. Callers add authoritative analytical observations through builder methods, then `build()` executes deterministic stages and returns an immutable finalized graph. Direct graph construction outside this builder is reserved for tests of domain primitives only.

## Pipeline stages

1. Observation collection gathers existing Trace report analytical output without parsing new chain data.
2. Observation normalization trims and validates subjects, canonicalizes limitations, and prepares stable observation and object identifiers.
3. Identity resolution keeps equivalent normalized observations mapped to the same deterministic IDs.
4. Object creation emits only authoritative backend analytical objects.
5. Relationship construction emits only evidence-backed relationships.
6. Evidence linking preserves observation references without duplicating evidence.
7. Graph validation rejects incomplete provenance, orphan relationships, unsupported directions, unsupported relationship types, and missing observations.
8. Graph finalization freezes deterministic mappings and computes a deterministic graph hash.
9. Report projection validates that the existing report has a graph projection object and then returns the unchanged compatible report.

## Relationship construction strategy

The current engine authoritatively supports a directed `ANALYZED_AS` relationship from a normalized Bitcoin address object to the trace report projection object because that relationship is produced by the existing `TraceService.analyze_address` analytical stage and supported by the scoring observation. The builder still records `authoritative_topology_producer_missing` because the current engine does not yet produce transaction, flow, clustering, counterparty, or address-to-address topology relationships.

## Identity and determinism strategy

Object, observation, relationship, and bundle identities use `stable_trace_id`, a SHA-256 based deterministic identifier over explicit analytical parts. Builder dictionaries merge duplicates by stable ID, and finalization sorts all mappings before freezing them. Identical analytical inputs therefore produce identical graph ordering and graph hashes.

## Provenance strategy

Every observation, object, and relationship carries `TraceProvenance` with producer, stage, supporting observations, evidence references, and limitations. Relationship provenance points to the originating scoring observation.

## Validation strategy

Graph validation is explicit and raises `TraceGraphBuildError` with typed validation failures. The builder does not silently return partial graphs that pretend to be complete.

## Report migration points

`TraceReportGraphProjectionService` is the compatibility migration point. It builds a graph from the existing report schema and verifies that a report projection object exists before returning the unchanged report. Later prompts can move report fields to graph-backed projections incrementally without changing public APIs first.

## Remaining blockers before Graph API

Before a public Graph API exists, Trace still needs an authoritative topology producer for Bitcoin transaction/address/counterparty relationships, graph persistence or snapshot persistence decisions, authorization semantics for graph access, and public DTO review.
