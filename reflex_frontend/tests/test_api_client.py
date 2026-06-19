from __future__ import annotations

import asyncio
from typing import Any

import httpx

from bastion_ui.config import Settings
from bastion_ui.services.api_client import BastionApiClient


def _client(handler: httpx.AsyncBaseTransport) -> BastionApiClient:
    return BastionApiClient(
        Settings(api_base_url="http://backend.test/", request_timeout_seconds=2),
        transport=handler,
    )


def test_base_url_strips_trailing_slash() -> None:
    settings = Settings(api_base_url="http://backend.test///")
    assert settings.api_base_url == "http://backend.test"


def test_client_joins_paths_safely() -> None:
    client = BastionApiClient(Settings(api_base_url="http://backend.test/"))
    assert client.build_url("/api/v1/public/status") == "http://backend.test/api/v1/public/status"
    assert client.build_url("api/v1/public/status") == "http://backend.test/api/v1/public/status"


def test_get_unwraps_data_envelope() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"ok": True}, "error": None, "meta": {}})

    result = asyncio.run(_client(httpx.MockTransport(handler)).get("/status"))
    assert result == {"ok": True}


def test_get_returns_raw_json_without_data_key() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok"})

    result = asyncio.run(_client(httpx.MockTransport(handler)).get("/status"))
    assert result == {"status": "ok"}


def test_204_returns_none() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    result = asyncio.run(_client(httpx.MockTransport(handler)).delete("/resource"))
    assert result is None


def test_post_patch_delete_methods_use_expected_http_verbs() -> None:
    seen: list[tuple[str, Any]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"data": {"method": request.method}})

    client = _client(httpx.MockTransport(handler))
    assert asyncio.run(client.post("/resource", json={"safe": True})) == {"method": "POST"}
    assert asyncio.run(client.patch("/resource", json={"safe": True})) == {"method": "PATCH"}
    assert asyncio.run(client.delete("/resource")) == {"method": "DELETE"}
    assert seen == [("POST", "/resource"), ("PATCH", "/resource"), ("DELETE", "/resource")]
