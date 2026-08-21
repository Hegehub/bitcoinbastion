from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class TraceReport(Base):
    __tablename__ = "trace_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idempotency_key_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    address: Mapped[str] = mapped_column(String(128), index=True)
    chain: Mapped[str] = mapped_column(String(32), default="bitcoin")
    trace_score: Mapped[float] = mapped_column(Float, default=0.0)
    trace_band: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    source_quality: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    freshness: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    summary: Mapped[str] = mapped_column(Text, default="")
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    operator_guidance_json: Mapped[str] = mapped_column(Text, default="[]")
    reason_codes_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    origin_passport_json: Mapped[str] = mapped_column(Text, default="{}")
    provider_disagreement_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_independence_json: Mapped[str] = mapped_column(Text, default="{}")
    source_status_summary_json: Mapped[str] = mapped_column(Text, default="[]")
    privacy_shield_json: Mapped[str] = mapped_column(Text, default="{}")
    utxo_hygiene_json: Mapped[str] = mapped_column(Text, default="{}")
    dust_radar_json: Mapped[str] = mapped_column(Text, default="{}")
    address_reuse_json: Mapped[str] = mapped_column(Text, default="{}")
    consolidation_risk_json: Mapped[str] = mapped_column(Text, default="{}")
    toxic_change_json: Mapped[str] = mapped_column(Text, default="{}")
    counterparty_lens_json: Mapped[str] = mapped_column(Text, default="{}")
    advisory_not_legal_verdict: Mapped[bool] = mapped_column(Boolean, default=True)
    not_consensus_proof: Mapped[bool] = mapped_column(Boolean, default=True)
    no_custody: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TraceEvidence(Base):
    __tablename__ = "trace_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("trace_reports.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(64), default="unknown")
    source_name: Mapped[str] = mapped_column(String(120), default="baseline")
    source_type: Mapped[str] = mapped_column(String(64), default="baseline")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    freshness_days: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence_ref: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TraceClaimModel(Base):
    __tablename__ = "trace_claims"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("trace_reports.id"), index=True)
    capture_id: Mapped[str] = mapped_column(String(64), index=True)
    claim_schema_version: Mapped[str] = mapped_column(String(64))
    subject_kind: Mapped[str] = mapped_column(String(64))
    subject_id: Mapped[str] = mapped_column(String(96), index=True)
    subject_public_value: Mapped[str] = mapped_column(String(256))
    predicate: Mapped[str] = mapped_column(String(64), index=True)
    value_kind: Mapped[str] = mapped_column(String(64))
    value_text: Mapped[str] = mapped_column(String(128))
    producer_id: Mapped[str] = mapped_column(String(128), index=True)
    producer_version: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[str] = mapped_column(String(128), index=True)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_references_json: Mapped[str] = mapped_column(Text, default="[]")
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TraceGraphSnapshotModel(Base):
    """Append-only, versioned capture of one exact Trace Graph."""

    __tablename__ = "trace_graph_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "report_id", "topology_snapshot_id", "builder_version", name="uq_trace_graph_capture"
        ),
    )

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("trace_reports.id"), index=True)
    topology_snapshot_id: Mapped[str] = mapped_column(String(96), index=True)
    claim_capture_id: Mapped[str] = mapped_column(String(64), index=True)
    snapshot_schema_version: Mapped[str] = mapped_column(String(64))
    graph_version: Mapped[str] = mapped_column(String(64))
    builder_version: Mapped[str] = mapped_column(String(64))
    graph_digest: Mapped[str] = mapped_column(String(64))
    graph_payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TraceSource(Base):
    __tablename__ = "trace_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(120), unique=True)
    source_type: Mapped[str] = mapped_column(String(64), default="baseline")
    trust_level: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TraceSourceSnapshot(Base):
    __tablename__ = "trace_source_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("trace_sources.id"), index=True)
    last_refreshed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    freshness: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    last_refresh_status: Mapped[str] = mapped_column(String(64), default="baseline")
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TraceWatchlistEntry(Base):
    __tablename__ = "trace_watchlist_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(128), index=True)
    label: Mapped[str] = mapped_column(String(120), default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    risk_hint: Mapped[str] = mapped_column(String(64), default="UNKNOWN")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TraceBatch(Base):
    __tablename__ = "trace_batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_label: Mapped[str] = mapped_column(String(120), default="")
    business_context: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    policy_profile_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_addresses: Mapped[int] = mapped_column(Integer, default=0)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    low_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    unknown_count: Mapped[int] = mapped_column(Integer, default=0)
    manual_review_count: Mapped[int] = mapped_column(Integer, default=0)
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TraceBatchItem(Base):
    __tablename__ = "trace_batch_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("trace_batches.id"), index=True)
    address: Mapped[str] = mapped_column(String(128))
    report_id: Mapped[int | None] = mapped_column(ForeignKey("trace_reports.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="processed")
    rejection_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    trace_band: Mapped[str | None] = mapped_column(String(32), nullable=True)
    trace_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    policy_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manual_review_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TraceBusinessPolicyProfileModel(Base):
    __tablename__ = "trace_business_policy_profiles"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    context_type: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    low_action: Mapped[str] = mapped_column(String(64), default="ACCEPT")
    medium_action: Mapped[str] = mapped_column(String(64), default="HOLD_FOR_REVIEW")
    high_action: Mapped[str] = mapped_column(String(64), default="HOLD_FOR_REVIEW")
    critical_action: Mapped[str] = mapped_column(String(64), default="REJECT_BY_POLICY")
    unknown_action: Mapped[str] = mapped_column(String(64), default="INSUFFICIENT_INFORMATION")
    manual_review_threshold: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    high_value_threshold_sats: Mapped[int] = mapped_column(Integer, default=5_000_000)
    require_review_on_provider_disagreement: Mapped[bool] = mapped_column(Boolean, default=True)
    require_review_on_low_confidence: Mapped[bool] = mapped_column(Boolean, default=True)
    require_review_on_privacy_high: Mapped[bool] = mapped_column(Boolean, default=False)
    limitations_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class TraceReviewItem(Base):
    __tablename__ = "trace_review_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("trace_reports.id"), nullable=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("trace_batches.id"), nullable=True)
    address: Mapped[str] = mapped_column(String(128))
    review_status: Mapped[str] = mapped_column(String(32), default="OPEN")
    review_priority: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    assigned_to: Mapped[str | None] = mapped_column(String(120), nullable=True)
    operator_note_count: Mapped[int] = mapped_column(Integer, default=0)
    decision: Mapped[str] = mapped_column(String(64), default="NO_DECISION")
    decision_reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class TraceOperatorNoteModel(Base):
    __tablename__ = "trace_operator_notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("trace_review_items.id"), nullable=True
    )
    report_id: Mapped[int | None] = mapped_column(ForeignKey("trace_reports.id"), nullable=True)
    note_type: Mapped[str] = mapped_column(String(64), default="GENERAL")
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    redacted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TraceBusinessProofPacketModel(Base):
    __tablename__ = "trace_business_proof_packets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("trace_reports.id"), index=True)
    review_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("trace_review_items.id"), nullable=True
    )
    policy_profile_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TraceBusinessExportModel(Base):
    __tablename__ = "trace_business_exports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("trace_batches.id"), nullable=True)
    report_id: Mapped[int | None] = mapped_column(ForeignKey("trace_reports.id"), nullable=True)
    format: Mapped[str] = mapped_column(String(32), default="JSON")
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class TraceBusinessEventModel(Base):
    __tablename__ = "trace_business_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
