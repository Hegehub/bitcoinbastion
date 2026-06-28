import asyncio

from app.services.market_time_machine.analytics_service import MarketTimeMachineAnalyticsService
from app.storage.analytics_store.errors import AnalyticsStoreQueryError
from app.storage.analytics_store.schemas import AnalyticsStoreHealth, AnalyticsStoreStatusValue


class DisabledStore:
    async def healthcheck(self) -> AnalyticsStoreHealth:
        return AnalyticsStoreHealth(enabled=False, status=AnalyticsStoreStatusValue.DISABLED)

    async def execute(
        self, query: str, parameters: dict[str, object] | None = None
    ):  # pragma: no cover
        raise AssertionError("disabled store must not execute")


class UnavailableStore:
    async def healthcheck(self) -> AnalyticsStoreHealth:
        return AnalyticsStoreHealth(
            enabled=True, status=AnalyticsStoreStatusValue.UNAVAILABLE, error="NetworkError"
        )

    async def execute(
        self, query: str, parameters: dict[str, object] | None = None
    ):  # pragma: no cover
        raise AssertionError("unavailable store must not execute")


class MissingProjectionStore:
    async def healthcheck(self) -> AnalyticsStoreHealth:
        return AnalyticsStoreHealth(enabled=True, status=AnalyticsStoreStatusValue.OK)

    async def execute(self, query: str, parameters: dict[str, object] | None = None):
        raise AnalyticsStoreQueryError("missing projection")


def test_clickhouse_disabled_returns_disabled_response() -> None:
    response = asyncio.run(
        MarketTimeMachineAnalyticsService(DisabledStore()).get_news_impact_history()
    )

    assert response.runtime_mode == "disabled"
    assert response.source_store == "none"
    assert response.items == []
    assert "clickhouse_disabled" in response.warnings


def test_clickhouse_unavailable_returns_unavailable_response() -> None:
    response = asyncio.run(
        MarketTimeMachineAnalyticsService(UnavailableStore()).get_candle_attribution_history()
    )

    assert response.runtime_mode == "unavailable"
    assert response.source_store == "none"
    assert "clickhouse_unavailable" in response.warnings


def test_missing_projection_returns_degraded_response() -> None:
    response = asyncio.run(
        MarketTimeMachineAnalyticsService(
            MissingProjectionStore()
        ).get_historical_reaction_windows()
    )

    assert response.runtime_mode == "degraded"
    assert response.source_store == "clickhouse"
    assert "projection_missing" in response.warnings
