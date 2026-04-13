from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OnchainEvent(Base):
    __tablename__ = "onchain_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    txid: Mapped[str] = mapped_column(String(128), default="")
    address: Mapped[str] = mapped_column(String(128), default="")
    value_sats: Mapped[int] = mapped_column(Integer, default=0)
    block_height: Mapped[int] = mapped_column(Integer, default=0)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    provider: Mapped[str] = mapped_column(String(120), default="mock")
    raw_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    significance_score: Mapped[float] = mapped_column(Float, default=0.0)
    tags: Mapped[str] = mapped_column(String(255), default="")
