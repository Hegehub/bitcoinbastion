from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class OperationsEvidence(Base):
    __tablename__ = "operations_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    drill_id: Mapped[str] = mapped_column(String(120), index=True)
    drill_type: Mapped[str] = mapped_column(String(80), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    operator: Mapped[str] = mapped_column(String(120), default="system")
    notes: Mapped[str] = mapped_column(Text, default="")
    artifact_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class OperationsSLOSnapshot(Base):
    __tablename__ = "operations_slo_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slo_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(24), default="healthy", index=True)
    target: Mapped[str] = mapped_column(String(64), default="")
    observed_value: Mapped[str] = mapped_column(String(64), default="")
    window: Mapped[str] = mapped_column(String(32), default="24h")
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    operational_limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class BackupValidationRecord(Base):
    __tablename__ = "backup_validation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    backup_id: Mapped[str] = mapped_column(String(160), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    objects_checked: Mapped[int] = mapped_column(Integer, default=0)
    integrity_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class RecoveryValidationRecord(Base):
    __tablename__ = "recovery_validation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recovery_id: Mapped[str] = mapped_column(String(160), index=True)
    validation_type: Mapped[str] = mapped_column(String(80), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deterministic_rebuild_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    integrity_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    replay_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
