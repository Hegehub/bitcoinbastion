from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class CandleAttribution(Base):
    __tablename__ = "candle_attributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candle_id: Mapped[int] = mapped_column(ForeignKey("btc_candles.id"), index=True, nullable=False)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), index=True, nullable=True)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), index=True, nullable=True)
    signal_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    timeframe: Mapped[str] = mapped_column(String(16), index=True, default="")
    candle_open_time: Mapped[datetime] = mapped_column(DateTime)
    candle_close_time: Mapped[datetime] = mapped_column(DateTime)
    attribution_type: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    candidate_category: Mapped[str] = mapped_column(String(64), default="UNKNOWN")
    candidate_rank: Mapped[int] = mapped_column(Integer, default=0, index=True)
    time_distance_seconds: Mapped[int] = mapped_column(Integer, default=0)
    event_before_candle_seconds: Mapped[int] = mapped_column(Integer, default=0)
    event_inside_candle: Mapped[bool] = mapped_column(Boolean, default=False)
    event_after_candle_seconds: Mapped[int] = mapped_column(Integer, default=0)
    time_distance_weight: Mapped[float] = mapped_column(Float, default=0.0)
    price_move_pct: Mapped[float] = mapped_column(Float, default=0.0)
    candle_direction: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    direction_match: Mapped[bool] = mapped_column(Boolean, default=False)
    sentiment_direction_match: Mapped[str] = mapped_column(String(16), default="unknown")
    btc_relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    market_impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    event_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    impact_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    historical_similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    pattern_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    freshness_weight: Mapped[float] = mapped_column(Float, default=0.0)
    volatility_weight: Mapped[float] = mapped_column(Float, default=0.0)
    event_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    confidence_band: Mapped[str] = mapped_column(String(16), default="LOW")
    source_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_primary_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    is_operator_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_operator_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    operator_review_status: Mapped[str] = mapped_column(String(32), default="pending")
    operator_note: Mapped[str] = mapped_column(Text, default="")
    window_used: Mapped[str] = mapped_column(String(32), default="")
    dominant_window: Mapped[str] = mapped_column(String(32), default="")
    summary_text: Mapped[str] = mapped_column(Text, default="")
    explanation_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    limitations_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    evidence_refs_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
