from __future__ import annotations

import asyncio

import httpx
import pytest

from bastion_ui.config import Settings
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import (
    CONNECTION_PUBLIC_MESSAGE,
    RATE_LIMIT_PUBLIC_MESSAGE,
    TIMEOUT_PUBLIC_MESSAGE,
    UNAVAILABLE_PUBLIC_MESSAGE,
    VALIDATION_PUBLIC_MESSAGE,
    BastionApiConnectionError,
    BastionApiNotFoundError,
    BastionApiRateLimitError,
    BastionApiTimeoutError,
    BastionApiUnavailableError,
    BastionApiValidationError,
)


def _client(handler: httpx.AsyncBaseTransport) -> BastionApiClient:
    return BastionApiClient(
        Settings(api_base_url="http://backend.test", request_timeout_seconds=1),
        transport=handler,
    )


def _raises_status(status: int) -> Exception:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"detail": "safe detail"}, request=request)

    with pytest.raises(Exception) as exc_info:
        asyncio.run(_client(httpx.MockTransport(handler)).get("/status"))
    return exc_info.value


def test_400_maps_to_validation_error() -> None:
    error = _raises_status(400)
    assert isinstance(error, BastionApiValidationError)
    assert error.public_message == VALIDATION_PUBLIC_MESSAGE


def test_404_maps_to_not_found_error() -> None:
    error = _raises_status(404)
    assert isinstance(error, BastionApiNotFoundError)


def test_429_maps_to_rate_limit_error() -> None:
    error = _raises_status(429)
    assert isinstance(error, BastionApiRateLimitError)
    assert error.public_message == RATE_LIMIT_PUBLIC_MESSAGE


def test_500_maps_to_unavailable_error() -> None:
    error = _raises_status(500)
    assert isinstance(error, BastionApiUnavailableError)
    assert error.public_message == UNAVAILABLE_PUBLIC_MESSAGE


def test_timeout_maps_to_timeout_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(BastionApiTimeoutError) as exc_info:
        asyncio.run(_client(httpx.MockTransport(handler)).get("/status"))
    assert exc_info.value.public_message == TIMEOUT_PUBLIC_MESSAGE


def test_connection_failure_maps_to_connection_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    with pytest.raises(BastionApiConnectionError) as exc_info:
        asyncio.run(_client(httpx.MockTransport(handler)).get("/status"))
    assert exc_info.value.public_message == CONNECTION_PUBLIC_MESSAGE


def test_error_envelope_raises_safe_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": None, "error": {"message": "limited evidence"}})

    with pytest.raises(Exception) as exc_info:
        asyncio.run(_client(httpx.MockTransport(handler)).get("/status"))
    assert "limited evidence" in str(exc_info.value)
