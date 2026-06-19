from __future__ import annotations

import asyncio

import httpx
import pytest

from bastion_ui.config import Settings
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import BastionApiUnavailableError
from bastion_ui.services.trace_client import get_trace_lite


def _client(handler: httpx.AsyncBaseTransport) -> BastionApiClient:
    return BastionApiClient(
        Settings(api_base_url="http://backend.test"),
        transport=handler,
    )


def test_trace_lite_client_unwraps_envelope_and_maps_dto() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/trace/lite/bc1qexample"
        return httpx.Response(
            200,
            json={
                "data": {
                    "address": "bc1qexample",
                    "report_id": "123",
                    "trace_band": "limited evidence",
                    "confidence": 0.42,
                    "summary": "Manual review recommended.",
                    "provider_count": 2,
                    "source_count": 4,
                    "degraded": True,
                    "limitations": ["Source coverage varies."],
                }
            },
        )

    result = asyncio.run(get_trace_lite("bc1qexample", _client(httpx.MockTransport(handler))))
    assert result.address == "bc1qexample"
    assert result.report_id == "123"
    assert result.risk_band == "limited evidence"
    assert result.degraded is True
    assert result.limitations == ["Source coverage varies."]


def test_trace_lite_client_maps_api_error_to_safe_message() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "backend unavailable"}, request=request)

    with pytest.raises(BastionApiUnavailableError) as exc_info:
        asyncio.run(get_trace_lite("bc1qexample", _client(httpx.MockTransport(handler))))
    assert exc_info.value.public_message == "Bitcoin Bastion is temporarily unavailable."
