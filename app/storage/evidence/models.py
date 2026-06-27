"""Typed storage evidence models for backup/restore/readiness artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EvidenceStatus(StrEnum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIPPED = "skipped"
    NOT_CONFIGURED = "not_configured"


class StorageEvidenceType(StrEnum):
    POSTGRES_BACKUP = "postgres_backup"
    POSTGRES_RESTORE = "postgres_restore"
    REDIS_DEGRADED_MODE = "redis_degraded_mode"
    OBJECT_STORAGE_INTEGRITY = "object_storage_integrity"
    OUTBOX_REPLAY = "outbox_replay"
    STORAGE_HEALTH = "storage_health"


class EvidenceCheckItem(BaseModel):
    name: str
    status: EvidenceStatus
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Evidence check name must not be empty.")
        return value.strip()


class StorageEvidence(BaseModel):
    evidence_type: StorageEvidenceType
    status: EvidenceStatus
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str = "unknown"
    storage_profile: str = "unknown"
    repository_component: str = "storage_layer"
    checks: list[EvidenceCheckItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceWriteResult(BaseModel):
    path: str
    sha256: str
    size_bytes: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
