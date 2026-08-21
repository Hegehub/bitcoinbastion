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
    TraceTopologySourceStatus,
)
from app.services.bastion_trace.graph.builder import TraceGraphBuilder
from app.services.bastion_trace.graph.domain import (
    TraceAnalyticalObject,
    TraceGraph,
    TraceObservation,
    TraceProvenance,
    TraceRelationship,
    stable_trace_id,
)
from app.services.bastion_trace.graph.topology_adapter import BitcoinTopologyGraphAdapter
from app.services.bitcoin_topology.engine import BitcoinTopologySnapshot
from app.services.bastion_trace.privacy_policy import TracePrivacyPolicy

BUILDER_VERSION = "trace-graph-builder-v1"
SCHEMA_VERSION = "trace-graph-schema-v1"


class TraceGraphApiProjectionService:
    def graph_for_report_model(
        self,
        report: TraceReportModel,
        topology_snapshot: BitcoinTopologySnapshot | None = None,
    ) -> TraceGraphDTO:
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
        if topology_snapshot is not None:
            builder.add_topology_projection(BitcoinTopologyGraphAdapter().project(topology_snapshot))
        graph = builder.build()
        return self.to_dto(graph, report.created_at)

    def history_for_report_model(
        self,
        report: TraceReportModel,
        topology_snapshots: tuple[BitcoinTopologySnapshot, ...] = (),
    ) -> TraceGraphHistoryDTO:
        snapshots: tuple[BitcoinTopologySnapshot | None, ...] = topology_snapshots or (None,)
        graphs = tuple(self.graph_for_report_model(report, snapshot) for snapshot in snapshots)
        entries = [self._history_entry(graph) for graph in graphs]
        return TraceGraphHistoryDTO(graph_id=graphs[-1].metadata.graph_id, entries=entries)

    def _history_entry(self, graph: TraceGraphDTO) -> TraceGraphHistoryEntryDTO:
        return TraceGraphHistoryEntryDTO(
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
            topology_source_status=graph.metadata.topology_source_status,
            topology_snapshot_id=graph.metadata.topology_snapshot_id,
        )

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
            topology_source_status=(
                TraceTopologySourceStatus.AUTHORITATIVE
                if graph.metadata.topology_snapshot_id is not None
                else TraceTopologySourceStatus.TOPOLOGY_SOURCE_UNAVAILABLE
            ),
            topology_snapshot_id=graph.metadata.topology_snapshot_id,
            topology_version=graph.metadata.topology_version,
            topology_engine_version=graph.metadata.topology_engine_version,
            topology_network=graph.metadata.topology_network,
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
            topology_snapshot_id=snapshot.topology_snapshot_id,
        )
        values = TracePrivacyPolicy().allowlisted("graph", {
            "metadata": metadata,
            "objects": [self._object_to_dto(item) for item in graph.objects.values()],
            "relationships": [self._relationship_to_dto(item) for item in graph.relationships.values()],
            "observations": [self._observation_to_dto(item) for item in graph.observations.values()],
            "snapshot": snapshot_dto,
        })
        return TraceGraphDTO.model_validate(values)

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
            source_relationship_id=provenance.source_relationship_id,
            topology_snapshot_id=provenance.topology_snapshot_id,
        )

    def _object_to_dto(self, item: TraceAnalyticalObject) -> TraceGraphObjectDTO:
        return TraceGraphObjectDTO(
            id=item.id,
            kind=item.kind.value,
            label=item.label,
            provenance=self._provenance_to_dto(item.provenance),
            limitations=list(item.limitations),
        )

    def _relationship_to_dto(self, item: TraceRelationship) -> TraceGraphRelationshipDTO:
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

    def _observation_to_dto(self, item: TraceObservation) -> TraceGraphObservationDTO:
        return TraceGraphObservationDTO(
            id=item.id,
            kind=item.kind.value,
            subject=item.subject,
            value=item.value,
            provenance=self._provenance_to_dto(item.provenance),
            limitations=list(item.limitations),
        )
