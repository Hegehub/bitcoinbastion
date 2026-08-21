"""Feature-54 default-deny projections for authoritative Trace Graph contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from bastion_ui.transport.generated_schemas import (
    SafeBitcoinNetworkClaimValueDTO,
    SafeRiskBandClaimValueDTO,
    SafeTraceClaimDTO,
    SafeTraceDisagreementCollectionDTO,
    TraceGraphDTO,
    TraceGraphHistoryDTO,
)


class FrozenViewModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class TraceTopologyNodeViewModel(FrozenViewModel):
    id: str
    kind: str
    label: str
    producer: str
    limitations: tuple[str, ...]


class TraceTopologyRelationshipViewModel(FrozenViewModel):
    id: str
    source_id: str
    target_id: str
    relationship_type: str
    direction: str
    producer: str
    confidence: str
    limitations: tuple[str, ...]


class TraceTopologyMetadataViewModel(FrozenViewModel):
    graph_id: str
    snapshot_id: str
    topology_snapshot_id: str
    captured_at: str
    graph_version: str
    source_status: str
    limitations: tuple[str, ...]


class TraceTopologyViewModel(FrozenViewModel):
    metadata: TraceTopologyMetadataViewModel
    nodes: tuple[TraceTopologyNodeViewModel, ...]
    relationships: tuple[TraceTopologyRelationshipViewModel, ...]


class TraceHistoryIndexItemViewModel(FrozenViewModel):
    snapshot_id: str
    topology_snapshot_id: str
    captured_at: str
    graph_version: str
    builder_version: str
    limitations: tuple[str, ...]


class TraceClaimViewModel(FrozenViewModel):
    id: str
    subject_id: str
    subject_label: str
    predicate: str
    value_kind: str
    value_label: str
    producer: str
    source: str
    producer_version: str
    confidence: str
    limitations: tuple[str, ...]


class TraceDisagreementViewModel(FrozenViewModel):
    evaluation_id: str
    graph_snapshot_id: str
    status: str
    resolution_status: str
    subject_id: str
    predicate: str
    claims: tuple[TraceClaimViewModel, ...]
    eligible_claim_count: int
    unavailable_producer_count: int
    limitations: tuple[str, ...]


class TraceDisagreementCollectionViewModel(FrozenViewModel):
    graph_snapshot_id: str
    evaluations: tuple[TraceDisagreementViewModel, ...]


def _enum_value(value: object) -> str:
    root = getattr(value, "root", value)
    return str(root)


def _time(value: datetime) -> str:
    return value.isoformat()


def adapt_trace_graph(graph: TraceGraphDTO) -> TraceTopologyViewModel:
    """Project backend nodes/edges without topology inference or reconstruction."""
    return TraceTopologyViewModel(
        metadata=TraceTopologyMetadataViewModel(
            graph_id=graph.metadata.graph_id,
            snapshot_id=graph.snapshot.snapshot_id,
            topology_snapshot_id=graph.snapshot.topology_snapshot_id or "Unavailable",
            captured_at=_time(graph.metadata.created_at),
            graph_version=graph.metadata.graph_version,
            source_status=_enum_value(graph.metadata.topology_source_status),
            limitations=tuple(graph.metadata.limitations or ()),
        ),
        nodes=tuple(
            TraceTopologyNodeViewModel(
                id=item.id,
                kind=item.kind,
                label=item.label,
                producer=item.provenance.producer,
                limitations=tuple(item.limitations or ()),
            )
            for item in graph.objects
        ),
        relationships=tuple(
            TraceTopologyRelationshipViewModel(
                id=item.id,
                source_id=item.source_id,
                target_id=item.target_id,
                relationship_type=item.relationship_type,
                direction=item.direction,
                producer=item.provenance.producer,
                confidence=_confidence(item.confidence),
                limitations=tuple(item.limitations or ()),
            )
            for item in graph.relationships
        ),
    )


def adapt_trace_history(
    history: TraceGraphHistoryDTO,
) -> tuple[TraceHistoryIndexItemViewModel, ...]:
    return tuple(
        TraceHistoryIndexItemViewModel(
            snapshot_id=item.snapshot_id,
            topology_snapshot_id=item.topology_snapshot_id or "Unavailable",
            captured_at=_time(item.created_at),
            graph_version=item.graph_version,
            builder_version=item.builder_version,
            limitations=tuple(item.limitations or ()),
        )
        for item in history.entries
    )


def adapt_trace_disagreements(
    collection: SafeTraceDisagreementCollectionDTO,
) -> TraceDisagreementCollectionViewModel:
    return TraceDisagreementCollectionViewModel(
        graph_snapshot_id=collection.graph_snapshot_id,
        evaluations=tuple(
            TraceDisagreementViewModel(
                evaluation_id=item.evaluation_id,
                graph_snapshot_id=item.graph_snapshot_id,
                status=item.status,
                resolution_status=item.resolution_status,
                subject_id=item.subject.object_id if item.subject else "Unavailable",
                predicate=item.predicate or "Unavailable",
                claims=tuple(_claim(claim) for claim in item.claims),
                eligible_claim_count=item.coverage.eligible_claim_count,
                unavailable_producer_count=item.coverage.unavailable_producer_count,
                limitations=tuple(item.limitations),
            )
            for item in collection.evaluations
        ),
    )


def _claim(claim: SafeTraceClaimDTO) -> TraceClaimViewModel:
    if isinstance(claim.value, SafeRiskBandClaimValueDTO):
        value_kind, value_label = "risk_band", claim.value.band
    elif isinstance(claim.value, SafeBitcoinNetworkClaimValueDTO):
        value_kind, value_label = "bitcoin_network", claim.value.network
    else:  # pragma: no cover - generated strict union rejects this before Feature-54
        raise ValueError("unsupported_trace_claim_value")
    return TraceClaimViewModel(
        id=claim.id,
        subject_id=claim.subject.object_id,
        subject_label=claim.subject.public_value,
        predicate=claim.predicate,
        value_kind=value_kind,
        value_label=value_label,
        producer=claim.producer,
        source=claim.source,
        producer_version=claim.producer_version,
        confidence=_confidence(claim.confidence),
        limitations=tuple(claim.limitations),
    )


def _confidence(value: Decimal | None) -> str:
    return "Not provided" if value is None else str(value)
