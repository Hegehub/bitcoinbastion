"""Feature-54 projections for backend-owned Evidence lineage workflows."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from bastion_ui.transport.generated_schemas import (
    SafeEvidenceExportDTO,
    SafeEvidenceLineageDTO,
    SafeEvidenceReplayDTO,
    SafeEvidenceVerificationDTO,
)


class FrozenEvidenceWorkflowViewModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class EvidenceLineageNodeViewModel(FrozenEvidenceWorkflowViewModel):
    id: str
    kind: str
    label: str
    producer: str
    producer_version: str
    captured_at: str
    limitations: tuple[str, ...]


class EvidenceLineageEdgeViewModel(FrozenEvidenceWorkflowViewModel):
    id: str
    source_id: str
    target_id: str
    relation: str
    direction: str


class EvidenceLineagePathViewModel(FrozenEvidenceWorkflowViewModel):
    path_id: str
    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]


class EvidenceLineageViewModel(FrozenEvidenceWorkflowViewModel):
    evidence_id: str
    graph_snapshot_id: str
    proof_packet_id: str
    historical: bool
    completeness: str
    nodes: tuple[EvidenceLineageNodeViewModel, ...]
    edges: tuple[EvidenceLineageEdgeViewModel, ...]
    paths: tuple[EvidenceLineagePathViewModel, ...]
    limitations: tuple[str, ...]


class EvidenceReplayViewModel(FrozenEvidenceWorkflowViewModel):
    replay_id: str
    evidence_id: str
    graph_snapshot_id: str
    eligibility: str
    status: str
    immutable_input_ids: tuple[str, ...]
    method_id: str
    method_version: str
    original_identity: str
    reproduced_identity: str
    comparison_scope: str
    replayed_at: str
    limitations: tuple[str, ...]


class EvidenceVerificationViewModel(FrozenEvidenceWorkflowViewModel):
    verification_id: str
    evidence_id: str
    graph_snapshot_id: str
    verifier_id: str
    verifier_version: str
    scope: str
    status: str
    verified_at: str
    proposition: str
    limitations: tuple[str, ...]


class EvidenceExportViewModel(FrozenEvidenceWorkflowViewModel):
    export_id: str
    evidence_id: str
    graph_snapshot_id: str
    proof_packet_id: str
    schema_version: str
    media_type: str
    filename: str
    content_digest: str
    integrity_status: str
    limitations: tuple[str, ...]


def _value(value: object) -> str:
    return str(getattr(value, "root", value))


def adapt_evidence_lineage(dto: SafeEvidenceLineageDTO) -> EvidenceLineageViewModel:
    return EvidenceLineageViewModel(
        evidence_id=dto.evidence.evidence_id,
        graph_snapshot_id=dto.graph_snapshot_id,
        proof_packet_id=dto.proof_packet_id,
        historical=dto.historical,
        completeness=_value(dto.completeness),
        nodes=tuple(
            EvidenceLineageNodeViewModel(
                id=item.id,
                kind=_value(item.kind),
                label=item.label,
                producer=item.producer or "Not provided",
                producer_version=item.producer_version or "Not provided",
                captured_at=item.captured_at.isoformat() if item.captured_at else "Not provided",
                limitations=tuple(item.limitations or ()),
            )
            for item in dto.nodes
        ),
        edges=tuple(
            EvidenceLineageEdgeViewModel(
                id=item.id,
                source_id=item.source_id,
                target_id=item.target_id,
                relation=_value(item.relation),
                direction=item.direction,
            )
            for item in dto.edges
        ),
        paths=tuple(
            EvidenceLineagePathViewModel(
                path_id=item.path_id,
                node_ids=tuple(item.node_ids),
                edge_ids=tuple(item.edge_ids),
            )
            for item in dto.paths
        ),
        limitations=tuple(dto.limitations or ()),
    )


def adapt_evidence_replay(dto: SafeEvidenceReplayDTO) -> EvidenceReplayViewModel:
    return EvidenceReplayViewModel(
        replay_id=dto.replay_id,
        evidence_id=dto.evidence_id,
        graph_snapshot_id=dto.graph_snapshot_id,
        eligibility=_value(dto.eligibility),
        status=_value(dto.status),
        immutable_input_ids=tuple(dto.immutable_input_ids),
        method_id=dto.method_id,
        method_version=dto.method_version,
        original_identity=dto.original_identity,
        reproduced_identity=dto.reproduced_identity or "Not reproduced",
        comparison_scope=dto.comparison_scope,
        replayed_at=dto.replayed_at.isoformat(),
        limitations=tuple(dto.limitations or ()),
    )


def adapt_evidence_verification(
    dto: SafeEvidenceVerificationDTO,
) -> EvidenceVerificationViewModel:
    return EvidenceVerificationViewModel(
        verification_id=dto.verification_id,
        evidence_id=dto.evidence_id,
        graph_snapshot_id=dto.graph_snapshot_id,
        verifier_id=dto.verifier_id,
        verifier_version=dto.verifier_version,
        scope=_value(dto.scope),
        status=_value(dto.status),
        verified_at=dto.verified_at.isoformat(),
        proposition=dto.proposition,
        limitations=tuple(dto.limitations or ()),
    )


def adapt_evidence_export(dto: SafeEvidenceExportDTO) -> EvidenceExportViewModel:
    return EvidenceExportViewModel(
        export_id=dto.export_id,
        evidence_id=dto.evidence_id,
        graph_snapshot_id=dto.graph_snapshot_id,
        proof_packet_id=dto.proof_packet_id,
        schema_version=dto.schema_version,
        media_type=dto.media_type,
        filename=dto.filename,
        content_digest=dto.content_digest,
        integrity_status=dto.integrity_status,
        limitations=tuple(dto.limitations or ()),
    )
