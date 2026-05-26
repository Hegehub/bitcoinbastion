from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class NewsRawPayload(Base):
    __tablename__ = "news_raw_payloads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("news_sources.id"), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    payload_sha256: Mapped[str] = mapped_column(String(64))
    payload_format: Mapped[str] = mapped_column(String(32), default="xml")
    raw_payload: Mapped[str] = mapped_column(Text)
    compression: Mapped[str] = mapped_column(String(32), default="none")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
