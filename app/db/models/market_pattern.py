from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class MarketPattern(Base):
    __tablename__ = "market_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), default="")
    category: Mapped[str] = mapped_column(String(64), index=True, default="unknown")
    description: Mapped[str] = mapped_column(String(600), default="")
    expected_sentiment: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    expected_direction: Mapped[str] = mapped_column(String(16), default="UNKNOWN")
    typical_impact_window: Mapped[str] = mapped_column(String(32), default="1h")
    historical_reaction_profile_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    confidence_rules_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=dict
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
