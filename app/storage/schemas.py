"""Pydantic response schemas for storage operational status."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class StorageStatusValue(StrEnum):
    OK = "ok"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MISCONFIGURED = "misconfigured"
    NOT_CONFIGURED = "not_configured"
    NOT_IMPLEMENTED = "not_implemented"
    UNKNOWN = "unknown"


class StorageRole(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    FUTURE = "future"
    LOCAL_ONLY = "local_only"


class StorageStoreStatus(BaseModel):
    status: StorageStatusValue
    role: StorageRole
    purpose: str
    latency_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class StorageStatusSummary(BaseModel):
    required_ok: bool
    optional_degraded: bool
    critical_failures: int
    warnings: int


class StorageDegradedMode(BaseModel):
    active: bool
    reason: str | None = None
    impact: list[str] = Field(default_factory=list)


class StorageStatusResponse(BaseModel):
    status: StorageStatusValue
    profile: str
    summary: StorageStatusSummary
    stores: dict[str, StorageStoreStatus]
    degraded_mode: StorageDegradedMode
