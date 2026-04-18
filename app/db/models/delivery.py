from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("signals.id"), nullable=True, index=True)
    digest_id: Mapped[str] = mapped_column(String(120), default="")
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    channel_type: Mapped[str] = mapped_column(String(40), default="telegram")
    destination: Mapped[str] = mapped_column(String(255), default="")
    provider_message_id: Mapped[str] = mapped_column(String(120), default="")
    delivery_status: Mapped[str] = mapped_column(String(40), default="sent")
    error_message: Mapped[str] = mapped_column(Text, default="")
    payload_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
