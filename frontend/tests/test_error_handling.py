from __future__ import annotations

import asyncio
from typing import Any

import httpx

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import (
    BastionApiConnectionError,
    BastionApiNotFoundError,
    BastionApiRateLimitError,
    BastionApiUnavailableError,
    BastionApiValidationError,
)


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def client_for(status_code: int) -> BastionApiClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"detail": "internal detail"})

    config = AppConfig(api_base_url="http://backend.test")
    return BastionApiClient(config=config, transport=httpx.MockTransport(handler))


def test_400_maps_to_validation_error() -> None:
    try:
        run(client_for(400).get("/bad"))
    except BastionApiValidationError as exc:
        assert (
            exc.public_message
            == "The request could not be processed. Check the input and try again."
        )
    else:  # pragma: no cover
        raise AssertionError("expected validation error")


def test_404_maps_to_not_found_error() -> None:
    try:
        run(client_for(404).get("/missing"))
    except BastionApiNotFoundError as exc:
        assert exc.public_message == "The requested resource was not found."
    else:  # pragma: no cover
        raise AssertionError("expected not found")


def test_429_maps_to_rate_limit_error() -> None:
    try:
        run(client_for(429).get("/limited"))
    except BastionApiRateLimitError as exc:
        assert exc.public_message == "Too many requests. Wait briefly and try again."
    else:  # pragma: no cover
        raise AssertionError("expected rate limit")


def test_500_maps_to_unavailable_error() -> None:
    try:
        run(client_for(500).get("/boom"))
    except BastionApiUnavailableError as exc:
        assert exc.public_message == "Bitcoin Bastion is temporarily unavailable."
    else:  # pragma: no cover
        raise AssertionError("expected unavailable")


def test_connection_failure_maps_to_connection_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    config = AppConfig(api_base_url="http://backend.test")
    client = BastionApiClient(config=config, transport=httpx.MockTransport(handler))
    try:
        run(client.get("/offline"))
    except BastionApiConnectionError as exc:
        assert exc.public_message == "Unable to reach Bitcoin Bastion backend."
    else:  # pragma: no cover
        raise AssertionError("expected connection error")


def test_non_json_response_is_safe_unavailable_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    config = AppConfig(api_base_url="http://backend.test")
    client = BastionApiClient(config=config, transport=httpx.MockTransport(handler))
    try:
        run(client.get("/html"))
    except BastionApiUnavailableError as exc:
        assert exc.public_message == "Bitcoin Bastion is temporarily unavailable."
    else:  # pragma: no cover
        raise AssertionError("expected unavailable")
