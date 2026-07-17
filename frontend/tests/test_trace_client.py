from __future__ import annotations

import asyncio
from typing import Any

from bastion_ui.services.trace_client import TraceApiClient


class RecordingClient:
    def __init__(self) -> None:
        self.paths: list[str] = []

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, str]:
        self.paths.append(path)
        return {"path": path}


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_trace_client_builds_expected_paths() -> None:
    recorder = RecordingClient()
    client = TraceApiClient(api_client=recorder)  # type: ignore[arg-type]
    run(client.get_trace_lite("bc1qexample"))
    run(client.get_trace_address("bc1qexample"))
    run(client.get_trace_report("42"))
    run(client.get_trace_evidence("42"))
    run(client.get_origin_passport("42"))
    run(client.get_privacy_shield("42"))
    run(client.get_source_summary("42"))
    run(client.get_provider_disagreement("42"))
    run(client.get_utxo_hygiene("42"))
    run(client.get_dust_radar("42"))
    run(client.get_counterparty_lens("42"))
    run(client.get_policy_facts("42"))
    assert recorder.paths == [
        "/api/v1/trace/lite/bc1qexample",
        "/api/v1/trace/address/bc1qexample",
        "/api/v1/trace/report/42",
        "/api/v1/trace/report/42/evidence",
        "/api/v1/trace/report/42/origin-passport",
        "/api/v1/trace/report/42/privacy-shield",
        "/api/v1/trace/report/42/source-summary",
        "/api/v1/trace/report/42/provider-disagreement",
        "/api/v1/trace/report/42/utxo-hygiene",
        "/api/v1/trace/report/42/dust-radar",
        "/api/v1/trace/report/42/counterparty-lens",
        "/api/v1/trace/report/42/policy-facts",
    ]
