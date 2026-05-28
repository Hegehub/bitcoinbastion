from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class ImpactConfidenceBreakdown(Base):
    __tablename__ = "impact_confidence_breakdowns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    impact_id: Mapped[int] = mapped_column(ForeignKey("news_price_impacts.id"), index=True, nullable=False)
    btc_relevance_component: Mapped[float] = mapped_column(Float, default=0.0)
    source_credibility_component: Mapped[float] = mapped_column(Float, default=0.0)
    price_strength_component: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_match_component: Mapped[float] = mapped_column(Float, default=0.0)
    provider_confidence_component: Mapped[float] = mapped_column(Float, default=0.0)
    freshness_component: Mapped[float] = mapped_column(Float, default=0.0)
    volatility_component: Mapped[float] = mapped_column(Float, default=0.0)
    final_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    explanation_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
