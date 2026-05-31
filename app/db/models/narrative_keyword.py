from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NarrativeKeyword(Base):
    __tablename__ = "narrative_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    narrative_id: Mapped[int] = mapped_column(ForeignKey("market_narratives.id"), index=True)
    keyword: Mapped[str] = mapped_column(String(160), index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
