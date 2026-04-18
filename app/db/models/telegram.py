from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class TelegramDeliveryLog(Base):
    __tablename__ = "telegram_delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), nullable=False)
    chat_id: Mapped[str] = mapped_column(String(120), nullable=False)
    message_id: Mapped[str] = mapped_column(String(120), default="")
    delivery_type: Mapped[str] = mapped_column(String(40), default="signal")
    status: Mapped[str] = mapped_column(String(40), default="sent")
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    error_message: Mapped[str] = mapped_column(Text, default="")
