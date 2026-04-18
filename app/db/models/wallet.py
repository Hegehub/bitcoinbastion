from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class WalletProfile(Base):
    __tablename__ = "wallet_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    descriptor_or_reference: Mapped[str] = mapped_column(String(255), default="")
    wallet_type: Mapped[str] = mapped_column(String(50), default="single-sig")
    watch_only: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class WalletHealthReport(Base):
    __tablename__ = "wallet_health_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_profile_id: Mapped[int] = mapped_column(ForeignKey("wallet_profiles.id"), index=True)
    health_score: Mapped[float] = mapped_column(Float, default=0.0)
    utxo_fragmentation_score: Mapped[float] = mapped_column(Float, default=0.0)
    privacy_score: Mapped[float] = mapped_column(Float, default=0.0)
    fee_exposure_score: Mapped[float] = mapped_column(Float, default=0.0)
    findings_json: Mapped[str] = mapped_column(Text, default="[]")
    recommendations_json: Mapped[str] = mapped_column(Text, default="[]")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
