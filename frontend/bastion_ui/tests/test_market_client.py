from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.market_client import MarketApiClient


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> MarketApiClient:
    transport = httpx.MockTransport(handler)
    config = AppConfig(api_base_url="http://backend.test")
    return MarketApiClient(BastionApiClient(config=config, transport=transport))


def test_market_dashboard_uses_web_time_machine_endpoint() -> None:
    async def run() -> None:
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.url.path)
            return httpx.Response(200, json={"data": {"status": "available"}})

        result = await _client(handler).get_market_dashboard()
        assert result.ok is True
        assert result.data == {"status": "available"}
        assert seen == ["/web/market-time-machine"]

    asyncio.run(run())


def test_market_client_returns_unavailable_state_on_404() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"detail": "missing"})

        result = await _client(handler).get_latest_intelligence_signals()
        assert result.ok is False
        assert result.degraded is True
        assert result.status_code == 404
        assert isinstance(result.data, dict)
        assert result.data["available"] is False

    asyncio.run(run())


def test_market_client_handles_timeout_without_fake_success() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        result = await _client(handler).get_provider_health()
        assert result.ok is False
        assert result.degraded is True
        assert "timed out" in (result.error or "").lower()

    asyncio.run(run())
