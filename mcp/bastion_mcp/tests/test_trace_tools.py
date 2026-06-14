from __future__ import annotations

import pytest

from bastion_mcp.server import run_tool
from bastion_mcp.safety import FORBIDDEN_OUTPUT_PHRASES


class TraceClient:
    def __init__(self) -> None:
        self.called = False

    async def get_trace_lite(self, address: str) -> dict[str, object]:
        self.called = True
        return {"report_id": 7, "confidence": 0.7, "limitations": ["advisory-only"]}

    async def get_trace_report(self, report_id: int | str) -> dict[str, object]:
        return {"report_id": report_id, "limitations": ["not legal verification"]}

    async def get_public_trace_summary(self, report_id: int | str) -> dict[str, object]:
        return {"report_id": report_id, "limitations": ["public-safe"]}


@pytest.mark.asyncio
async def test_public_address_accepted_and_trace_flags_present() -> None:
    result = await run_tool(
        "analyze_address",
        {"address": "bc1qexamplepublicaddress000000000000000000000"},
        client=TraceClient(),  # type: ignore[arg-type]
    )
    assert result["safety_flags"]["advisory_only"] is True
    assert result["safety_flags"]["not_legal_verification"] is True
    assert result["safety_flags"]["not_bitcoin_consensus_proof"] is True
    output = str(result).casefold()
    for phrase in FORBIDDEN_OUTPUT_PHRASES:
        assert phrase not in output


@pytest.mark.asyncio
async def test_seed_private_key_rejected_before_api_call() -> None:
    client = TraceClient()
    result = await run_tool("analyze_address", {"address": "private key xprv"}, client=client)  # type: ignore[arg-type]
    assert result["error_code"] == "safety_violation"
    assert client.called is False
