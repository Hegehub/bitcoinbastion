"""Schemas for storage projection workers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClickHouseProjectionSummary(BaseModel):
    processed: int = 0
    inserted: int = 0
    failed_retryable: int = 0
    failed_terminal: int = 0
    skipped: int = 0
    dry_run: bool = False
    clickhouse_enabled: bool = True
    reason: str | None = None
    errors: list[str] = Field(default_factory=list)
