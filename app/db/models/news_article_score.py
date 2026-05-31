from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NewsArticleScore(Base):
    __tablename__ = "news_article_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id"), index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("news_events.id"), nullable=True, index=True)
    btc_relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    market_impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    urgency_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    institutional_score: Mapped[float] = mapped_column(Float, default=0.0)
    macro_score: Mapped[float] = mapped_column(Float, default=0.0)
    regulatory_score: Mapped[float] = mapped_column(Float, default=0.0)
    security_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    sovereignty_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_label: Mapped[str] = mapped_column(String(16), default="UNCERTAIN")
    risk_band: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    score_version: Mapped[str] = mapped_column(String(32), default="v1_rule_based")
    scoring_method: Mapped[str] = mapped_column(String(32), default="RULE_BASED")
    explanation_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    factor_breakdown_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    limitations_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
