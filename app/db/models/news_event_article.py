from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NewsEventArticle(Base):
    __tablename__ = "news_event_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("news_events.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("news_articles.id"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), default="supporting")
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_primary_source: Mapped[bool] = mapped_column(Boolean, default=False)
    time_distance_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
