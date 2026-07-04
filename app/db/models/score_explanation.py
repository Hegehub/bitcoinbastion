from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class ScoreExplanation(Base):
    __tablename__ = "score_explanations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    score_id: Mapped[int] = mapped_column(ForeignKey("news_scores.id"), index=True)
    summary: Mapped[str] = mapped_column(String(500), default="")
    key_factors_json: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    limitations_json: Mapped[list[str]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
