import asyncio
from datetime import UTC, datetime, timedelta

from app.services.market_time_machine.analytics_service import MarketTimeMachineAnalyticsService
from app.services.market_time_machine.queries import market_event_timeline_query
from app.storage.analytics_store.schemas import AnalyticsStoreHealth


class NotUsedStore:
    async def healthcheck(self) -> AnalyticsStoreHealth:  # pragma: no cover
        raise AssertionError("excessive query window should not hit ClickHouse")

    async def execute(
        self, query: str, parameters: dict[str, object] | None = None
    ):  # pragma: no cover
        raise AssertionError("excessive query window should not execute")


def test_excessive_query_window_degrades_without_clickhouse_call() -> None:
    service = MarketTimeMachineAnalyticsService(NotUsedStore())
    now = datetime.now(UTC)

    response = asyncio.run(
        service.get_market_event_timeline(from_ts=now - timedelta(days=4000), to_ts=now)
    )

    assert response.runtime_mode == "degraded"
    assert response.source_store == "none"
    assert "query_window_too_large" in response.warnings


def test_query_builder_uses_parameters_not_raw_interpolation() -> None:
    query = market_event_timeline_query(
        from_ts=datetime.now(UTC) - timedelta(days=1),
        to_ts=datetime.now(UTC),
        asset="BTC'; DROP TABLE market_time_machine_events; --",
        limit=10,
        event_type="market.time_machine.event'; DROP TABLE x; --",
    )

    assert "DROP TABLE" not in query.query
    assert "{asset:String}" in query.query
    assert "{event_type:String}" in query.query
    assert "DROP TABLE" in query.params["asset"]
