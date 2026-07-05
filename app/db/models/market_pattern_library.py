from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class MarketPatternLibrary(Base):
    __tablename__ = "market_pattern_library"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), default="")
    description: Mapped[str] = mapped_column(String(500), default="")
    expected_sentiment: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    expected_time_windows: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    default_confidence_band: Mapped[str] = mapped_column(String(32), default="Moderate")
    default_sentiment: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    expected_reaction_window: Mapped[str] = mapped_column(String(32), default="unknown")
    expected_volatility: Mapped[str] = mapped_column(String(32), default="normal")
    confidence_modifier: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
