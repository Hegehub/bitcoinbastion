from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NewsPriceImpact(Base):
    __tablename__ = "news_price_impacts"
    __table_args__ = (
        Index("uq_news_price_impacts_article_id", "article_id", unique=True),
        Index("uq_news_price_impacts_event_id", "event_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_articles.id"), nullable=True, index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_events.id"), nullable=True, index=True
    )

    price_at_publish: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_after_15m: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_after_1h: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_after_4h: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_after_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_15m_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_1h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_4h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_24h_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_change_15m: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_change_1h: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_change_4h: Mapped[float | None] = mapped_column(Float, nullable=True)
    absolute_change_24h: Mapped[float | None] = mapped_column(Float, nullable=True)

    sentiment_label: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    expected_direction: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    actual_direction: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    direction_match: Mapped[str] = mapped_column(String(16), default="unknown")
    btc_relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    market_impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    impact_confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    dominant_window: Mapped[str] = mapped_column(String(16), default="UNKNOWN", index=True)
    volatility_context: Mapped[float] = mapped_column(Float, default=0.0)
    liquidity_context: Mapped[str] = mapped_column(String(32), default="unknown")
    impact_band: Mapped[str] = mapped_column(String(16), default="VERY_LOW", index=True)
    explanation_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    limitations_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    # Compatibility fields used by earlier impact-confidence endpoints.
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_band: Mapped[str] = mapped_column(String(16), default="VERY_LOW")
    confidence_contributions_json: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    degradation_factors_json: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    uncertainty_flags_json: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    delayed_reaction_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    false_signal_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    freshness_weight: Mapped[float] = mapped_column(Float, default=1.0)
    volatility_context_weight: Mapped[float] = mapped_column(Float, default=1.0)
    event_confirmation_weight: Mapped[float] = mapped_column(Float, default=0.5)
    explanation_summary: Mapped[str] = mapped_column(String(500), default="")
    limitation: Mapped[str] = mapped_column(
        String(200), default="Correlation-based attribution is not proof of causation."
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
