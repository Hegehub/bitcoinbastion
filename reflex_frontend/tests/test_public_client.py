from __future__ import annotations

import asyncio

import httpx

from bastion_ui.config import Settings
from bastion_ui.services import public_client
from bastion_ui.services.api_client import BastionApiClient


def _recording_client(paths: list[str]) -> BastionApiClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.raw_path.decode())
        return httpx.Response(200, json={"data": {"path": request.url.path}})

    return BastionApiClient(
        Settings(api_base_url="http://backend.test"), transport=httpx.MockTransport(handler)
    )


def test_public_client_builds_expected_paths() -> None:
    paths: list[str] = []
    client = _recording_client(paths)
    asyncio.run(public_client.get_landing(client))
    asyncio.run(public_client.get_status(client))
    asyncio.run(public_client.get_roadmap(client))
    asyncio.run(public_client.get_stats(client))
    asyncio.run(public_client.get_features(client))
    asyncio.run(public_client.get_public_trace_summary("report 1", client))
    assert paths == [
        "/api/v1/public/landing",
        "/api/v1/public/status",
        "/api/v1/public/roadmap",
        "/api/v1/public/stats",
        "/api/v1/public/features",
        "/api/v1/public/trace/report%201/summary",
    ]
