"""Safe schemas for analytics-store health, queries, and inserts."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AnalyticsStoreStatusValue(StrEnum):
    OK = "ok"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MISCONFIGURED = "misconfigured"
    UNKNOWN = "unknown"


class AnalyticsStoreHealth(BaseModel):
    enabled: bool
    status: AnalyticsStoreStatusValue
    database: str | None = None
    latency_ms: float | None = None
    error: str | None = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    details: dict[str, Any] = Field(default_factory=dict)


class AnalyticsQueryResult(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    elapsed_ms: float | None = None


class AnalyticsInsertResult(BaseModel):
    table: str
    inserted_count: int
    elapsed_ms: float | None = None
    status: AnalyticsStoreStatusValue


class AnalyticsStoreStatus(BaseModel):
    enabled: bool
    profile: str
    health: AnalyticsStoreHealth
