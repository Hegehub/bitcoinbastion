from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CitadelAssessment(Base):
    __tablename__ = "citadel_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_type: Mapped[str] = mapped_column(String(40), default="user", index=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True)

    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    custody_resilience_score: Mapped[float] = mapped_column(Float, default=0.0)
    recovery_readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    privacy_resilience_score: Mapped[float] = mapped_column(Float, default=0.0)
    treasury_resilience_score: Mapped[float] = mapped_column(Float, default=0.0)
    vendor_independence_score: Mapped[float] = mapped_column(Float, default=0.0)
    inheritance_readiness_score: Mapped[float] = mapped_column(Float, default=0.0)
    fee_survivability_score: Mapped[float] = mapped_column(Float, default=0.0)
    policy_maturity_score: Mapped[float] = mapped_column(Float, default=0.0)
    operational_hygiene_score: Mapped[float] = mapped_column(Float, default=0.0)

    critical_findings_json: Mapped[str] = mapped_column(Text, default="[]")
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    recommendations_json: Mapped[str] = mapped_column(Text, default="[]")
    explainability_json: Mapped[str] = mapped_column(Text, default="{}")
    freshness_json: Mapped[str] = mapped_column(Text, default="{}")

    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
