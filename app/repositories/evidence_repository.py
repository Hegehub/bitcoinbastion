from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.evidence_packet import (
    EvidenceArtifact,
    EvidenceIntegritySnapshot,
    EvidencePacket,
    EvidenceRelationship,
    EvidenceReplayLog,
)


class EvidenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_packet(self, row: EvidencePacket) -> EvidencePacket:
        self.db.add(row)
        self.db.flush()
        return row

    def get_packet(self, packet_id: int) -> EvidencePacket | None:
        return self.db.get(EvidencePacket, packet_id)

    def list_packets(self, *, limit: int = 50) -> list[EvidencePacket]:
        return list(self.db.execute(select(EvidencePacket).order_by(EvidencePacket.created_at.desc()).limit(limit)).scalars())

    def add_artifact(self, row: EvidenceArtifact) -> EvidenceArtifact:
        self.db.add(row)
        self.db.flush()
        return row

    def artifacts_for_packet(self, packet_id: int) -> list[EvidenceArtifact]:
        return list(
            self.db.execute(
                select(EvidenceArtifact)
                .where(EvidenceArtifact.packet_id == packet_id)
                .order_by(EvidenceArtifact.created_at.asc(), EvidenceArtifact.id.asc())
            ).scalars()
        )

    def add_relationship(self, row: EvidenceRelationship) -> EvidenceRelationship:
        existing = self.db.execute(
            select(EvidenceRelationship).where(
                EvidenceRelationship.parent_entity_type == row.parent_entity_type,
                EvidenceRelationship.parent_entity_id == row.parent_entity_id,
                EvidenceRelationship.child_entity_type == row.child_entity_type,
                EvidenceRelationship.child_entity_id == row.child_entity_id,
                EvidenceRelationship.relationship_type == row.relationship_type,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        self.db.add(row)
        self.db.flush()
        return row

    def relationships_for_entity(self, entity_type: str, entity_id: int) -> list[EvidenceRelationship]:
        return list(
            self.db.execute(
                select(EvidenceRelationship)
                .where(
                    ((EvidenceRelationship.parent_entity_type == entity_type) & (EvidenceRelationship.parent_entity_id == entity_id))
                    | ((EvidenceRelationship.child_entity_type == entity_type) & (EvidenceRelationship.child_entity_id == entity_id))
                )
                .order_by(EvidenceRelationship.created_at.asc(), EvidenceRelationship.id.asc())
            ).scalars()
        )

    def add_integrity_snapshot(self, row: EvidenceIntegritySnapshot) -> EvidenceIntegritySnapshot:
        self.db.add(row)
        self.db.flush()
        return row

    def latest_integrity_snapshot(self, entity_type: str, entity_id: int) -> EvidenceIntegritySnapshot | None:
        return self.db.execute(
            select(EvidenceIntegritySnapshot)
            .where(EvidenceIntegritySnapshot.entity_type == entity_type, EvidenceIntegritySnapshot.entity_id == entity_id)
            .order_by(EvidenceIntegritySnapshot.created_at.desc(), EvidenceIntegritySnapshot.id.desc())
            .limit(1)
        ).scalar_one_or_none()

    def add_replay_log(self, row: EvidenceReplayLog) -> EvidenceReplayLog:
        self.db.add(row)
        self.db.flush()
        return row
