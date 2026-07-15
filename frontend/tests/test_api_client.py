from __future__ import annotations

import asyncio
from typing import Any

import httpx

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import BastionApiTimeoutError


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def client_for(handler: httpx.MockTransport) -> BastionApiClient:
    config = AppConfig(api_base_url="http://backend.test/", request_timeout_seconds=2)
    return BastionApiClient(config=config, transport=handler)


def test_base_url_strips_trailing_slash_and_joins_paths() -> None:
    config = AppConfig(api_base_url="http://backend.test///")
    client = BastionApiClient(config=config)
    assert client.base_url == "http://backend.test"
    assert client.build_url("api/v1/public/status") == "http://backend.test/api/v1/public/status"
    assert client.build_url("/api/v1/public/status") == "http://backend.test/api/v1/public/status"


def test_get_unwraps_response_envelope_data() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    result = run(client_for(httpx.MockTransport(handler)).get("/wrapped"))
    assert result == {"ok": True}


def test_get_returns_raw_json_without_data() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok"})

    result = run(client_for(httpx.MockTransport(handler)).get("/raw"))
    assert result == {"status": "ok"}


def test_204_returns_none() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    result = run(client_for(httpx.MockTransport(handler)).delete("/resource"))
    assert result is None


def test_timeout_maps_to_timeout_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    try:
        run(client_for(httpx.MockTransport(handler)).get("/slow"))
    except BastionApiTimeoutError as exc:
        assert exc.public_message == "The request timed out. Try again shortly."
    else:  # pragma: no cover
        raise AssertionError("expected timeout")
