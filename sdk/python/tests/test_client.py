from __future__ import annotations

import httpx
import pytest

from bitcoin_bastion_sdk import AsyncBastionClient, BastionClient


def test_creates_sync_client_and_normalizes_base_url() -> None:
    client = BastionClient(base_url="http://example.com/", transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})))
    assert client._transport.config.base_url == "http://example.com"
    assert client._transport.config.api_prefix == "/api/v1"
    client.close()


@pytest.mark.asyncio
async def test_creates_async_client() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [], "error": None, "meta": {}})

    async with AsyncBastionClient(base_url="http://example.com", transport=httpx.MockTransport(handler)) as client:
        assert await client.signals.latest() == []


def test_applies_api_prefix_and_bearer_auth_without_exposing_token(captured_requests: list[httpx.Request]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    client = BastionClient(
        base_url="http://example.com",
        api_prefix="api/v1",
        api_key="super-secret-token",
        transport=httpx.MockTransport(handler),
    )
    assert client.trace.get_report(1) == {"ok": True}
    request = captured_requests[0]
    assert str(request.url) == "http://example.com/api/v1/trace/report/1"
    assert request.headers["authorization"] == "Bearer super-secret-token"
    client.close()
