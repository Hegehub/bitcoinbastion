from pathlib import Path

SAFE_TOOLS = {
    "get_latest_signals",
    "analyze_address",
    "get_trace_report",
    "get_wallet_health",
    "evaluate_policy",
    "create_treasury_draft",
    "explain_signal",
    "get_provider_health",
}
FORBIDDEN_TOOL_PARTS = (
    "sign_transaction",
    "broadcast",
    "private_key",
    "seed_phrase",
    "approve_request",
    "override",
)


def test_mcp_tools_are_read_draft_recommendation_only() -> None:
    source = Path("mcp/bastion_mcp/server.py").read_text(encoding="utf-8")
    for tool in SAFE_TOOLS:
        assert tool in source
    assert not [part for part in FORBIDDEN_TOOL_PARTS if part in source]
