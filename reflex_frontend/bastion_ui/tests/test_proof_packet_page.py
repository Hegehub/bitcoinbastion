from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx

from bastion_ui.config import AppConfig
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.evidence_client import EvidenceApiClient


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_proof_packet_route_exists() -> None:
    app_source = Path(__file__).resolve().parents[1] / "app.py"
    text = app_source.read_text()
    assert 'route="/trace/[report_id]/proof-packet"' in text


def test_missing_proof_packet_state_is_safe() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "missing"})

    client = EvidenceApiClient(
        BastionApiClient(
            config=AppConfig(api_base_url="http://backend.test"),
            transport=httpx.MockTransport(handler),
        )
    )
    result = run(client.get_proof_packet("report-1"))
    assert not result.ok
    assert result.status_code == 404
    assert result.degraded
    assert result.error == "The requested resource was not found."


def test_evidence_client_unwraps_trace_evidence() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"evidence": [{"title": "source note"}]}})

    client = EvidenceApiClient(
        BastionApiClient(
            config=AppConfig(api_base_url="http://backend.test"),
            transport=httpx.MockTransport(handler),
        )
    )
    result = run(client.get_trace_evidence("report-1"))
    assert result.ok
    assert isinstance(result.data, dict)
    assert result.data["evidence"][0]["title"] == "source note"
