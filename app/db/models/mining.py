from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.time_utils import utcnow


class CapabilityState(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    CLAIMED_UNVERIFIED = "claimed_unverified"
    VERIFIED = "verified"


class SeverityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SourceType(StrEnum):
    REAL = "real"
    FALLBACK = "fallback"
    SYNTHETIC = "synthetic"
    UNKNOWN = "unknown"


class TemplateControlOwner(StrEnum):
    MINER = "miner"
    POOL = "pool"
    TEMPLATE_PROVIDER = "template_provider"
    SHARED = "shared"
    UNKNOWN = "unknown"


class MiningPool(Base):
    __tablename__ = "mining_pools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False, default="unknown")

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default=SourceType.UNKNOWN.value)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    freshness_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    endpoints: Mapped[list[MiningPoolEndpoint]] = relationship(back_populates="pool", cascade="all, delete-orphan")
    stratum_v2_capabilities: Mapped[list[StratumV2Capability]] = relationship(
        back_populates="pool", cascade="all, delete-orphan"
    )
    sovereignty_scores: Mapped[list[PoolSovereigntyScore]] = relationship(
        back_populates="pool", cascade="all, delete-orphan"
    )
    censorship_risks: Mapped[list[MiningCensorshipRisk]] = relationship(
        back_populates="pool", cascade="all, delete-orphan"
    )
    template_control_assessments: Mapped[list[TemplateControlAssessment]] = relationship(
        back_populates="pool", cascade="all, delete-orphan"
    )
    signals: Mapped[list[MiningSignal]] = relationship(back_populates="pool", cascade="all, delete-orphan")


class MiningPoolEndpoint(Base):
    __tablename__ = "mining_pool_endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("mining_pools.id"), nullable=False, index=True)
    endpoint_type: Mapped[str] = mapped_column(String(40), nullable=False, default="api")
    endpoint_url: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    network: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown")

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default=SourceType.UNKNOWN.value)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    freshness_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    pool: Mapped[MiningPool] = relationship(back_populates="endpoints")


class StratumV2Capability(Base):
    __tablename__ = "stratum_v2_capabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("mining_pools.id"), nullable=False, index=True)

    capability_state: Mapped[str] = mapped_column(String(40), nullable=False, default=CapabilityState.UNKNOWN.value, index=True)
    job_declaration_state: Mapped[str] = mapped_column(String(40), nullable=False, default=CapabilityState.UNKNOWN.value)
    translator_proxy_state: Mapped[str] = mapped_column(String(40), nullable=False, default=CapabilityState.UNKNOWN.value)
    encrypted_channel_state: Mapped[str] = mapped_column(String(40), nullable=False, default=CapabilityState.UNKNOWN.value)

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default=SourceType.UNKNOWN.value)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    freshness_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    pool: Mapped[MiningPool] = relationship(back_populates="stratum_v2_capabilities")


class PoolSovereigntyScore(Base):
    __tablename__ = "pool_sovereignty_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("mining_pools.id"), nullable=False, index=True)

    score_100: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default=SeverityLevel.UNKNOWN.value)
    factor_breakdown_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    explainability_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default=SourceType.UNKNOWN.value)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    freshness_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    pool: Mapped[MiningPool] = relationship(back_populates="sovereignty_scores")


class MiningCensorshipRisk(Base):
    __tablename__ = "mining_censorship_risks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("mining_pools.id"), nullable=False, index=True)

    risk_score_100: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default=SeverityLevel.UNKNOWN.value, index=True)
    factor_breakdown_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    explainability_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default=SourceType.UNKNOWN.value)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    freshness_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    window_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    pool: Mapped[MiningPool] = relationship(back_populates="censorship_risks")


class TemplateControlAssessment(Base):
    __tablename__ = "template_control_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int] = mapped_column(ForeignKey("mining_pools.id"), nullable=False, index=True)

    template_control_state: Mapped[str] = mapped_column(String(50), nullable=False, default=CapabilityState.UNKNOWN.value)
    template_control_owner: Mapped[str] = mapped_column(
        String(40), nullable=False, default=TemplateControlOwner.UNKNOWN.value
    )
    template_sovereignty_score_100: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    template_interference_risk_score_100: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mitm_risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default=SeverityLevel.UNKNOWN.value)
    explainability_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default=SourceType.UNKNOWN.value)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    freshness_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    pool: Mapped[MiningPool] = relationship(back_populates="template_control_assessments")


class MiningSignal(Base):
    __tablename__ = "mining_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pool_id: Mapped[int | None] = mapped_column(ForeignKey("mining_pools.id"), nullable=True, index=True)

    signal_type: Mapped[str] = mapped_column(String(60), nullable=False, default="MINING_SOVEREIGNTY")
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default=SeverityLevel.UNKNOWN.value)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, default=SourceType.UNKNOWN.value)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False, default="unknown")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    freshness_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    title: Mapped[str] = mapped_column(String(220), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    explainability_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    limitations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    evidence_refs_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    pool: Mapped[MiningPool | None] = relationship(back_populates="signals")
