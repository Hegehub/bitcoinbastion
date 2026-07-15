from __future__ import annotations

import asyncio
from typing import Any

import httpx

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.trace_client import TraceApiClient


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def make_client(handler: Any) -> TraceApiClient:
    api_client = BastionApiClient(
        config=AppConfig(api_base_url="http://backend.test"),
        transport=httpx.MockTransport(handler),
    )
    return TraceApiClient(api_client)


def test_trace_report_client_unwraps_response_envelope() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"data": {"report_id": "r1", "summary": "limited evidence"}}
        )

    result = run(make_client(handler).get_trace_report("r1"))
    assert result.ok
    assert isinstance(result.data, dict)
    assert result.data["report_id"] == "r1"


def test_trace_report_client_handles_404() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "missing"})

    result = run(make_client(handler).get_trace_report("missing"))
    assert not result.ok
    assert result.status_code == 404
    assert result.error == "The requested resource was not found."


def test_trace_report_client_handles_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    result = run(make_client(handler).get_privacy_shield("r1"))
    assert not result.ok
    assert result.degraded
    assert result.error == "The request timed out. Try again shortly."


def test_trace_report_client_handles_partial_panel_failures() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/evidence"):
            return httpx.Response(500, json={"detail": "down"})
        return httpx.Response(200, json={"data": {"ok": True}})

    client = make_client(handler)
    report = run(client.get_trace_report("r1"))
    evidence = run(client.get_trace_evidence("r1"))
    assert report.ok
    assert not evidence.ok
    assert evidence.degraded
