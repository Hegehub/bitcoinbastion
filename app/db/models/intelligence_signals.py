from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class IntelligenceSignalCandidate(Base):
    __tablename__ = "intelligence_signal_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_entity_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True, index=True)
    candle_id: Mapped[int | None] = mapped_column(ForeignKey("btc_candles.id"), nullable=True, index=True)
    impact_id: Mapped[int | None] = mapped_column(ForeignKey("news_price_impacts.id"), nullable=True, index=True)
    attribution_id: Mapped[int | None] = mapped_column(ForeignKey("candle_attributions.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    btc_relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    provider_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    direction_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dominant_window: Mapped[str | None] = mapped_column(String(32), nullable=True)
    evidence_packet_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    policy_decision: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    policy_reason: Mapped[str] = mapped_column(Text, default="")
    requires_operator_review: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class IntelligenceOperatorReview(Base):
    __tablename__ = "intelligence_operator_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_candidate_id: Mapped[int] = mapped_column(ForeignKey("intelligence_signal_candidates.id"), index=True, nullable=False)
    review_status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    reviewer_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    operator_note: Mapped[str] = mapped_column(Text, default="")
    decision_reason: Mapped[str] = mapped_column(Text, default="")
    false_positive_marker: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confidence_override: Mapped[float | None] = mapped_column(Float, nullable=True)
    publish_override: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class IntelligencePublishingPolicy(Base):
    __tablename__ = "intelligence_publishing_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, default="default")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    min_btc_relevance_score: Mapped[float] = mapped_column(Float, default=0.45)
    min_impact_confidence: Mapped[float] = mapped_column(Float, default=0.65)
    min_source_confidence: Mapped[float] = mapped_column(Float, default=0.60)
    min_provider_confidence: Mapped[float] = mapped_column(Float, default=0.60)
    allow_auto_publish: Mapped[bool] = mapped_column(Boolean, default=False)
    require_review_for_security_shock: Mapped[bool] = mapped_column(Boolean, default=True)
    require_review_for_regulatory_shock: Mapped[bool] = mapped_column(Boolean, default=True)
    require_review_for_low_confidence: Mapped[bool] = mapped_column(Boolean, default=True)
    require_review_for_provider_degraded: Mapped[bool] = mapped_column(Boolean, default=True)
    require_review_for_false_signal: Mapped[bool] = mapped_column(Boolean, default=True)
    max_signals_per_hour: Mapped[int] = mapped_column(Integer, default=20)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=15)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class IntelligenceSignalDeliveryLog(Base):
    __tablename__ = "intelligence_signal_delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_candidate_id: Mapped[int] = mapped_column(ForeignKey("intelligence_signal_candidates.id"), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    target: Mapped[str] = mapped_column(String(160), default="")
    message_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message_sanitized: Mapped[str | None] = mapped_column(String(500), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
