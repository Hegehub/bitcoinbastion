import asyncio
from datetime import UTC, datetime, timedelta

from app.services.market_time_machine.analytics_service import MarketTimeMachineAnalyticsService
from app.storage.analytics_store.schemas import (
    AnalyticsQueryResult,
    AnalyticsStoreHealth,
    AnalyticsStoreStatusValue,
)


class LiveStore:
    def __init__(self) -> None:
        self.last_query = ""
        self.last_params: dict[str, object] = {}

    async def healthcheck(self) -> AnalyticsStoreHealth:
        return AnalyticsStoreHealth(
            enabled=True, status=AnalyticsStoreStatusValue.OK, database="bb"
        )

    async def execute(self, query: str, parameters: dict[str, object] | None = None):
        self.last_query = query
        self.last_params = parameters or {}
        return AnalyticsQueryResult(
            rows=[
                {
                    "event_id": "evt-1",
                    "event_type": "market.time_machine.event",
                    "occurred_at": datetime.now(UTC),
                    "asset": "BTC",
                    "timeframe": "1h",
                    "regime": "risk_on",
                    "confidence_band": "high",
                    "signal_family": "macro",
                    "payload_json": "{}",
                }
            ],
            row_count=1,
        )


def test_market_event_timeline_returns_live_items_and_metadata() -> None:
    store = LiveStore()
    service = MarketTimeMachineAnalyticsService(store)
    now = datetime.now(UTC)

    response = asyncio.run(
        service.get_market_event_timeline(
            from_ts=now - timedelta(days=1), to_ts=now, asset="BTC", limit=10
        )
    )

    assert response.runtime_mode == "live"
    assert response.source_store == "clickhouse"
    assert response.limit == 10
    assert response.items[0]["event_id"] == "evt-1"
    assert store.last_params["asset"] == "BTC"
