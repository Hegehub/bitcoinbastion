import inspect

from app.storage.analytics_store.base import AnalyticsStore
from app.storage.analytics_store.schemas import (
    AnalyticsInsertResult,
    AnalyticsQueryResult,
    AnalyticsStoreHealth,
    AnalyticsStoreStatusValue,
)


def test_analytics_store_interface_is_minimal() -> None:
    members = {
        name for name, value in inspect.getmembers(AnalyticsStore) if inspect.isfunction(value)
    }
    assert {"healthcheck", "execute", "insert_events"}.issubset(members)


def test_analytics_store_schemas_do_not_require_secrets() -> None:
    health = AnalyticsStoreHealth(enabled=False, status=AnalyticsStoreStatusValue.DISABLED)
    query = AnalyticsQueryResult(rows=[{"count": 1}], row_count=1)
    insert = AnalyticsInsertResult(
        table="events", inserted_count=1, status=AnalyticsStoreStatusValue.OK
    )

    payload = f"{health.model_dump()} {query.model_dump()} {insert.model_dump()}".lower()
    assert "password" not in payload
    assert "secret" not in payload
