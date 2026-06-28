"""Minimal analytics-store interface for rebuildable projection stores."""

from __future__ import annotations

from typing import Protocol

from app.storage.analytics_store.schemas import (
    AnalyticsInsertResult,
    AnalyticsQueryResult,
    AnalyticsStoreHealth,
)


class AnalyticsStore(Protocol):
    async def healthcheck(self) -> AnalyticsStoreHealth:
        """Return sanitized analytics-store health."""

    async def execute(
        self, query: str, parameters: dict[str, object] | None = None
    ) -> AnalyticsQueryResult:
        """Execute a bounded analytics query."""

    async def insert_events(
        self, table: str, events: list[dict[str, object]]
    ) -> AnalyticsInsertResult:
        """Insert rebuildable projection events into an analytics table."""
