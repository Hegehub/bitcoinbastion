import asyncio

import pytest

from app.storage.analytics_store.disabled import DisabledAnalyticsStore
from app.storage.analytics_store.errors import AnalyticsStoreDisabledError


def test_disabled_clickhouse_store_health_is_disabled() -> None:
    health = asyncio.run(DisabledAnalyticsStore().healthcheck())

    assert health.enabled is False
    assert health.status == "disabled"
    assert health.database is None
    assert health.error is None


def test_disabled_clickhouse_store_rejects_execute_and_insert() -> None:
    store = DisabledAnalyticsStore()

    with pytest.raises(AnalyticsStoreDisabledError, match="disabled"):
        asyncio.run(store.execute("SELECT 1"))

    with pytest.raises(AnalyticsStoreDisabledError, match="disabled"):
        asyncio.run(store.insert_events("events", [{"safe": True}]))
