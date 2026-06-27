"""Factory and health helpers for the analytics store."""

from __future__ import annotations

from app.core.config import Settings
from app.storage.analytics_store.base import AnalyticsStore
from app.storage.analytics_store.clickhouse import ClickHouseAnalyticsStore
from app.storage.analytics_store.disabled import DisabledAnalyticsStore
from app.storage.analytics_store.schemas import AnalyticsStoreHealth


def build_analytics_store(settings: Settings) -> AnalyticsStore:
    clickhouse = settings.storage.clickhouse
    if not clickhouse.enabled:
        return DisabledAnalyticsStore()
    return ClickHouseAnalyticsStore(clickhouse)


async def check_analytics_store(settings: Settings) -> AnalyticsStoreHealth:
    return await build_analytics_store(settings).healthcheck()
