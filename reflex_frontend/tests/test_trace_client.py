from __future__ import annotations

import asyncio

import httpx

from bastion_ui.config import Settings
from bastion_ui.services import trace_client
from bastion_ui.services.api_client import BastionApiClient


def _recording_client(paths: list[str]) -> BastionApiClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.raw_path.decode())
        return httpx.Response(200, json={"data": {"path": request.url.path}})

    return BastionApiClient(
        Settings(api_base_url="http://backend.test"), transport=httpx.MockTransport(handler)
    )


def test_trace_client_builds_expected_paths() -> None:
    paths: list[str] = []
    client = _recording_client(paths)
    asyncio.run(trace_client.get_trace_lite("bc1qexample", client))
    asyncio.run(trace_client.get_trace_address("bc1qexample", client))
    asyncio.run(trace_client.get_trace_report("rpt-1", client))
    asyncio.run(trace_client.get_trace_evidence("rpt-1", client))
    asyncio.run(trace_client.get_origin_passport("rpt-1", client))
    asyncio.run(trace_client.get_privacy_shield("rpt-1", client))
    asyncio.run(trace_client.get_source_summary("rpt-1", client))
    asyncio.run(trace_client.get_provider_disagreement("rpt-1", client))
    asyncio.run(trace_client.get_utxo_hygiene("rpt-1", client))
    asyncio.run(trace_client.get_dust_radar("rpt-1", client))
    asyncio.run(trace_client.get_counterparty_lens("rpt-1", client))
    asyncio.run(trace_client.get_policy_facts("rpt-1", client))
    assert paths == [
        "/api/v1/trace/lite/bc1qexample",
        "/api/v1/trace/address/bc1qexample",
        "/api/v1/trace/report/rpt-1",
        "/api/v1/trace/report/rpt-1/evidence",
        "/api/v1/trace/report/rpt-1/origin-passport",
        "/api/v1/trace/report/rpt-1/privacy-shield",
        "/api/v1/trace/report/rpt-1/source-summary",
        "/api/v1/trace/report/rpt-1/provider-disagreement",
        "/api/v1/trace/report/rpt-1/utxo-hygiene",
        "/api/v1/trace/report/rpt-1/dust-radar",
        "/api/v1/trace/report/rpt-1/counterparty-lens",
        "/api/v1/trace/report/rpt-1/policy-facts",
    ]
