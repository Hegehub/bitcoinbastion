from fastapi.testclient import TestClient

from app.api.v1.market_time_machine import get_market_time_machine_service
from app.main import app
from app.services.market_time_machine import MarketTimeMachineAnalyticsService
from app.storage.analytics_store.errors import AnalyticsStoreQueryError
from app.storage.analytics_store.schemas import AnalyticsStoreHealth, AnalyticsStoreStatusValue


class MissingProjectionStore:
    async def healthcheck(self) -> AnalyticsStoreHealth:
        return AnalyticsStoreHealth(enabled=True, status=AnalyticsStoreStatusValue.OK)

    async def execute(self, query: str, parameters: dict[str, object] | None = None):
        raise AnalyticsStoreQueryError("missing projection")


def override_service() -> MarketTimeMachineAnalyticsService:
    return MarketTimeMachineAnalyticsService(MissingProjectionStore())


def test_market_time_machine_route_degrades_on_projection_failure() -> None:
    app.dependency_overrides[get_market_time_machine_service] = override_service
    try:
        response = TestClient(app).get("/api/v1/market-time-machine/events?asset=BTC&limit=5")
    finally:
        app.dependency_overrides.pop(get_market_time_machine_service, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime_mode"] == "degraded"
    assert payload["source_store"] == "clickhouse"
    assert payload["items"] == []
    assert "projection_missing" in payload["warnings"]
    assert {"runtime_mode", "source_store", "generated_at", "warnings", "limitations"}.issubset(
        payload
    )
