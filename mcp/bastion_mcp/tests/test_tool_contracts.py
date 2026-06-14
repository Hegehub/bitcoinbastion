from __future__ import annotations

import pytest

from bastion_mcp.server import TOOL_REGISTRY, run_tool


class FakeClient:
    async def get_latest_signals(self, *, limit: int = 10, signal_type: str | None = None) -> list[dict[str, object]]:
        return [{"id": 1, "signal_type": signal_type or "context", "limitations": ["not financial advice"]}]

    async def get_signal(self, signal_id: int | str) -> dict[str, object]:
        return {"id": signal_id, "limitations": ["operator review required"]}

    async def get_signal_evidence(self, signal_id: int | str) -> dict[str, object]:
        return {"signal_id": signal_id, "evidence_refs": ["ev1"], "limitations": ["partial evidence"]}

    async def get_trace_lite(self, address: str) -> dict[str, object]:
        return {"report_id": 1, "trace_band": "review", "limitations": ["advisory-only"]}

    async def get_trace_report(self, report_id: int | str) -> dict[str, object]:
        return {"report_id": report_id, "limitations": ["not legal verification"]}

    async def get_public_trace_summary(self, report_id: int | str) -> dict[str, object]:
        return {"report_id": report_id, "limitations": ["public summary"]}

    async def get_wallet_health(self, wallet_id: str | None = None) -> dict[str, object]:
        return {"status": "unavailable", "limitations": ["Wallet health endpoint is not available in this deployment."]}

    async def evaluate_policy(self, policy_profile: str, action_type: str, context: dict[str, object]) -> dict[str, object]:
        return {"policy_profile": policy_profile, "approval_required": True, "limitations": ["evaluate only"]}

    async def create_treasury_draft(self, payload: dict[str, object]) -> dict[str, object]:
        return {"draft_id": "local", "approval_required": True, "limitations": ["draft only"]}

    async def get_provider_health(self, provider_type: str | None = None) -> dict[str, object]:
        return {"providers": [], "degraded": False, "limitations": ["sample"]}

    async def get_market_dashboard(self, timeframe: str = "1h") -> dict[str, object]:
        return {"timeframe": timeframe, "limitations": ["not financial advice"]}

    async def get_evidence_packet(self, packet_id: int | str) -> dict[str, object]:
        return {"packet_id": packet_id, "limitations": ["partial"]}


@pytest.mark.asyncio
async def test_all_required_tools_are_registered_and_structured() -> None:
    required = {
        "get_latest_signals",
        "explain_signal",
        "analyze_address",
        "get_trace_report",
        "get_public_trace_summary",
        "get_wallet_health",
        "evaluate_policy",
        "create_treasury_draft",
        "get_provider_health",
        "get_market_dashboard",
        "get_evidence_packet",
    }
    assert required <= set(TOOL_REGISTRY)

    args = {
        "get_latest_signals": {"limit": 1},
        "explain_signal": {"signal_id": 1},
        "analyze_address": {"address": "bc1qexamplepublicaddress000000000000000000000"},
        "get_trace_report": {"report_id": 1},
        "get_public_trace_summary": {"report_id": 1},
        "get_wallet_health": {"wallet_id": "wallet-1"},
        "evaluate_policy": {"policy_profile": "default", "action_type": "trace_review", "context": {}},
        "create_treasury_draft": {"destination": "bc1qexamplepublicaddress000000000000000000000", "amount_sats": 1000},
        "get_provider_health": {},
        "get_market_dashboard": {"timeframe": "1h"},
        "get_evidence_packet": {"packet_id": 1},
    }
    for tool_name in required:
        result = await run_tool(tool_name, args[tool_name], client=FakeClient())  # type: ignore[arg-type]
        assert "limitations" in result
        assert "safety_flags" in result
        assert result["source"] == "bitcoin_bastion_mcp"
