from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.time_utils import utcnow


class StorageArtifactStatus(StrEnum):
    PENDING = "pending"
    AVAILABLE = "available"
    FAILED = "failed"
    DELETED = "deleted"
    QUARANTINED = "quarantined"


class StorageArtifact(Base):
    __tablename__ = "storage_artifacts"
    __table_args__ = (
        Index("ix_storage_artifacts_artifact_type", "artifact_type"),
        Index("ix_storage_artifacts_domain", "domain"),
        Index("ix_storage_artifacts_sha256_hash", "sha256_hash"),
        Index("ix_storage_artifacts_bucket_object_key", "bucket", "object_key"),
        Index("ix_storage_artifacts_created_at", "created_at"),
        Index("ix_storage_artifacts_retention_policy", "retention_policy"),
        Index("ix_storage_artifacts_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(80), nullable=False)
    artifact_subtype: Mapped[str | None] = mapped_column(String(80), nullable=True)
    domain: Mapped[str] = mapped_column(String(80), nullable=False)
    object_uri: Mapped[str] = mapped_column(String(2048), nullable=False)
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(2048), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    compression: Mapped[str | None] = mapped_column(String(32), nullable=True)
    encryption_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    signature_alg: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_key_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    retention_policy: Mapped[str] = mapped_column(String(64), nullable=False, default="standard")
    retention_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    legal_hold: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    redaction_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="not_required"
    )
    access_policy_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=dict
    )
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False, default=dict
    )
    created_by_hash: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StorageArtifactStatus.AVAILABLE.value
    )
