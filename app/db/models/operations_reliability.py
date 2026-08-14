from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class OperationsIncident(Base):
    __tablename__ = "operations_incidents"
    __table_args__ = (
        UniqueConstraint(
            "active_correlation_key", name="uq_operations_incident_active_correlation"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    correlation_key: Mapped[str] = mapped_column(String(320), index=True)
    active_correlation_key: Mapped[str | None] = mapped_column(String(320), nullable=True)
    detector_id: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    affected_target: Mapped[str] = mapped_column(String(200), index=True)
    summary: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(160))
    limitations: Mapped[str] = mapped_column(Text, default="")
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class OperationsIncidentTransition(Base):
    __tablename__ = "operations_incident_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("operations_incidents.incident_id"), index=True
    )
    transition: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))
    severity: Mapped[str] = mapped_column(String(20))
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    source: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(String(500))
