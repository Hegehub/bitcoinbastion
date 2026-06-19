from __future__ import annotations

import asyncio

import httpx

from bastion_ui.config import Settings
from bastion_ui.services.api_client import BastionApiClient
from bastion_ui.services.evidence_client import (
    get_proof_packet,
    get_provider_disagreement,
    get_trace_evidence,
)


def _client(handler: httpx.AsyncBaseTransport) -> BastionApiClient:
    return BastionApiClient(Settings(api_base_url="http://backend.test"), transport=handler)


def test_evidence_client_paths_and_envelope_unwrap() -> None:
    paths: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        return httpx.Response(200, json={"data": {"status": "limited evidence"}})

    client = _client(httpx.MockTransport(handler))
    evidence = asyncio.run(get_trace_evidence("rpt-1", client))
    packet = asyncio.run(get_proof_packet("rpt-1", client))
    disagreement = asyncio.run(get_provider_disagreement("rpt-1", client))
    assert evidence.ok is True
    assert packet.ok is True
    assert disagreement.ok is True
    assert paths == [
        "/api/v1/trace/report/rpt-1/evidence",
        "/api/v1/trace/report/rpt-1/proof-packet",
        "/api/v1/trace/report/rpt-1/provider-disagreement",
    ]


def test_evidence_client_404_is_safe_degraded_result() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "missing"}, request=request)

    result = asyncio.run(get_proof_packet("missing", _client(httpx.MockTransport(handler))))
    assert result.ok is False
    assert result.error == "The requested resource was not found."
    assert result.degraded is True
