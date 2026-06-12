from __future__ import annotations

import httpx
import pytest

from bitcoin_bastion_sdk import BastionClient
from bitcoin_bastion_sdk.errors import BastionSafetyError


def make_client(captured: list[str]) -> BastionClient:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.url.path)
        return httpx.Response(200, json={"data": {"path": request.url.path}, "error": None, "meta": {}})

    return BastionClient(base_url="http://example.com", transport=httpx.MockTransport(handler))


def test_trace_lite_calls_correct_endpoint() -> None:
    captured: list[str] = []
    client = make_client(captured)
    client.trace.lite("bc1qexamplepublicaddress000000000000000000000")
    assert captured == ["/api/v1/trace/lite/bc1qexamplepublicaddress000000000000000000000"]


def test_trace_analyze_address_calls_correct_endpoint() -> None:
    captured: list[str] = []
    client = make_client(captured)
    client.trace.analyze_address("bc1qexamplepublicaddress000000000000000000000")
    assert captured == ["/api/v1/trace/address/bc1qexamplepublicaddress000000000000000000000"]


def test_trace_get_report_calls_correct_endpoint() -> None:
    captured: list[str] = []
    make_client(captured).trace.get_report(123)
    assert captured == ["/api/v1/trace/report/123"]


def test_trace_get_public_summary_calls_correct_endpoint() -> None:
    captured: list[str] = []
    make_client(captured).trace.get_public_summary(123)
    assert captured == ["/api/v1/public/trace/123/summary"]


def test_trace_batch_rejects_sensitive_material() -> None:
    with pytest.raises(BastionSafetyError):
        make_client([]).trace.batch(["seed phrase should not be accepted"])
