from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NewsSource(Base):
    __tablename__ = "news_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    kind: Mapped[str] = mapped_column(String(50), default="rss")
    base_url: Mapped[str] = mapped_column(String(255), default="")
    rss_url: Mapped[str] = mapped_column(String(255), nullable=False)
    credibility_weight: Mapped[float] = mapped_column(Float, default=1.0)
    language: Mapped[str] = mapped_column(String(8), default="en")
    category: Mapped[str] = mapped_column(String(80), default="general")
    is_active: Mapped[bool] = mapped_column(default=True)
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    author: Mapped[str] = mapped_column(String(120), default="")
    content_raw: Mapped[str] = mapped_column(Text, default="")
    content_clean: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(8), default="en")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    canonical_hash: Mapped[str] = mapped_column(String(64), default="")
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True)

    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    btc_relevance_score: Mapped[float] = mapped_column(Float, default=0.0)
    urgency_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    explainability_json: Mapped[str] = mapped_column(Text, default="{}")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
