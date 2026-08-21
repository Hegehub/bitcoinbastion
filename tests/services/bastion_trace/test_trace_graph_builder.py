import pytest

from app.schemas.bastion_trace import TraceBand, TraceFreshness, TraceReport, TraceSourceQuality
from app.services.bastion_trace.graph.builder import (
    GRAPH_RELATIONSHIP_PRODUCER_MISSING,
    TraceGraphBuildError,
    TraceGraphBuilder,
)
from app.services.bastion_trace.graph.report_projection import TraceReportGraphProjectionService
from app.services.bastion_trace.graph.domain import (
    GRAPH_VERSION,
    TraceAnalyticalObjectKind,
    TraceRelationshipDirection,
    TraceRelationshipType,
)


def report(
    address: str = "bc1qexamplepublicaddress000000000000000000000", report_id: int = 7
) -> TraceReport:
    return TraceReport(
        id=report_id,
        address=address,
        trace_score=0.0,
        trace_band=TraceBand.LOW,
        confidence=0.42,
        source_quality=TraceSourceQuality.UNKNOWN,
        freshness=TraceFreshness.UNKNOWN,
        limitations=["advisory_only", "not_consensus_proof"],
    )


def build_graph(*reports: TraceReport):
    builder = TraceGraphBuilder()
    for item in reports:
        builder.add_report_projection(item)
    return builder.build()


def test_stable_object_identity() -> None:
    first = build_graph(report())
    second = build_graph(report())
    assert sorted(first.objects) == sorted(second.objects)


def test_stable_relationship_identity_and_direction() -> None:
    graph = build_graph(report())
    relationships = list(graph.relationships.values())
    assert len(relationships) == 1
    relationship = relationships[0]
    assert relationship.relationship_type is TraceRelationshipType.ANALYZED_AS
    assert relationship.direction is TraceRelationshipDirection.DIRECTED
    assert relationship.source_id != relationship.target_id
    assert relationship.id in graph.relationships


def test_duplicate_merging_is_by_stable_identity() -> None:
    duplicate = report()
    graph = build_graph(duplicate, duplicate)
    assert len(graph.objects) == 2
    assert len(graph.relationships) == 1
    assert len(graph.observations) == 2


def test_builder_determinism() -> None:
    a = report("bc1qexamplepublicaddress000000000000000000000", 7)
    b = report("bc1qotherpublicaddress0000000000000000000000", 8)
    graph_one = build_graph(a, b)
    graph_two = build_graph(b, a)
    assert tuple(graph_one.objects) == tuple(graph_two.objects)
    assert tuple(graph_one.relationships) == tuple(graph_two.relationships)
    assert tuple(graph_one.observations) == tuple(graph_two.observations)


def test_provenance_preserved_for_objects_and_relationships() -> None:
    graph = build_graph(report())
    address_objects = [
        o for o in graph.objects.values() if o.kind is TraceAnalyticalObjectKind.BITCOIN_ADDRESS
    ]
    assert address_objects[0].provenance.producer == "TraceService.analyze_address"
    assert address_objects[0].provenance.observations
    relationship = next(iter(graph.relationships.values()))
    assert relationship.provenance.stage == "relationship_construction"
    assert relationship.originating_observation_id in graph.observations
    assert relationship.confidence == 0.42


def test_graph_version_semantics_are_independent_from_analysis_version() -> None:
    graph = TraceGraphBuilder(analysis_version="custom-analysis-v2").build()
    assert graph.metadata.graph_version == GRAPH_VERSION
    assert graph.metadata.analysis_version == "custom-analysis-v2"


def test_snapshot_is_immutable_and_backend_state_only() -> None:
    graph = build_graph(report())
    snapshot = graph.snapshot()
    assert snapshot.graph_version == GRAPH_VERSION
    assert not hasattr(snapshot, "layout")
    with pytest.raises(Exception):
        snapshot.object_ids += ("mutate",)  # type: ignore[misc]


def test_current_graph_records_missing_authoritative_topology_producer() -> None:
    graph = build_graph(report())
    assert GRAPH_RELATIONSHIP_PRODUCER_MISSING in graph.limitations


def test_invalid_observation_rejection() -> None:
    builder = TraceGraphBuilder()
    builder.add_report_projection(report(address="   "))
    with pytest.raises(TraceGraphBuildError):
        builder.build()


def test_builder_idempotency_and_graph_hash() -> None:
    builder = TraceGraphBuilder()
    item = report()
    builder.add_report_projection(item)
    first = builder.build()
    second = builder.build()
    assert first.metadata.graph_hash == second.metadata.graph_hash
    assert first.snapshot() == second.snapshot()


def test_graph_mappings_are_immutable() -> None:
    graph = build_graph(report())
    with pytest.raises(TypeError):
        graph.objects["new"] = next(iter(graph.objects.values()))  # type: ignore[index]


def test_report_projection_preserves_report_compatibility() -> None:
    item = report()
    projector = TraceReportGraphProjectionService()
    graph = projector.build_graph_for_report(item)
    assert projector.project_compatible_report(item, graph) == item


def test_report_projection_is_graph_authoritative() -> None:
    item = report()
    graph = TraceGraphBuilder().build()
    projector = TraceReportGraphProjectionService()
    with pytest.raises(ValueError):
        projector.project_report(graph)

    graph = projector.build_graph_for_report(item)
    projected = projector.project_report(graph)
    assert projected.trace_score == item.trace_score
    assert projected.trace_band == item.trace_band
    assert projected.confidence == item.confidence
    assert next(iter(graph.report_facts.values())).provenance.observations


def test_graph_snapshot_includes_report_fact_identity() -> None:
    graph = build_graph(report())
    assert graph.snapshot().report_fact_ids == tuple(sorted(graph.report_facts))
