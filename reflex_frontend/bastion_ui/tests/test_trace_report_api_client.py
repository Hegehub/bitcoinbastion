from __future__ import annotations

import asyncio

import httpx

from bastion_ui.config import Settings
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.trace_client import (
    get_proof_packet,
    get_public_trace_summary,
    get_trace_report_result,
)


def _client(handler: httpx.AsyncBaseTransport) -> BastionApiClient:
    return BastionApiClient(Settings(api_base_url="http://backend.test"), transport=handler)


def test_trace_report_client_unwraps_response_envelope() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/trace/report/rpt-1"
        return httpx.Response(200, json={"data": {"report_id": "rpt-1", "degraded": True}})

    result = asyncio.run(get_trace_report_result("rpt-1", _client(httpx.MockTransport(handler))))
    assert result.ok is True
    assert result.data == {"report_id": "rpt-1", "degraded": True}
    assert result.degraded is True


def test_trace_report_client_handles_404_as_safe_result() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "missing"}, request=request)

    result = asyncio.run(get_public_trace_summary("missing", _client(httpx.MockTransport(handler))))
    assert result.ok is False
    assert result.status_code == 404
    assert result.error == "The requested resource was not found."
    assert result.degraded is True


def test_trace_report_client_handles_timeout_as_safe_result() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout", request=request)

    result = asyncio.run(get_proof_packet("rpt-1", _client(httpx.MockTransport(handler))))
    assert result.ok is False
    assert result.error == "The request timed out. Try again shortly."
    assert result.degraded is True
