from __future__ import annotations

import hashlib
import json

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.db.models.bastion_trace import TraceGraphSnapshotModel
from app.schemas.trace_graph import TraceGraphDTO, TraceGraphHistoryDTO, TraceGraphHistoryEntryDTO
from app.services.bastion_trace.graph.api_projection import BUILDER_VERSION, SCHEMA_VERSION


class TraceGraphSnapshotRepository:
    """Append-only GS1 persistence validated by the strict TraceGraphDTO schema."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def is_available(self) -> bool:
        return bool(inspect(self._db.get_bind()).has_table(TraceGraphSnapshotModel.__tablename__))

    def capture(self, report_id: int, graph: TraceGraphDTO) -> TraceGraphDTO:
        if not self.is_available():
            return graph
        topology_id = graph.snapshot.topology_snapshot_id or "topology-unavailable"
        existing = self._db.execute(
            select(TraceGraphSnapshotModel).where(
                TraceGraphSnapshotModel.report_id == report_id,
                TraceGraphSnapshotModel.topology_snapshot_id == topology_id,
                TraceGraphSnapshotModel.builder_version == BUILDER_VERSION,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return self._decode(existing)
        payload = graph.model_dump(mode="json")
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        self._db.add(
            TraceGraphSnapshotModel(
                id=graph.snapshot.snapshot_id,
                report_id=report_id,
                topology_snapshot_id=topology_id,
                claim_capture_id=f"trace_report:{report_id}",
                snapshot_schema_version=SCHEMA_VERSION,
                graph_version=graph.metadata.graph_version,
                builder_version=BUILDER_VERSION,
                graph_digest=digest,
                graph_payload_json=canonical,
                created_at=graph.metadata.created_at,
            )
        )
        self._db.commit()
        return graph

    def exact(self, report_id: int, snapshot_id: str) -> TraceGraphDTO | None:
        if not self.is_available():
            return None
        row = self._db.execute(
            select(TraceGraphSnapshotModel).where(
                TraceGraphSnapshotModel.report_id == report_id,
                TraceGraphSnapshotModel.id == snapshot_id,
            )
        ).scalar_one_or_none()
        return self._decode(row) if row is not None else None

    def history(self, report_id: int) -> TraceGraphHistoryDTO:
        rows = tuple(self._db.execute(
            select(TraceGraphSnapshotModel)
            .where(TraceGraphSnapshotModel.report_id == report_id)
            .order_by(TraceGraphSnapshotModel.created_at, TraceGraphSnapshotModel.id)
        ).scalars())
        graphs = tuple(self._decode(row) for row in rows)
        return TraceGraphHistoryDTO(
            graph_id=graphs[-1].metadata.graph_id if graphs else "",
            entries=[TraceGraphHistoryEntryDTO.from_graph(graph) for graph in graphs],
        )

    @staticmethod
    def _decode(row: TraceGraphSnapshotModel) -> TraceGraphDTO:
        graph = TraceGraphDTO.model_validate_json(row.graph_payload_json)
        canonical = json.dumps(graph.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        if hashlib.sha256(canonical.encode()).hexdigest() != row.graph_digest:
            raise ValueError("Trace Graph snapshot digest mismatch")
        return graph
