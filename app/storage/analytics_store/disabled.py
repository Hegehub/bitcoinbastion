"""Disabled analytics-store implementation used when ClickHouse is off."""

from __future__ import annotations

from app.storage.analytics_store.errors import AnalyticsStoreDisabledError
from app.storage.analytics_store.schemas import (
    AnalyticsInsertResult,
    AnalyticsQueryResult,
    AnalyticsStoreHealth,
    AnalyticsStoreStatusValue,
)


class DisabledAnalyticsStore:
    async def healthcheck(self) -> AnalyticsStoreHealth:
        return AnalyticsStoreHealth(
            enabled=False,
            status=AnalyticsStoreStatusValue.DISABLED,
            database=None,
            latency_ms=None,
            error=None,
            details={"reason": "CLICKHOUSE_ENABLED=false"},
        )

    async def execute(
        self, query: str, parameters: dict[str, object] | None = None
    ) -> AnalyticsQueryResult:
        raise AnalyticsStoreDisabledError("ClickHouse analytics store is disabled.")

    async def insert_events(
        self, table: str, events: list[dict[str, object]]
    ) -> AnalyticsInsertResult:
        raise AnalyticsStoreDisabledError("ClickHouse analytics store is disabled.")
