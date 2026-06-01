from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NewsArticle(Base):
    __tablename__ = "news_articles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid4()), unique=True, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    canonical_url_hash: Mapped[str] = mapped_column(String(64), index=True)
    title_hash: Mapped[str] = mapped_column(String(64), index=True)
    normalized_title_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    author: Mapped[str] = mapped_column(String(255), default="")
    language: Mapped[str] = mapped_column(String(8), default="en")
    summary: Mapped[str] = mapped_column(Text, default="")
    raw_content: Mapped[str] = mapped_column(Text, default="")
    content_text: Mapped[str] = mapped_column(Text, default="")
    content_clean: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    article_type: Mapped[str] = mapped_column(String(64), default="NEWS")
    category: Mapped[str] = mapped_column(String(80), default="general")
    ingestion_method: Mapped[str] = mapped_column(String(32), default="RSS")
    provider_confidence: Mapped[float] = mapped_column(Float, default=0.5)
    fetch_status: Mapped[str] = mapped_column(String(32), default="fetched")
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    etag: Mapped[str] = mapped_column(String(255), default="")
    last_modified: Mapped[str] = mapped_column(String(255), default="")
    content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str] = mapped_column(String(120), default="")
    sentiment_label: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    btc_relevance_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    market_impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    credibility_score: Mapped[float] = mapped_column(Float, default=0.0)
    urgency_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_duplicate_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_candidate_reason: Mapped[str] = mapped_column(String(120), default="")
    duplicate_of_id: Mapped[int | None] = mapped_column(ForeignKey("news_articles.id"), nullable=True, index=True)
    deduplication_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("news_article_clusters.id"), nullable=True, index=True)
    is_canonical: Mapped[bool] = mapped_column(Boolean, default=False)
    deduplication_reason: Mapped[str] = mapped_column(String(255), default="")
    deduplication_metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB().with_variant(JSON(), "sqlite"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
