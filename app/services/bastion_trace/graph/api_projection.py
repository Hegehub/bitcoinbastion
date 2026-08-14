from __future__ import annotations

import json
from datetime import UTC, datetime

from app.db.models.bastion_trace import TraceReport as TraceReportModel
from app.schemas.bastion_trace import TraceBand, TraceFreshness, TraceReport, TraceSourceQuality
from app.schemas.trace_graph import (
    TraceGraphApiVersion,
    TraceGraphDTO,
    TraceGraphEvidenceReferenceDTO,
    TraceGraphHistoryDTO,
    TraceGraphHistoryEntryDTO,
    TraceGraphMetadataDTO,
    TraceGraphObjectDTO,
    TraceGraphObservationDTO,
    TraceGraphProvenanceDTO,
    TraceGraphRelationshipDTO,
    TraceGraphSnapshotDTO,
    TraceSnapshotVersion,
)
from app.services.bastion_trace.graph.builder import TraceGraphBuilder
from app.services.bastion_trace.graph.domain import (
    TraceGraph,
    TraceProvenance,
    stable_trace_id,
)

BUILDER_VERSION = "trace-graph-builder-v1"
SCHEMA_VERSION = "trace-graph-schema-v1"


class TraceGraphApiProjectionService:
    def graph_for_report_model(self, report: TraceReportModel) -> TraceGraphDTO:
        schema = TraceReport(
            id=report.id,
            address=report.address,
            summary=report.summary,
            chain=report.chain,
            trace_score=report.trace_score,
            trace_band=TraceBand(report.trace_band),
            confidence=report.confidence,
            source_quality=TraceSourceQuality(report.source_quality),
            freshness=TraceFreshness(report.freshness),
            reason_codes=json.loads(report.reason_codes_json or "[]"),
            evidence_refs=json.loads(report.evidence_refs_json or "[]"),
            limitations=json.loads(report.limitations_json or "[]"),
            operator_guidance=json.loads(report.operator_guidance_json or "[]"),
            advisory_not_legal_verdict=report.advisory_not_legal_verdict,
            not_consensus_proof=report.not_consensus_proof,
            no_custody=report.no_custody,
            created_at=report.created_at,
        )
        builder = TraceGraphBuilder()
        builder.add_report_projection(schema)
        graph = builder.build()
        return self.to_dto(graph, report.created_at)

    def history_for_report_model(self, report: TraceReportModel) -> TraceGraphHistoryDTO:
        graph = self.graph_for_report_model(report)
        entry = TraceGraphHistoryEntryDTO(
            snapshot_id=graph.snapshot.snapshot_id,
            graph_id=graph.metadata.graph_id,
            graph_version=graph.metadata.graph_version,
            snapshot_version=graph.metadata.snapshot_version,
            api_version=graph.metadata.api_version,
            schema_version=graph.metadata.schema_version,
            builder_version=graph.metadata.builder_version,
            analysis_version=graph.metadata.analysis_version,
            created_at=graph.metadata.created_at,
            provenance_summary=sorted(
                {item.provenance.producer for item in graph.objects + graph.relationships}
            ),
            limitations=graph.metadata.limitations,
        )
        return TraceGraphHistoryDTO(graph_id=graph.metadata.graph_id, entries=[entry])

    def to_dto(self, graph: TraceGraph, created_at: datetime | None) -> TraceGraphDTO:
        creation_time = created_at or datetime.now(UTC)
        graph_id = stable_trace_id("trace_graph", graph.metadata.graph_hash)
        snapshot_id = stable_trace_id("trace_snapshot", graph.metadata.graph_hash, BUILDER_VERSION)
        metadata = TraceGraphMetadataDTO(
            graph_id=graph_id,
            graph_version=graph.metadata.graph_version,
            snapshot_version=TraceSnapshotVersion.V1,
            api_version=TraceGraphApiVersion.V1,
            schema_version=SCHEMA_VERSION,
            builder_version=BUILDER_VERSION,
            analysis_version=graph.metadata.analysis_version,
            chain=graph.metadata.chain,
            graph_hash=graph.metadata.graph_hash,
            created_at=creation_time,
            limitations=list(graph.limitations),
        )
        snapshot = graph.snapshot()
        snapshot_dto = TraceGraphSnapshotDTO(
            snapshot_id=snapshot_id,
            graph_id=graph_id,
            metadata=metadata,
            object_ids=snapshot.object_ids,
            relationship_ids=snapshot.relationship_ids,
            observation_ids=snapshot.observation_ids,
            report_fact_ids=snapshot.report_fact_ids,
        )
        return TraceGraphDTO(
            metadata=metadata,
            objects=[self._object_to_dto(item) for item in graph.objects.values()],
            relationships=[self._relationship_to_dto(item) for item in graph.relationships.values()],
            observations=[self._observation_to_dto(item) for item in graph.observations.values()],
            snapshot=snapshot_dto,
        )

    def _provenance_to_dto(self, provenance: TraceProvenance) -> TraceGraphProvenanceDTO:
        return TraceGraphProvenanceDTO(
            producer=provenance.producer,
            stage=provenance.stage,
            observations=list(provenance.observations),
            evidence=[
                TraceGraphEvidenceReferenceDTO(
                    reference=item.reference,
                    source_name=item.source_name,
                    source_type=item.source_type,
                )
                for item in provenance.evidence
            ],
            limitations=list(provenance.limitations),
        )

    def _object_to_dto(self, item) -> TraceGraphObjectDTO:
        return TraceGraphObjectDTO(
            id=item.id,
            kind=item.kind.value,
            label=item.label,
            provenance=self._provenance_to_dto(item.provenance),
            limitations=list(item.limitations),
        )

    def _relationship_to_dto(self, item) -> TraceGraphRelationshipDTO:
        return TraceGraphRelationshipDTO(
            id=item.id,
            source_id=item.source_id,
            target_id=item.target_id,
            relationship_type=item.relationship_type.value,
            direction=item.direction.value,
            originating_observation_id=item.originating_observation_id,
            provenance=self._provenance_to_dto(item.provenance),
            confidence=item.confidence,
            limitations=list(item.limitations),
        )

    def _observation_to_dto(self, item) -> TraceGraphObservationDTO:
        return TraceGraphObservationDTO(
            id=item.id,
            kind=item.kind.value,
            subject=item.subject,
            value=item.value,
            provenance=self._provenance_to_dto(item.provenance),
            limitations=list(item.limitations),
        )
