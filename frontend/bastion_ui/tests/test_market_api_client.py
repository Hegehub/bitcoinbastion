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


def test_market_time_machine_client_unwraps_response_envelope() -> None:
    async def run() -> None:
        seen: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.url.path)
            return httpx.Response(200, json={"data": {"timeline_items": []}})

        result = await _client(handler).get_time_machine()
        assert result.ok is True
        assert result.data == {"timeline_items": []}
        assert seen == ["/web/market-time-machine"]

    asyncio.run(run())


def test_market_client_preserves_degraded_and_stale_flags() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": {"degraded": True, "stale": True}})

        result = await _client(handler).get_timeline()
        assert result.ok is True
        assert result.degraded is True

    asyncio.run(run())


def test_market_client_handles_404_without_fake_success() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"detail": "missing"})

        result = await _client(handler).get_market_sources()
        assert result.ok is False
        assert result.status_code == 404
        assert result.degraded is True
        assert isinstance(result.data, dict)
        assert result.data["available"] is False

    asyncio.run(run())


def test_market_client_handles_429_without_fake_success() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"detail": "limited"})

        result = await _client(handler).get_market_signals()
        assert result.ok is False
        assert result.status_code == 429
        assert result.degraded is True

    asyncio.run(run())


def test_market_client_handles_timeout_without_fake_success() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        result = await _client(handler).get_market_evidence()
        assert result.ok is False
        assert result.degraded is True
        assert "unavailable" in (result.error or "").lower()

    asyncio.run(run())
