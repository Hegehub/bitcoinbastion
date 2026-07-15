from __future__ import annotations

import asyncio
from typing import Any

from bastion_ui.services.public_client import PublicApiClient


class RecordingClient:
    def __init__(self) -> None:
        self.paths: list[str] = []

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, str]:
        self.paths.append(path)
        return {"path": path}


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_public_client_builds_expected_paths() -> None:
    recorder = RecordingClient()
    client = PublicApiClient(api_client=recorder)  # type: ignore[arg-type]
    run(client.get_landing())
    run(client.get_status())
    run(client.get_roadmap())
    run(client.get_stats())
    run(client.get_features())
    run(client.get_public_trace_summary("123"))
    assert recorder.paths == [
        "/api/v1/public/landing",
        "/api/v1/public/status",
        "/api/v1/public/roadmap",
        "/api/v1/public/stats",
        "/api/v1/public/features",
        "/api/v1/public/trace/123/summary",
    ]
