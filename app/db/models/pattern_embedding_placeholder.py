from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class PatternEmbeddingPlaceholder(Base):
    __tablename__ = "pattern_embeddings_placeholder"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_id: Mapped[int] = mapped_column(
        ForeignKey("market_patterns.id"), index=True, nullable=False
    )
    embedding_provider: Mapped[str] = mapped_column(String(64), default="none")
    embedding_version: Mapped[str] = mapped_column(String(64), default="deterministic_placeholder")
    vector_json: Mapped[list[float]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), default=list
    )
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
