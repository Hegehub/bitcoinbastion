from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class EvidencePacket(Base):
    __tablename__ = "evidence_packets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    packet_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True, index=True)
    impact_id: Mapped[int | None] = mapped_column(ForeignKey("news_price_impacts.id"), nullable=True, index=True)
    attribution_id: Mapped[int | None] = mapped_column(ForeignKey("candle_attributions.id"), nullable=True, index=True)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("intelligence_signal_candidates.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class EvidenceRelationship(Base):
    __tablename__ = "evidence_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    parent_entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    child_entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    child_entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class EvidenceArtifact(Base):
    __tablename__ = "evidence_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    packet_id: Mapped[int | None] = mapped_column(ForeignKey("evidence_packets.id"), nullable=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    artifact_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class EvidenceIntegritySnapshot(Base):
    __tablename__ = "evidence_integrity_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(32), default="sha256", nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class EvidenceReplayLog(Base):
    __tablename__ = "evidence_replay_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    step_name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    input_hash: Mapped[str] = mapped_column(String(128), default="")
    output_hash: Mapped[str] = mapped_column(String(128), default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
