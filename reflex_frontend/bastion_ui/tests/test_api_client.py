from __future__ import annotations

from typing import Any

import httpx
import pytest

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.errors import (
    CONNECTION_PUBLIC_MESSAGE,
    RATE_LIMIT_PUBLIC_MESSAGE,
    TIMEOUT_PUBLIC_MESSAGE,
    VALIDATION_PUBLIC_MESSAGE,
    BastionApiConnectionError,
    BastionApiError,
    BastionApiNotFoundError,
    BastionApiRateLimitError,
    BastionApiTimeoutError,
    BastionApiValidationError,
)
from bastion_ui.services.public_client import PublicApiClient
from bastion_ui.services.trace_client import TRACE_LITE_ENDPOINT, TraceApiClient


class RecordingApiClient:
    def __init__(self) -> None:
        self.paths: list[str] = []

    async def get(self, path: str) -> dict[str, Any]:
        self.paths.append(path)
        return {"ok": True}


def _client_for_response(status_code: int, json_body: Any) -> BastionApiClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=json_body, request=request)

    return BastionApiClient(
        AppConfig(api_base_url="https://api.example.test", request_timeout_seconds=1.5),
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_client_uses_configured_base_url_and_timeout() -> None:
    captured: dict[str, Any] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"data": {"status": "ok"}}, request=request)

    client = BastionApiClient(
        AppConfig(api_base_url="https://api.example.test///", request_timeout_seconds=2.25),
        transport=httpx.MockTransport(handler),
    )
    assert client.config.request_timeout_seconds == 2.25
    assert await client.get("/api/v1/public/status") == {"status": "ok"}
    assert captured["url"] == "https://api.example.test/api/v1/public/status"


@pytest.mark.asyncio
async def test_response_envelope_unwraps_data_and_raw_json_falls_back() -> None:
    envelope_client = _client_for_response(200, {"data": {"status": "ok"}})
    raw_client = _client_for_response(200, {"status": "raw"})
    assert await envelope_client.get("/status") == {"status": "ok"}
    assert await raw_client.get("/status") == {"status": "raw"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "expected_error", "public_message"),
    [
        (400, BastionApiValidationError, VALIDATION_PUBLIC_MESSAGE),
        (404, BastionApiNotFoundError, "The requested resource was not found."),
        (422, BastionApiValidationError, VALIDATION_PUBLIC_MESSAGE),
        (429, BastionApiRateLimitError, RATE_LIMIT_PUBLIC_MESSAGE),
    ],
)
async def test_http_errors_are_normalized(
    status_code: int, expected_error: type[BastionApiError], public_message: str
) -> None:
    client = _client_for_response(status_code, {"detail": "token=supersecret"})
    with pytest.raises(expected_error) as exc_info:
        await client.get("/failing")
    assert exc_info.value.status_code == status_code
    assert exc_info.value.public_message == public_message
    assert "supersecret" not in exc_info.value.public_message


@pytest.mark.asyncio
async def test_timeout_and_network_errors_are_normalized() -> None:
    async def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("token=supersecret", request=request)

    async def network_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("token=supersecret", request=request)

    with pytest.raises(BastionApiTimeoutError) as timeout_exc:
        await BastionApiClient(transport=httpx.MockTransport(timeout_handler)).get("/timeout")
    assert timeout_exc.value.public_message == TIMEOUT_PUBLIC_MESSAGE
    assert "supersecret" not in timeout_exc.value.public_message

    with pytest.raises(BastionApiConnectionError) as network_exc:
        await BastionApiClient(transport=httpx.MockTransport(network_handler)).get("/network")
    assert network_exc.value.public_message == CONNECTION_PUBLIC_MESSAGE
    assert "supersecret" not in network_exc.value.public_message


@pytest.mark.asyncio
async def test_public_client_targets_expected_backend_endpoints() -> None:
    recorder = RecordingApiClient()
    public = PublicApiClient(api_client=recorder)  # type: ignore[arg-type]
    await public.get_status()
    await public.get_roadmap()
    await public.get_public_trace_summary("report-123")
    assert recorder.paths == [
        "/api/v1/public/status",
        "/api/v1/public/roadmap",
        "/api/v1/public/trace/report-123/summary",
    ]


@pytest.mark.asyncio
async def test_trace_client_targets_expected_backend_endpoints() -> None:
    recorder = RecordingApiClient()
    trace = TraceApiClient(api_client=recorder)  # type: ignore[arg-type]
    await trace.get_public_trace_summary("report-123")
    await trace.get_trace_report("report-123")
    await trace.get_trace_evidence("report-123")
    await trace.get_trace_lite("bc1qexampleaddress000000000000000000000000000")
    assert recorder.paths == [
        "/api/v1/public/trace/report-123/summary",
        "/api/v1/trace/report/report-123",
        "/api/v1/trace/report/report-123/evidence",
        TRACE_LITE_ENDPOINT.format(address="bc1qexampleaddress000000000000000000000000000"),
    ]
