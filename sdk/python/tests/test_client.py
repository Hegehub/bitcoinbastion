from __future__ import annotations

import asyncio

import httpx
import pytest

from bitcoin_bastion_sdk import AsyncBastionClient, BastionClient
from bitcoin_bastion_sdk.auth import LegacyAuthDisabledError


def test_creates_sync_client_and_normalizes_base_url() -> None:
    client = BastionClient(
        base_url="http://example.com/",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
    )
    assert client._transport.config.base_url == "http://example.com"
    assert client._transport.config.api_prefix == "/api/v1"
    client.close()


def test_creates_async_client() -> None:
    async def run() -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": [], "error": None, "meta": {}})

        async with AsyncBastionClient(
            base_url="http://example.com", transport=httpx.MockTransport(handler)
        ) as client:
            assert await client.signals.latest() == []

    asyncio.run(run())


def test_legacy_bearer_api_key_auth_is_disabled(captured_requests: list[httpx.Request]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    with pytest.raises(LegacyAuthDisabledError):
        BastionClient(
            base_url="http://example.com",
            api_prefix="api/v1",
            api_key="super-secret-token",
            transport=httpx.MockTransport(handler),
        )

    assert captured_requests == []


def test_applies_api_prefix_without_bearer_auth(captured_requests: list[httpx.Request]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    client = BastionClient(
        base_url="http://example.com",
        api_prefix="api/v1",
        headers={"X-Bastion-Session": "session"},
        transport=httpx.MockTransport(handler),
    )
    assert client.trace.get_report(1) == {"ok": True}
    request = captured_requests[0]
    assert str(request.url) == "http://example.com/api/v1/trace/report/1"
    assert "authorization" not in request.headers
    assert request.headers["x-bastion-session"] == "session"
    client.close()
