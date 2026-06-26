from __future__ import annotations

import asyncio
from typing import Any

import httpx

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import BastionApiUnavailableError
from bastion_ui.services.trace_client import TraceApiClient


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_trace_lite_client_uses_lite_endpoint_and_unwraps_data() -> None:
    seen_paths: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "data": {
                    "address": "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080",
                    "report_id": "42",
                    "risk_band": "manual review recommended",
                    "confidence": 0.64,
                    "provider_count": 2,
                    "source_count": 3,
                    "summary": "Source-dependent advisory context.",
                    "degraded": False,
                },
                "error": None,
            },
        )

    client = BastionApiClient(
        config=AppConfig(api_base_url="http://backend.test"),
        transport=httpx.MockTransport(handler),
    )
    result = run(
        TraceApiClient(client).get_trace_lite("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080")
    )
    assert seen_paths == ["/api/v1/trace/lite/bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"]
    assert result.report_id == "42"
    assert result.risk_band == "manual review recommended"
    assert result.provider_count == 2


def test_trace_api_error_maps_to_safe_message() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "internal"})

    client = BastionApiClient(
        config=AppConfig(api_base_url="http://backend.test"),
        transport=httpx.MockTransport(handler),
    )
    try:
        run(TraceApiClient(client).get_trace_lite("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"))
    except BastionApiUnavailableError as exc:
        assert exc.public_message == "Bitcoin Bastion is temporarily unavailable."
    else:  # pragma: no cover
        raise AssertionError("expected safe API error")
